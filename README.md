# 10 Apps in 10 Days

Monorepo for ten production-style Python 3.11 + Streamlit MVPs, built one app per day.

## Structure

- `apps/` contains the Streamlit MVPs that belong to this monorepo
- `launchers/` contains macOS double-click launchers for the Streamlit apps
- `projects/` contains separate side projects that should not clutter the app root
- `scripts/` contains shared local tooling

Each app under `apps/` is designed to run independently with `streamlit run app.py`.

## Apps

| Day | App | Folder | Status |
| --- | --- | --- | --- |
| 01 | Idea Rater | `apps/day-01-idea-rater` | Built |
| 02 | Classic Game | `apps/day-02-classic-game` | Built |
| 03 | Serie A LiveScore | `apps/day-03-serie-a-livescore` | Built |
| 04 | Travel Itinerary Builder | `apps/day-04-travel-itinerary-builder` | Built |
| 05 | Contract Risk Scanner | `apps/day-05-contract-risk-scanner` | Planned |
| 06 | YouTube Shorts Planner | `apps/day-06-youtube-shorts-planner` | Planned |
| 07 | Process Mapper | `apps/day-07-process-mapper` | Planned |
| 08 | AI Study Coach | `apps/day-08-ai-study-coach` | Planned |
| 09 | Recipe Fridge Matcher | `apps/day-09-recipe-fridge-matcher` | Planned |
| 10 | Decision Memo Generator | `apps/day-10-decision-memo-generator` | Planned |

## Local setup

Use Python 3.11. For any app:

1. `cd` into the app folder
2. Install dependencies with `pip install -r requirements.txt`
3. Start the app with `streamlit run app.py`

Each app README contains app-specific usage details and sample inputs.

## Local Launchers

For macOS, you can double-click a launcher under `launchers/` to start an app locally:

- [run-day-01-idea-rater.command](/Users/abellotta/Documents/New%20project/launchers/run-day-01-idea-rater.command)
- [run-day-02-classic-game.command](/Users/abellotta/Documents/New%20project/launchers/run-day-02-classic-game.command)
- [run-day-03-serie-a-livescore.command](/Users/abellotta/Documents/New%20project/launchers/run-day-03-serie-a-livescore.command)
- [run-day-04-travel-itinerary-builder.command](/Users/abellotta/Documents/New%20project/launchers/run-day-04-travel-itinerary-builder.command)

Each launcher:

- creates a local virtual environment on first run
- requires Python 3.11 and recreates stale venvs built with another version
- installs dependencies if needed
- starts Streamlit so the app opens in your browser
- writes startup errors to a `day-*.log` file in the repo root

## Live apps

| Day | App | Live URL |
| --- | --- | --- |
| 01 | Idea Rater | [Run App](https://10-apps-in-10-days-b7xqnxqs8nqsmjzhva5cry.streamlit.app/) |

## Side Projects

Non-monorepo work is kept under `projects/` so the main app repo stays easier to scan.
