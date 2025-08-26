# Schritte 
- UV installieren
    - ''uv sync'' um alle Pakete für das Projekt zu laden

- Kaggle API erstellen, runterladen und im Root verzeichnis Packen
    - Link zum Dataset: https://www.kaggle.com/datasets/davidcariboo/player-scores
    - Link zum Erstellen eines API Tokens: https://www.kaggle.com/settings
    - ''create new Token'' auswählen

- get_data in /scripts ausführen, um alle daten zu bekommen

- create_data im /scipts ausführen, um benötige daten für Dataframe zu erstellen

# Bestandteile des Analyseprojektes

ZIEL: Marktwert eines Spielers ermitteln, um am Ende Daten einzugeben und dann den Marktwert vom Spieler bekommen
    Welche Features bestimmen den Marktwert eines Spielers? Gewichtung herausfinden (Regression)

- Exploration eures Datensatzes inklusive aussagekräftiger Visualisierungen.

- Erläuterung bzw. Ableitung aus der Exploration, welcher Wert vorhergesagt wird
Transformation der Daten in geeigneten Pipelines.

- Untersuchung verschiedener Modelle inkl. Hyperparameteroptimierung, Kreuzvalidierung und separaten Tests.

- Darstellung der Vorhersagen in Bezug zu den restlichen Daten. Verdichtet Daten wo sinnvoll zu einer KPI.

- Diskussion des verwendeten Suchverfahrens und was bei der Produktivnahme des Ergebnisses zu beachten ist.

- Die Abgabe soll eine README zu Inhalten und Reproduktion beinhalten. Also wo was ist und wie man es nachmachen kann.

# Über den Datensatz:

Clean, structured and automatically updated football data from Transfermarkt, including

- 60,000+ games from many seasons on all major competitions
- 400+ clubs from those competitions
- 30,000+ players from those clubs
- 400,000+ player market valuations historical records
- 1,200,000+ player appearance records from all games

and more

![ERM](src/data_diagram.svg)

# Auswertung

- Bauen eines Datensets mit Zielvariable `market_value_in_eur` aus `players.csv`, weil dort die meisten Infos eines Spielers vorhanden ist

- `transfers.csv`
    - für jede `players_id` aus `players.csv` die Summe berechnen von `transfer_fee` hinzufügen (Summe von Transfergebühr eines Spielers)
    - für jede `players_id` aus `players.csv` die Summe der Anzahl an Transfers berechnen und hinzufügen (Summe von Transfers eines Spielers)

- `game_lineups.csv`
    - für jede `players_id` aus `players.csv` die Summe einzelner `type` berechenen und hinzufügen
    - für jede `players_id` aus `players.csv` die Summe von `teamcaptain` berechnen und hinzufügen
    - für jede `players_id` aus `players.csv` die Summe von beiden `type` berechnene = Summe der Spiele

- `clubs.csv`
    - wird benötigt um herauszufinden wie viele Spiele ein Spieler pro gespielten Club gemacht hat aus `game_lineups.csv`

- `appearances.csv`
    - für jede `players_id` aus `players.csv` die Summe berechnen von `yellow_cards` und hinzufügen
    - für jede `players_id` aus `players.csv` die Summe berechnen von `red_cards` und hinzufügen
    - für jede `players_id` aus `players.csv` die Summe berechnen von `goals` und hinzufügen
    - für jede `players_id` aus `players.csv` die Summe berechnen von `assists` und hinzufügen
    - für jede `players_id` aus `players.csv` die Summe berechnen von `minutes_played` und hinzufügen

- `competitions.csv`
    - wird benötigt um herauszufinden wie viele Spiele ein Spieler pro gespiele Liga gemacht hat aus `appearances.csv`

- ~~`games.csv` & `game_events.csv` & `club_games.csv`~~
    - enhählt keine wichtige Infos für einen Spieler

- ~~`player_valuations.csv`~~
    - zu wenig Infos für einen Spieler (Dopplung von `players.csv`zum Teil)