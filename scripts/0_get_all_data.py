import os
import json
from pathlib import Path
import sys
import base64
import urllib.request
import urllib.error
import zipfile

# Projektwurzel relativ zu diesem Skript ermitteln
project_root = Path(__file__).resolve().parents[1]
data_dir = project_root / "data"
raw_dir = data_dir / "raw"
kaggle_json_path = project_root / "kaggle.json" #JSON Credentials für Kaggle API

# Nur wenn "data/raw" nicht existiert, alles Weitere ausführen
if not raw_dir.exists():
    # Vorab-Info, was fehlt
    if not data_dir.exists():
        print(f'Datenordner fehlte: "{data_dir}" – wird jetzt erstellt...')
    else:
        print(f'Datenordner vorhanden: "{data_dir}"')
    print(f'Raw-Unterordner fehlte: "{raw_dir}" – wird jetzt erstellt...')

    # Erstellung
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f'Datenordner erstellt: "{data_dir}"')
    raw_dir.mkdir(parents=True, exist_ok=True)
    print(f'Raw-Ordner erstellt: "{raw_dir}"')

    # Kaggle-Credentials laden (aus kaggle.json oder via bereits gesetzten Umgebungsvariablen)
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

    # Streaming-Download mit animierter Progressbar
    username = os.environ.get("KAGGLE_USERNAME")
    key = os.environ.get("KAGGLE_KEY")

    if not username or not key:
        raise RuntimeError("KAGGLE_USERNAME/KAGGLE_KEY nicht verfügbar.")

    download_url = "https://www.kaggle.com/api/v1/datasets/download/davidcariboo/player-scores"
    zip_path = raw_dir / "player-scores.zip"

    # HTTP Basic Auth Header
    token = base64.b64encode(f"{username}:{key}".encode("utf-8")).decode("utf-8")
    req = urllib.request.Request(download_url)
    req.add_header("Authorization", f"Basic {token}")
    req.add_header("User-Agent", "kaggle/1.6.6")
    req.add_header("Accept", "application/zip")

    print("Lade Datensatz 'davidcariboo/player-scores' in 'data/raw' herunter…")
    try:
        with urllib.request.urlopen(req) as resp, open(zip_path, "wb") as f:
            total = resp.getheader("Content-Length")
            total = int(total) if total is not None else None
            downloaded = 0
            chunk_size = 1024 * 256  # 256KB

            def render_bar(done, total_bytes):
                if total_bytes:
                    frac = done / total_bytes
                    bar_len = 30
                    filled = int(bar_len * frac)
                    bar = "=" * filled + ">" + " " * (bar_len - filled - 1)
                    msg = f"\rDownload: [{bar}] {done/1_048_576:.1f}MB/{total_bytes/1_048_576:.1f}MB ({frac*100:5.1f}%)"
                else:
                    msg = f"\rDownload: {done/1_048_576:.1f}MB"
                sys.stdout.write(msg)
                sys.stdout.flush()

            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                render_bar(downloaded, total)

        sys.stdout.write("\n")
        print(f"Download abgeschlossen: {zip_path}")
    except urllib.error.HTTPError as e:
        if e.code == 403:
            raise RuntimeError(
                "Zugriff verweigert (403). Prüfe, ob du die Nutzungsbedingungen des Datasets akzeptiert hast und ob die Credentials korrekt sind."
            ) from e
        raise

    # Entpacken mit einfacher Fortschrittsanzeige
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            members = zf.infolist()
            total_files = len(members)
            print("Entpacke Dateien nach raw/ …")
            for i, m in enumerate(members, start=1):
                zf.extract(m, path=raw_dir)
                bar_len = 30
                frac = i / total_files if total_files else 1
                filled = int(bar_len * frac)
                bar = "=" * filled + ">" + " " * (bar_len - filled - 1)
                sys.stdout.write(f"\rUnzip:   [{bar}] {i}/{total_files}")
                sys.stdout.flush()
        sys.stdout.write("\n")
        os.remove(zip_path)
        print(f"Entpacken abgeschlossen. Daten liegen in: {raw_dir}")
    except zipfile.BadZipFile:
        # Falls Kaggle bereits entpackte Dateien lieferte, einfach weitermachen
        print("Hinweis: Keine gültige ZIP-Datei — Entpacken übersprungen.")
else:
    print(f'Raw-Ordner existiert bereits, überspringe Download: "{raw_dir}"')