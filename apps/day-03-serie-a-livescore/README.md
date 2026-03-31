# Day 03 - Serie A LiveScore

Webapp Streamlit ispirata a Livescore, focalizzata solo sulla Serie A.

## Funzioni

- scoreboard con partite live, finite e upcoming
- filtri per stato partita e squadra
- dettaglio match con timeline eventi e statistiche
- classifica della Serie A
- classifica live via API
- stato feed e fallback locale se l'API non risponde

## Run locally

```bash
cd apps/day-03-serie-a-livescore
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Dati reali

L'app prova a leggere dati reali da TheSportsDB usando:

- chiave free pubblica `123` di default
- oppure `THESPORTSDB_API_KEY` se vuoi usare una tua chiave

Esempio:

```bash
export THESPORTSDB_API_KEY=la_tua_chiave
streamlit run app.py
```
