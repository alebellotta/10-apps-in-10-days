# Day 01 - Idea Rater

Idea Rater is a rules-based Streamlit app for evaluating startup, product, and app ideas with a structured scoring model. It helps a founder or operator quickly pressure-test an idea before spending time building.

## Features

- Weighted score out of 100 across five dimensions
- Dimension-level rationale and score breakdown
- Rules-based SWOT analysis
- Three recommended next experiments
- Example preset for instant demo
- Markdown export for sharing or saving a review

## Run locally

```bash
cd apps/day-01-idea-rater
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Inputs

- Idea description
- Target user
- Pain point
- Monetization hypothesis
- Adjustable scoring weights

## Example usage

Use the built-in example preset for an AI meeting prep assistant. Then adjust the weight sliders to reflect your strategy, such as prioritizing speed to MVP over differentiation.

## Export

The app generates a downloadable Markdown report with:

- total score
- breakdown by dimension
- SWOT analysis
- next experiments

## Notes

The scoring engine is deterministic by design. The code is structured around helper functions so an LLM-based evaluator can be added later without replacing the current workflow.
