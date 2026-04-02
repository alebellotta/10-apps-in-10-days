# Day 04 - Travel Itinerary Builder

Streamlit MVP that builds a city-break itinerary from destination, dates, pace, budget style, and interests.

## Features

- day-by-day plan with morning, afternoon, and evening blocks
- optional OpenAI-powered concierge mode that turns the plan into client-ready copy
- built-in destination packs for Rome, Paris, Barcelona, and Amsterdam
- budget snapshot covering trip estimate, daily average, and activity spend
- packing suggestions adapted to destination and season
- AI concierge brief with booking checklist, personalization notes, and upsell angle
- copyable and downloadable Markdown export for sharing the itinerary

## Run locally

```bash
cd apps/day-04-travel-itinerary-builder
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Or launch it from [run-day-04-travel-itinerary-builder.command](/Users/abellotta/Documents/New%20project/launchers/run-day-04-travel-itinerary-builder.command).

## Notes

- This MVP is offline-friendly and uses curated in-app destination/activity data.
- To enable GenAI mode, set `OPENAI_API_KEY` and optionally `OPENAI_MODEL` before running the app.
- Trip length is intentionally capped at 7 days to keep the itinerary readable.
- The generated Markdown export is designed for easy copy/paste into docs, email, or chat.
