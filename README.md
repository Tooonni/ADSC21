# Marktwertprognose für Fußballspieler

Dieses Projekt untersucht ein Ende-zu-Ende-Setup, um den Marktwert professioneller Fußballspieler auf Basis öffentlich verfügbarer Transfermarkt-Daten vorherzusagen. Das Projekt deckt Datenbeschaffung (Kaggle), Aufbereitung, explorative Analyse, Feature Engineering, Modellierung, Interpretierbarkeit und KPI-Ableitung ab.

## Überblick
- **Business-Ziel:** Marktwert eines Spielers ermitteln, um am Ende Daten einzugeben und dann den Marktwert vom Spieler bekommen
- **Kernfragen:** Welche Features bestimmen den Marktwert eines Spielers? Wie gut lassen sich Marktwerte mittels ML vorhersagen? Wie lassen sich Ergebnisse transparent kommunizieren?
- **Hauptartefakte:** automatisierte Datenerstellung (`scripts/`), Analyse-Notebooks (`notebooks/`), Feature-Diagramm (`src/data_diagram.svg`) und dokumentierte Modellleistung

## Repository-Struktur
- `README.md` – dieser Leitfaden.
- `pyproject.toml`, `uv.lock` – Python-Umgebung (verwaltet mit [uv](https://github.com/astral-sh/uv)).
- `scripts/` – Automatisierungsschritte:
  - `0_get_all_data.py`: Download & Entpacken des Kaggle-Datasets inkl. Credential-Handling.
  - `1_create_data.py`: Aggregiert Rohdaten zu einer Spieler-Mastertabelle (`data/players.csv`).
- `notebooks/` – Analyse-Workflow von Datenverständnis bis Modellierung (siehe Abschnitt *Analyse-Workflow*).
- `data/` – persistierte Datensätze (`raw/` Rohdaten, `players.csv`, `players_cleaned.csv`, `players_eda.csv`, `players_fe.csv`, sowie Referenzdateien `clubs.csv`, `competitions.csv`).
- `src/data_diagram.svg` – ERM-Visualisierung der wichtigsten Tabellen.
- `output/` – Platzhalter für Export-Artefakte (Plots, Tabellen, Modell-Dumps).

## Setup & Datenbeschaffung
Folge den vorhandenen Schritten, um die Arbeitsumgebung zu initialisieren:

- UV installieren
    - `uv sync` um alle Pakete für das Projekt zu laden

- Kaggle API erstellen, runterladen und im Root verzeichnis Packen
    - Link zum Dataset: https://www.kaggle.com/datasets/davidcariboo/player-scores
    - Link zum Erstellen eines API Tokens: https://www.kaggle.com/settings
    - `create new Token` auswählen und in der ersten Ebene im Projektordner hinterlegen

- `scripts/0_get_all_data.py` ausführen, um alle daten zu bekommen  
  (z.B. `uv run python scripts/0_get_all_data.py`)

- `scripts/1_create_data.py` ausführen, um benötige Daten für Dataframe zu erstellen  
  (z.B. `uv run python scripts/1_create_data.py`)

### Ergänzende Hinweise
- Die Skripte prüfen eigenständig, ob `data/raw/` bereits existiert und überspringen den Download dann.
- Für den Kaggle-Zugriff können statt `kaggle.json` auch die Umgebungsvariablen `KAGGLE_USERNAME` und `KAGGLE_KEY` verwendet werden.
- Nach `1_create_data.py` liegen alle aggregierten Features in `data/players.csv`; `data/players_fe.csv` enthält zusätzliche Feature-Engineering-Schritte aus Notebook `04_Feature_Engineering.ipynb`.

## Bestandteile des Analyseprojektes

Marktwert eines Spielers ermitteln, um am Ende Daten einzugeben und dann den Marktwert vom Spieler bekommen

- Welche Features bestimmen den Marktwert eines Spielers? Gewichtung herausfinden (Regression)
- Exploration des Datensatzes inklusive aussagekräftiger Visualisierungen
- Erläuterung bzw. Ableitung aus der Exploration, welcher Wert vorhergesagt wird  
  Transformation der Daten in geeigneten Pipelines
- Untersuchung verschiedener Modelle inkl. Hyperparameteroptimierung, Kreuzvalidierung und separaten Tests
- Darstellung der Vorhersagen in Bezug zu den restlichen Daten. Verdichtet Daten wo sinnvoll zu einer KPI.
- Diskussion des verwendeten Suchverfahrens und was bei der Produktivnahme des Ergebnisses zu beachten ist.

## Datenquelle

Clean, structured and automatically updated football data from Transfermarkt, including

- 60,000+ games from many seasons on all major competitions
- 400+ clubs from those competitions
- 30,000+ players from those clubs
- 400,000+ player market valuations historical records
- 1,200,000+ player appearance records from all games

and more

![ERM](src/data_diagram.svg)

## Datenaufbereitung (1_create_data.py)

- Bauen eines Datensets mit Zielvariable `market_value_in_eur` aus `players.csv`, weil dort die meisten Infos eines Spielers vorhanden ist.
- `transfers.csv`
    - für jede `player_id` aus `players.csv` die Summe berechnen von `transfer_fee` hinzufügen (Summe von Transfergebühr eines Spielers)
    - für jede `player_id` aus `players.csv` die Summe der Anzahl an Transfers berechnen und hinzufügen (Summe von Transfers eines Spielers)
- `game_lineups.csv`
    - für jede `player_id` aus `players.csv` die Summe einzelner `type` berechnen und hinzufügen
    - für jede `player_id` aus `players.csv` die Summe von `team_captain` berechnen und hinzufügen
    - für jede `player_id` aus `players.csv` die Summe von beiden `type` berechnen = Summe der Spiele
- `clubs.csv`
    - wird benötigt um herauszufinden wie viele Spiele ein Spieler pro gespielten Club gemacht hat aus `game_lineups.csv`
- `appearances.csv`
    - für jede `player_id` aus `players.csv` die Summe berechnen von `yellow_cards` und hinzufügen
    - für jede `player_id` aus `players.csv` die Summe berechnen von `red_cards` und hinzufügen
    - für jede `player_id` aus `players.csv` die Summe berechnen von `goals` und hinzufügen
    - für jede `player_id` aus `players.csv` die Summe berechnen von `assists` und hinzufügen
    - für jede `player_id` aus `players.csv` die Summe berechnen von `minutes_played` und hinzufügen
- `competitions.csv`
    - wird benötigt um herauszufinden wie viele Spiele ein Spieler pro gespielte Liga gemacht hat aus `appearances.csv`
- ~~`games.csv` & `game_events.csv` & `club_games.csv`~~
    - enthält keine wichtige Infos für einen Spieler
- ~~`player_valuations.csv`~~
    - zu wenig Infos für einen Spieler (Dopplung von `players.csv` zum Teil)

Zusätzlich kümmert sich `1_create_data.py` um Aufräumen des `raw/`-Ordners und verschiebt Referenzdateien (`clubs.csv`, `competitions.csv`) nach `data/`, um spätere Analysen zu erleichtern.

## Analyse-Workflow (Notebooks)

| Notebook | Fokus | Kernergebnisse |
| --- | --- | --- |
| `00_help_create_data.ipynb` | Prototyp der Feature-Aggregation | Validierung, dass Summenbildung über Transfers, Lineups & Appearances funktioniert |
| `01_Datenverständnis.ipynb` | Problemdefinition & Datenüberblick | Zieldefinition, Auswahl des Kaggle-Datasets, erste Profilierung wichtiger Tabellen |
| `02_Datenbereinigung.ipynb` | Datenqualitätsmaßnahmen | Behandlung fehlender Werte, Harmonisierung von Ländern/Städten, Transformation kritischer Spalten |
| `03_EDA.ipynb` | Explorative Analysen | Marktwertgetriebene Visualisierungen (Alter, Position, Performance, Transfers, Zeitverlauf) |
| `04_Feature_Engineering.ipynb` | Feature-Building & Selection | Ableitung von Raten-/Intensitätskennzahlen (z.B. Tore/90, Transferintensität), Bereinigung redundanter Spalten |
| `05_Modelling.ipynb` | Modellierung & Evaluation | Pipelines, Grid Search (Ridge, RandomForest, HistGB), KPI-Reporting, Interpretierbarkeit, Produktionshinweise |

Alle Notebooks sind so strukturiert, dass sie sequenziell ausführbar sind. Die späteren Notebooks (`03`–`05`) erwarten die von `1_create_data.py` generierten Daten.

## Modellierung & Ergebnisse

Im Notebook `05_Modelling.ipynb` wurden drei Pipelines verglichen. Zielgröße ist `log_market_value`, womit die Bewertung metrischer Fehler in log-Skala erfolgt.

| Modell | Test-MAE (log) | Test-RMSE (log) | Test-R² |
| --- | --- | --- | --- |
| Ridge (simple) | 0.7641 | 0.9794 | 0.6073 |
| RandomForest (medium) | 0.6028 | 0.7875 | 0.7461 |
| HistGB (strong) | **0.5775** | **0.7547** | **0.7668** |

- Alle Pipelines bestehen aus einem `ColumnTransformer` mit Median-Imputation + Standardisierung (numerisch) sowie Most-Frequent-Imputation + One-Hot-Encoding (kategorisch).
- Hyperparameter wurden per `GridSearchCV` (5-fold, `neg_mean_absolute_error`) optimiert. Für den HistGradientBoosting-Regressor erwies sich die Kombination `learning_rate=0.03`, `max_leaf_nodes=127`, `max_iter=300` als bestes Setup.

## KPIs & Fehleranalyse

Aus den Prognosen wird ein indikatorisches Fehler-Dashboard abgeleitet (Einheit `€` auf Originalskala, Testsplit):

| Split | MAE (log) | RMSE (log) | Median absoluter Fehler [Mio. €] | MAPE |
| --- | --- | --- | --- | --- |
| Train | 0.4442 | 0.5892 | 0.076 | 51.9 % |
| Test | 0.5775 | 0.7547 | **0.101** | **74.2 %** |

- Zusätzlich visualisieren die Notebooks:
  - **Ist vs. Prognose (Scatter)** inkl. 45°-Referenzlinie, gefärbt nach Position.
  - **Fehlerverteilung nach Segment** (z.B. Boxplots nach Position, Country).
  - **Partial Dependence Plots** für die wichtigsten numerischen Merkmale (Alter, Einsatzzeit).

## Interpretierbarkeit (XAI)

- Permutation Importance (Testdaten) hebt folgende Top-Treiber hervor:
  1. `age`
  2. `total_minutes_played`
  3. `transfer_intensity_per_10k_min`
  4. `total_transfer_fee`
  5. `contract_years_left`
- PDPs zeigen u.a. einen abnehmenden marginalen Effekt höheren Alters sowie steigende Werte bei höherer Einsatzzeit.
- Die Pipeline kapselt One-Hot-Spaltennamen (`prep.get_feature_names_out()`), sodass Visualisierungen/Reports konsistent mit dem Modellstand bleiben.

## Diskussion & Produktivsetzung

- **Suchverfahren:** Exhaustiver Grid Search liefert robuste, aber teurere Optimierung. Für breitere Parameter-Räume würden `RandomizedSearchCV` oder successive Halving (`HalvingGridSearchCV`) die Rechenlast reduzieren.
- **Produktivanforderungen:** 
  - Pipeline serialisieren (`joblib.dump`) inklusive Preprocessing-Schritte.
  - Vorhersagen wieder auf Euro-Skala exponentieren und KPIs in Währung reporten (Median absoluter Fehler ≈ 0,10 Mio. € auf Testdaten).
  - Data-Drift beobachten (neue Kategorien → `OneHotEncoder(handle_unknown="ignore")` fängt dies ab, Logging empfehlenswert).
  - Re-Trainingsprozesse automatisieren (z.B. monatlich) und Ergebnisse gegen Validation- oder Hold-out-Sets monitoren.

## Reproduzierbarkeit & Nutzung

1. **Environment**  
   ```bash
   uv sync
   ```
2. **Daten laden & vorbereiten**  
   ```bash
   uv run python scripts/0_get_all_data.py
   uv run python scripts/1_create_data.py
   ```
3. **Analyse starten**  
   ```bash
   uv run jupyter lab
   ```  
   oder `uv run jupyter notebook` und Notebooks in aufsteigender Reihenfolge ausführen.
4. **Modelle evaluieren**  
   Notebook `05_Modelling.ipynb` durchlaufen lassen, danach Visualisierungen exportieren (`output/`).

## Weiterführende Todos
- Modell als API oder Batch-Job deployen (z.B. FastAPI + Docker).
- Weitere Features testen (Verletzungen, Vertragsverlängerungen) oder externe Marktdaten integrieren.
- Fehlerraten für Nachwuchsspieler (geringe Einsatzzeit) separat überwachen.
- KPI-Dashboard (z.B. Streamlit) für Stakeholder visualisieren.

## Quellen & Referenzen
- Kaggle Dataset: https://www.kaggle.com/datasets/davidcariboo/player-scores
- Kaggle API Token: https://www.kaggle.com/settings
- scikit-learn Documentation: https://scikit-learn.org/stable/
- uv Package Manager: https://github.com/astral-sh/uv
