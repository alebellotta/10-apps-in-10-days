# 10 Apps in 10 Days

Monorepo for ten production-style Python 3.11 + Streamlit MVPs, built one app per day.

## Structure

Each app lives in its own folder under `apps/` and is designed to run independently with:

```bash
streamlit run app.py
```

## Apps

| Day | App | Folder | Status |
| --- | --- | --- | --- |
| 01 | Idea Rater | `apps/day-01-idea-rater` | Built |
| 02 | Meeting Minute Maker | `apps/day-02-meeting-minute-maker` | Planned |
| 03 | Personal Finance Simulator | `apps/day-03-personal-finance-simulator` | Planned |
| 04 | Travel Itinerary Builder | `apps/day-04-travel-itinerary-builder` | Planned |
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

## Local launcher

For macOS, you can double-click [run-day-01-idea-rater.command](/Users/abellotta/Documents/New%20project/run-day-01-idea-rater.command) to start Day 01 locally. The launcher:

- creates a local virtual environment on first run
- installs dependencies if needed
- starts Streamlit so the app opens in your browser
