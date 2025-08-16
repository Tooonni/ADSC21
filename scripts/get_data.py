import os
import json
from pathlib import Path

# Projektwurzel relativ zu diesem Skript ermitteln
project_root = Path(__file__).resolve().parents[1]
data_dir = project_root / "data"
kaggle_json_path = project_root / "kaggle.json" #JSON Credentials für Kaggle API

# 1) Nur wenn data/ nicht existiert, alles Weitere ausführen
if not data_dir.exists():
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f'Datenordner erstellt: "{data_dir}" - weil keiner vorhanden war')

    # 2) Kaggle-Credentials laden (aus kaggle.json oder via bereits gesetzten Umgebungsvariablen)
    if kaggle_json_path.exists():
        with open(kaggle_json_path, "r") as f:
            kaggle_creds = json.load(f)
        # Nur setzen, wenn noch nicht gesetzt (erlaubt Überschreiben via Environment)
        os.environ.setdefault("KAGGLE_USERNAME", kaggle_creds.get("username", ""))
        os.environ.setdefault("KAGGLE_KEY", kaggle_creds.get("key", ""))
    else:
        # Falls keine Datei vorhanden ist, müssen Env-Vars gesetzt sein oder ~/.kaggle/kaggle.json existieren
        if not (os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY")):
            raise FileNotFoundError(
                f"kaggle.json nicht gefunden unter {kaggle_json_path} und keine Umgebungsvariablen KAGGLE_USERNAME/KAGGLE_KEY gesetzt. "
                "Lege kaggle.json im Projektroot ab, setze die Variablen, oder platziere die Datei in ~/.kaggle/."
            )

    # 3) Erst nach gesetzten Credentials importieren
    import kaggle  # type: ignore

    # 4) Authentifizieren und Download
    kaggle.api.authenticate()
    print("Lade Datensatz 'davidcariboo/player-scores' nach data/ herunter…")
    # Nutze die offizielle Kaggle API zum vollständigen Download inkl. Entpacken
    kaggle.api.dataset_download_files(
        "davidcariboo/player-scores", path=str(data_dir), unzip=True
    )
    print(f"Download abgeschlossen. Dateien liegen in: {data_dir}")

    # Optional: Übrig gebliebene ZIP-Dateien im data-Ordner entfernen
    for fname in os.listdir(data_dir):
        if fname.endswith(".zip"):
            try:
                os.remove(data_dir / fname)
            except Exception:
                pass
else:
    print(f'Datenordner existiert bereits, überspringe Download: "{data_dir}"')