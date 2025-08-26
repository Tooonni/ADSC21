from __future__ import annotations
from pathlib import Path
import shutil
import pandas as pd

# Dieses Skript übernimmt die "Feature Engineering" Schritte für die Spieler-Daten.
# Annahme: Die Rohdaten wurden zuvor mittels get_all_data.py in data/raw/ geladen und entpackt.
# Ablauf grob:
# 1. Pflicht-Rohdateien einlesen (players, transfers, game_lineups, appearances)
# 2. Feature-Spalten aus Transfers (Anzahl / Summe Gebühren) iterativ berechnen – wie im Notebook gewünscht
# 3. Feature-Spalten aus Aufstellungen (Startelf/Sub/Captain/Gesamtspiele) ableiten
# 4. Feature-Spalten aus Appearances (Summen von Karten, Toren, Assists, Minuten) aggregieren
# 5. Ergebnis als players.csv (angereichert) im data/ Verzeichnis speichern
# 6. Aufräumen: Unnötige Dateien löschen, clubs/competitions verschieben

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

OUT_PLAYERS = DATA_DIR / "players.csv"  # Zieldatei der verarbeiteten / angereicherten Spielerdaten


def require(file: Path) -> Path:
	"""Stellt sicher, dass die angegebene Datei existiert.

	Hebt einen FileNotFoundError aus, falls die Datei fehlt – damit frühzeitiges Abbrechen
	möglich ist, statt später in Folgefunktionen unklare Fehler zu bekommen.
	"""
	if not file.exists():
		raise FileNotFoundError(f"Benötigte Datei fehlt: {file}")
	return file


def load_raw() -> dict[str, pd.DataFrame]:
	"""Liest alle für die Feature-Berechnung benötigten Roh-CSV-Dateien ein.

	Pflicht: players.csv, transfers.csv, game_lineups.csv, appearances.csv
	Optional (werden nur eingelesen, wenn vorhanden): clubs.csv, competitions.csv (nur für späteres Verschieben)
	Rückgabe: Dictionary {name: DataFrame}
	"""
	files = {
		"players": require(RAW_DIR / "players.csv"),
		"transfers": require(RAW_DIR / "transfers.csv"),
		"game_lineups": require(RAW_DIR / "game_lineups.csv"),
		"appearances": require(RAW_DIR / "appearances.csv"),
	}
	# Optionale Dateien (für Verschieben/Referenz, nicht für unmittelbare Feature-Bildung zwingend)
	optional = ["clubs.csv", "competitions.csv"]
	dfs: dict[str, pd.DataFrame] = {}
	for key, path in files.items():
		dfs[key] = pd.read_csv(path)
	for name in optional:
		p = RAW_DIR / name
		if p.exists():
			dfs[name.replace('.csv','')] = pd.read_csv(p)
	return dfs


def add_transfer_features(players: pd.DataFrame, transfers: pd.DataFrame) -> pd.DataFrame:
	"""Berechnet Transfer-Features je Spieler (Anzahl Transfers, Summe der Gebühren).

	Umsetzung orientiert sich explizit an der Notebook-Variante (iterative Schleifen) –
	absichtlich nicht durch reine GroupBy-Aggregation ersetzt, um 1:1 Nachvollziehbarkeit zu gewährleisten.
	"""
	# Defensive Kopien (Originale nicht verändern)
	players = players.copy()
	transfers = transfers.copy()

	# Zielspalten initialisieren (überschreiben falls bereits vorhanden)
	players["number_of_transfers"] = 0
	players["total_transfer_fee"] = 0

	# Falls Spalte fehlt → künstlich anlegen; ansonsten fehlende Werte auf 0 setzen
	if "transfer_fee" not in transfers.columns:
		transfers["transfer_fee"] = 0.0
	else:
		transfers["transfer_fee"] = transfers["transfer_fee"].fillna(0.0)

	# Iterative Berechnung (bewusst nicht optimiert, zur Deckungsgleichheit mit Notebook) 
	for pid in players["player_id"].to_list():
		number_of_transfers = 0
		total_transfer_fee = 0
		# Alle Zeilen für Spieler pid filtern und durchlaufen
		for tr in transfers[transfers["player_id"] == pid].itertuples():
			number_of_transfers += 1
			# Numerische Robustheit: Fallback 0 bei Parsing-Problemen
			try:
				val = float(tr.transfer_fee)
			except Exception:
				val = 0.0
			total_transfer_fee += val
		# Rückschreiben der berechneten Werte in die DataFrame-Zeilen des Spielers
		players.loc[players["player_id"] == pid, "number_of_transfers"] = number_of_transfers
		players.loc[players["player_id"] == pid, "total_transfer_fee"] = total_transfer_fee
	return players


def add_lineup_features(players: pd.DataFrame, lineups: pd.DataFrame) -> pd.DataFrame:
	"""Leitet Aufstellungs-bezogene Kennzahlen ab (Startelf, Einwechslungen, Captain, Gesamtspiele)."""
	# Pivot: Anzahl Spiele je Typ (starting_lineup / substitutes) → Umbenennung in sprechende Spalten
	type_pivot = (
		lineups.pivot_table(
			index="player_id",
			columns="type",
			values="game_id",
			aggfunc="count",
			fill_value=0,
		)
		.rename(columns={"starting_lineup": "total_starting_lineups", "substitutes": "total_substitute_appearances"})
		.reset_index()
	)

	# Captain-Einsätze (team_captain == 1) summieren – falls Spalte vorhanden
	if "team_captain" in lineups.columns:
		captain_counts = (
			lineups.assign(is_captain=(lineups["team_captain"] == 1))
			.groupby("player_id")["is_captain"]
			.sum()
			.rename("total_captain_appearances")
			.reset_index()
		)
	else:
		captain_counts = pd.DataFrame({"player_id": [], "total_captain_appearances": []})

	# Gesamtanzahl Zeilen (Spiele) je Spieler
	total_games = lineups.groupby("player_id").agg(total_games=("game_id", "count")).reset_index()

	# Zusammenführen aller Teil-Aggregationen
	merged = players.merge(type_pivot, on="player_id", how="left")
	merged = merged.merge(captain_counts, on="player_id", how="left")
	merged = merged.merge(total_games, on="player_id", how="left")

	# Fehlende Werte der neuen numerischen Spalten auf 0 setzen und konsistent als int ablegen
	for col in [
		"total_starting_lineups",
		"total_substitute_appearances",
		"total_captain_appearances",
		"total_games",
	]:
		if col in merged.columns:
			merged[col] = merged[col].fillna(0).astype(int)
	return merged


def add_appearance_features(players: pd.DataFrame, appearances: pd.DataFrame) -> pd.DataFrame:
	"""Aggregiert Summenstatistiken aus appearances (Karten, Tore, Assists, Minuten)."""
	# Mapping Rohspalten → Zielspaltennamen
	cols = {
		"yellow_cards": "total_yellow_cards",
		"red_cards": "total_red_cards",
		"goals": "total_goals",
		"assists": "total_assists",
		"minutes_played": "total_minutes_played",
	}
	# Nur existierende Spalten verwenden (Dataset kann variieren)
	existing = [c for c in cols.keys() if c in appearances.columns]
	grp = appearances.groupby("player_id")[existing].sum().rename(columns=cols).reset_index()
	merged = players.merge(grp, on="player_id", how="left")
	# NaNs (Spieler ohne appearances) auf 0 setzen
	for c in cols.values():
		if c in merged.columns:
			merged[c] = merged[c].fillna(0)
	return merged


def save_players(df: pd.DataFrame) -> Path:
	"""Speichert die angereicherte players-DataFrame als CSV unter data/players.csv."""
	DATA_DIR.mkdir(parents=True, exist_ok=True)
	df.to_csv(OUT_PLAYERS, index=False)
	return OUT_PLAYERS


def cleanup_and_move():
	"""Bereinigt das raw-Verzeichnis und verschiebt Referenzdateien.

	Gelöscht werden diverse große/irrelevante CSVs (Liste siehe Code). Anschließend werden
	clubs.csv und competitions.csv aus raw/ in data/ verschoben (Überschreiben, falls vorhanden).
	"""
	# Kandidaten zum Löschen (reduziert Platz / verhindert versehentliche Nutzung später)
	to_delete = [
		"games.csv",
		"game_events.csv",
		"club_games.csv",
		"club_games.cav",  # falls Tippfehler existiert
		"player_valuations.csv",
	]
	for name in to_delete:
		p = RAW_DIR / name
		if p.exists():
			try:
				p.unlink()
				print(f"Gelöscht: {p}")
			except Exception as e:
				print(f"Konnte {p} nicht löschen: {e}")

	# Verschieben ausgewählter Referenzdateien heraus aus raw/
	for name in ["clubs.csv", "competitions.csv"]:
		src = RAW_DIR / name
		if src.exists():
			dest = DATA_DIR / name
			try:
				if dest.exists():  # vorhandene Ziel-Datei überschreiben
					dest.unlink()
				shutil.move(str(src), str(dest))
				print(f"Verschoben: {src} -> {dest}")
			except Exception as e:
				print(f"Fehler beim Verschieben {src}: {e}")


def main():
	"""Orchestriert den End-to-End Prozess der Spieler-Feature-Erstellung."""
	if not RAW_DIR.exists():
		raise SystemExit(f"Raw-Verzeichnis nicht gefunden: {RAW_DIR}. Bitte erst get_all_data.py ausführen.")

	# 1. Rohdaten laden
	dfs = load_raw()
	players = dfs["players"].copy()

	# 2. Feature-Erweiterungen anwenden
	players = add_transfer_features(players, dfs["transfers"])       # Transfers
	players = add_lineup_features(players, dfs["game_lineups"])      # Aufstellungen
	players = add_appearance_features(players, dfs["appearances"])   # Appearance-Statistiken

	# 3. Speichern Ergebnisdatei
	out_path = save_players(players)
	print(f"Verarbeitete Players-Datei gespeichert: {out_path}")

	# 4. Aufräumen & Verschieben
	cleanup_and_move()
	print("Fertig.")


if __name__ == "__main__":
	main()