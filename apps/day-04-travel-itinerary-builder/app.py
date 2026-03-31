from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, timedelta
from textwrap import dedent
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st
from pydantic import BaseModel, Field


@dataclass(frozen=True)
class Activity:
    title: str
    category: str
    vibe: str
    duration_hours: float
    price_eur: int
    indoor: bool
    morning_fit: bool
    evening_fit: bool
    description: str


class AITripDay(BaseModel):
    day_number: int = Field(ge=1, le=7)
    title: str = Field(min_length=6, max_length=80)
    morning_plan: str = Field(min_length=18, max_length=220)
    afternoon_plan: str = Field(min_length=18, max_length=220)
    evening_plan: str = Field(min_length=18, max_length=220)
    logistics_tip: str = Field(min_length=18, max_length=180)


class AITripBrief(BaseModel):
    trip_hook: str = Field(min_length=16, max_length=120)
    client_summary: str = Field(min_length=30, max_length=220)
    booking_checklist: list[str] = Field(min_length=3, max_length=4)
    concierge_upgrade: str = Field(min_length=18, max_length=160)


class AITripResponse(BaseModel):
    overview: str = Field(min_length=30, max_length=240)
    days: list[AITripDay] = Field(min_length=1, max_length=7)
    brief: AITripBrief


DESTINATIONS: dict[str, dict[str, object]] = {
    "Rome": {
        "country": "Italy",
        "airport": "FCO",
        "best_for": ["history", "food", "culture", "architecture"],
        "daily_budget": {"Budget": 110, "Comfort": 185, "Premium": 310},
        "packing": ["Comfortable walking shoes", "Light scarf for churches", "Power bank"],
        "activities": [
            Activity("Colosseum and Roman Forum loop", "history", "iconic", 3.0, 24, False, True, False, "Start early to beat queues and heat."),
            Activity("Trastevere food walk", "food", "social", 2.5, 38, False, False, True, "Best on the first night for an easy landing."),
            Activity("Vatican Museums focus visit", "culture", "immersive", 3.0, 30, True, True, False, "Book an early slot and move straight to the highlights."),
            Activity("Villa Borghese slow afternoon", "relaxation", "calm", 2.0, 12, False, False, False, "A lower-energy reset between bigger sightseeing blocks."),
            Activity("Campo de' Fiori and Pantheon stroll", "architecture", "wandering", 2.0, 0, False, True, True, "Great flexible block for day one orientation."),
            Activity("Tiber sunset walk", "relaxation", "romantic", 1.5, 0, False, False, True, "Easy add-on before dinner."),
        ],
    },
    "Paris": {
        "country": "France",
        "airport": "CDG",
        "best_for": ["culture", "romance", "food", "art"],
        "daily_budget": {"Budget": 135, "Comfort": 220, "Premium": 360},
        "packing": ["Compact umbrella", "Smart-casual dinner outfit", "Museum-ready tote"],
        "activities": [
            Activity("Louvre priority highlights", "art", "iconic", 3.0, 22, True, True, False, "Keep it selective so the museum stays energizing."),
            Activity("Montmartre cafe and stair circuit", "culture", "cinematic", 2.5, 18, False, True, True, "Ideal for photographers and slow wanderers."),
            Activity("Seine picnic and riverbank walk", "relaxation", "romantic", 2.0, 16, False, False, True, "Weather-dependent but easy to swap."),
            Activity("Le Marais tasting crawl", "food", "social", 2.5, 35, False, False, True, "Small plates, pastry stop, and late-afternoon browsing."),
            Activity("Musee d'Orsay visit", "art", "refined", 2.0, 16, True, True, False, "Works well when rain hits."),
            Activity("Eiffel and Trocadero blue-hour stop", "architecture", "romantic", 1.5, 0, False, False, True, "Short and memorable close to the day."),
        ],
    },
    "Barcelona": {
        "country": "Spain",
        "airport": "BCN",
        "best_for": ["architecture", "nightlife", "food", "beach"],
        "daily_budget": {"Budget": 105, "Comfort": 175, "Premium": 285},
        "packing": ["Sunscreen", "Light layers", "Swimwear in warm months"],
        "activities": [
            Activity("Sagrada Familia and Eixample walk", "architecture", "iconic", 2.5, 26, False, True, False, "Pair the basilica with a relaxed neighborhood lap."),
            Activity("Gothic Quarter tapas trail", "food", "social", 2.5, 32, False, False, True, "Best done without a rigid pace."),
            Activity("Barceloneta beach reset", "beach", "easygoing", 2.0, 12, False, False, True, "Useful low-effort buffer if the trip feels packed."),
            Activity("Park Guell morning slot", "architecture", "playful", 2.0, 18, False, True, False, "Morning light and smaller crowds help here."),
            Activity("El Born design and coffee circuit", "culture", "creative", 2.0, 14, False, True, True, "Flexible block with shops, coffee, and galleries."),
            Activity("Bunker viewpoint sunset", "relaxation", "scenic", 1.5, 0, False, False, True, "Great payoff for a lower-cost evening."),
        ],
    },
    "Amsterdam": {
        "country": "Netherlands",
        "airport": "AMS",
        "best_for": ["culture", "canals", "nightlife", "cycling"],
        "daily_budget": {"Budget": 120, "Comfort": 195, "Premium": 320},
        "packing": ["Waterproof jacket", "Crossbody bag", "Bike-friendly shoes"],
        "activities": [
            Activity("Canal cruise opener", "culture", "easygoing", 1.5, 22, False, False, True, "Low-friction first activity after arrival."),
            Activity("Jordaan cafe and gallery wander", "culture", "creative", 2.0, 18, False, True, True, "Balanced option for slower travelers."),
            Activity("Rijksmuseum essentials", "art", "immersive", 2.5, 22, True, True, False, "Focus on one wing plus a short museum stop."),
            Activity("Foodhallen casual tasting", "food", "social", 2.0, 28, True, False, True, "Ideal when weather turns wet."),
            Activity("Vondelpark decompress block", "relaxation", "calm", 1.5, 0, False, True, False, "Good counterweight to museum-heavy days."),
            Activity("De Pijp late dinner circuit", "nightlife", "lively", 2.5, 34, False, False, True, "A stronger evening for groups or couples."),
        ],
    },
}

PACE_TARGETS = {"Slow": 2, "Balanced": 3, "Fast": 4}
SEASON_PACKING = {
    "Spring": ["Light jacket", "Layering basics"],
    "Summer": ["Refillable water bottle", "Sunglasses"],
    "Autumn": ["Packable rain layer", "Closed-toe shoes"],
    "Winter": ["Warm coat", "Thermal layer"],
}

DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "300"))
OLLAMA_MODE_PROFILES = {
    "Cheap": {
        "model": os.getenv("OLLAMA_CHEAP_MODEL", DEFAULT_OLLAMA_MODEL),
        "temperature": 0.1,
        "max_tokens": 700,
        "label": "Lowest local cost, fastest local draft",
    },
    "Balanced": {
        "model": os.getenv("OLLAMA_BALANCED_MODEL", DEFAULT_OLLAMA_MODEL),
        "temperature": 0.2,
        "max_tokens": 1000,
        "label": "Best default for most local runs",
    },
    "Premium": {
        "model": os.getenv("OLLAMA_PREMIUM_MODEL", "qwen3:8b"),
        "temperature": 0.25,
        "max_tokens": 1400,
        "label": "Richer local copy, heavier model",
    },
}

GENERIC_ACTIVITY_LIBRARY = {
    "history": ("Historic core walking route", "history", "context-rich", 2.5, 18, False, True, False, "Anchor the day with the most storied district and one standout landmark."),
    "food": ("Signature neighborhood tasting crawl", "food", "social", 2.5, 32, False, False, True, "Build the day around a local food street, market, or bistro cluster."),
    "culture": ("Museum and old-town combination", "culture", "immersive", 2.5, 24, True, True, False, "Pair one cultural anchor with a slower neighborhood wander."),
    "architecture": ("Design and architecture circuit", "architecture", "visual", 2.0, 16, False, True, True, "Focus on the most photogenic district and one iconic building."),
    "art": ("Gallery-led creative afternoon", "art", "refined", 2.0, 20, True, False, False, "Keep the art block selective so the day still feels light."),
    "relaxation": ("Slow scenic reset", "relaxation", "calm", 1.5, 10, False, False, True, "Use a park, waterfront, or viewpoint to create breathing room."),
    "beach": ("Coastal or lakeside unwind", "beach", "easygoing", 2.0, 14, False, False, True, "A flexible soft-energy block when the weather cooperates."),
    "nightlife": ("Late-night local hotspot run", "nightlife", "lively", 2.5, 28, False, False, True, "Reserve one evening for the city’s most atmospheric bars or music spots."),
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Manrope:wght@400;500;600;700&display=swap');
        :root {
            --bg: #f3f1ec;
            --paper: rgba(255, 255, 255, 0.78);
            --card: rgba(255, 255, 255, 0.9);
            --ink: #15181c;
            --muted: #66707a;
            --accent: #ae8a5c;
            --accent-soft: rgba(174, 138, 92, 0.12);
            --line: rgba(21, 24, 28, 0.08);
            --shadow: 0 20px 48px rgba(15, 20, 28, 0.08);
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 255, 255, 0.55), transparent 20%),
                radial-gradient(circle at 88% 0%, rgba(174, 138, 92, 0.1), transparent 16%),
                linear-gradient(180deg, #f8f7f4 0%, var(--bg) 100%);
            color: var(--ink);
            font-family: "Manrope", sans-serif;
        }
        .block-container {
            max-width: 1180px;
            padding-top: 1.1rem;
            padding-bottom: 3rem;
        }
        h1, h2, h3 {
            font-family: "Fraunces", serif;
            color: var(--ink);
            letter-spacing: -0.03em;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f6f5f2 0%, #efede8 100%);
            border-right: 1px solid var(--line);
        }
        [data-testid="stSidebar"] * {
            color: var(--ink);
        }
        [data-testid="stMetric"] {
            background: var(--paper);
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 0.85rem 1rem;
            box-shadow: none;
        }
        [data-testid="stVerticalBlock"] [data-testid="stContainer"] {
            border-radius: 22px;
        }
        .hero {
            background:
                linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(249, 247, 243, 0.82));
            border: 1px solid rgba(21, 24, 28, 0.08);
            border-radius: 32px;
            padding: 1.6rem 1.7rem;
            color: var(--ink);
            box-shadow: var(--shadow);
            margin-bottom: 1.15rem;
        }
        .eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.22em;
            font-size: 0.72rem;
            color: var(--muted);
            margin-bottom: 0.45rem;
        }
        .hero-title {
            font-size: 3rem;
            line-height: 0.94;
            margin-bottom: 0.6rem;
            max-width: 760px;
        }
        .hero-copy {
            max-width: 680px;
            color: var(--muted);
        }
        .hero-strip {
            display: flex;
            gap: 0.7rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }
        .chip {
            background: rgba(21, 24, 28, 0.03);
            border: 1px solid rgba(21, 24, 28, 0.08);
            border-radius: 999px;
            padding: 0.45rem 0.75rem;
            font-size: 0.78rem;
        }
        .chip.ai-on {
            background: var(--accent-soft);
            border-color: rgba(174, 138, 92, 0.24);
        }
        .stButton > button,
        .stDownloadButton > button {
            border-radius: 999px;
            border: 1px solid rgba(21, 24, 28, 0.08);
            background: linear-gradient(180deg, #171a1f 0%, #20252c 100%);
            color: #f7f5f1;
            padding: 0.65rem 1rem;
            font-weight: 600;
            box-shadow: none;
        }
        .stButton > button:hover,
        .stDownloadButton > button:hover {
            border-color: rgba(21, 24, 28, 0.14);
            background: linear-gradient(180deg, #111418 0%, #1a1e24 100%);
            color: #ffffff;
        }
        .stTextInput input,
        .stTextArea textarea,
        .stDateInput input,
        .stSelectbox [data-baseweb="select"] > div,
        .stMultiSelect [data-baseweb="select"] > div {
            border-radius: 16px !important;
            background: rgba(255, 255, 255, 0.82) !important;
            border: 1px solid rgba(21, 24, 28, 0.08) !important;
        }
        .stCodeBlock {
            border-radius: 22px;
            border: 1px solid var(--line);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def trip_length(start_date: date, end_date: date) -> int:
    return (end_date - start_date).days + 1


def validate_trip_inputs(start_date: date, end_date: date, interests: list[str], trip_days: int) -> list[str]:
    errors: list[str] = []
    if end_date < start_date:
        errors.append("End date must be on or after the start date.")
    if trip_days > 7:
        errors.append("This MVP supports trips up to 7 days so the itinerary stays readable.")
    if not interests:
        errors.append("Pick at least one interest so the itinerary has a clear direction.")
    return errors


def choose_activities(destination: str, interests: list[str], pace: str, wants_nightlife: bool) -> list[Activity]:
    pool = get_destination_context(destination, interests)["activities"]
    scored: list[tuple[int, Activity]] = []
    for activity in pool:
        score = 0
        if activity.category in interests:
            score += 4
        if wants_nightlife and activity.category == "nightlife":
            score += 3
        if pace == "Slow" and activity.duration_hours <= 2.0:
            score += 2
        if pace == "Fast" and activity.duration_hours >= 2.5:
            score += 2
        if activity.category == "relaxation":
            score += 1
        scored.append((score, activity))
    ranked = [item for _, item in sorted(scored, key=lambda pair: (pair[0], -pair[1].price_eur), reverse=True)]
    return ranked


def build_daily_plan(
    destination: str,
    start_date: date,
    end_date: date,
    interests: list[str],
    pace: str,
    budget_style: str,
    wants_nightlife: bool,
) -> list[dict[str, object]]:
    days = trip_length(start_date, end_date)
    ranked_activities = choose_activities(destination, interests, pace, wants_nightlife)
    slots = ["Morning", "Afternoon", "Evening"][: PACE_TARGETS[pace]]
    itinerary: list[dict[str, object]] = []
    used_titles: set[str] = set()

    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        day_items: list[dict[str, object]] = []
        for slot in slots:
            activity = next(
                (
                    candidate
                    for candidate in ranked_activities
                    if candidate.title not in used_titles
                    and ((slot == "Morning" and candidate.morning_fit) or (slot == "Evening" and candidate.evening_fit) or slot == "Afternoon")
                ),
                None,
            )
            if activity is None:
                activity = ranked_activities[(day_offset + len(day_items)) % len(ranked_activities)]
            used_titles.add(activity.title)
            day_items.append({"slot": slot, "activity": activity})

        daily_spend = sum(item["activity"].price_eur for item in day_items)
        itinerary.append(
            {
                "date": current_date,
                "theme": f"Day {day_offset + 1} - {'Arrival flow' if day_offset == 0 else 'Local rhythm'}",
                "items": day_items,
                "daily_spend": daily_spend + int(get_destination_context(destination, interests)["daily_budget"][budget_style] * 0.35),
            }
        )
    return itinerary


def format_currency(amount: int) -> str:
    return f"EUR {amount}"


def get_ollama_mode_profile(selected_mode: str) -> dict[str, Any]:
    return OLLAMA_MODE_PROFILES.get(selected_mode, OLLAMA_MODE_PROFILES["Balanced"])


def ollama_ready(selected_mode: str) -> tuple[bool, str]:
    profile = get_ollama_mode_profile(selected_mode)
    return True, f"{selected_mode} local mode ready via {profile['model']} at {DEFAULT_OLLAMA_URL}."


def get_ollama_status() -> tuple[bool, list[str], str]:
    request = Request(f"{DEFAULT_OLLAMA_URL}/api/tags", method="GET")
    try:
        with urlopen(request, timeout=5) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception:
        return False, [], f"Ollama is not reachable at {DEFAULT_OLLAMA_URL}. Start it with `ollama serve`."

    models = [item.get("name", "") for item in body.get("models", []) if item.get("name")]
    return True, models, f"Ollama is reachable at {DEFAULT_OLLAMA_URL}."


def build_generic_destination(destination: str, interests: list[str]) -> dict[str, object]:
    selected_interests = interests or ["culture", "food", "architecture"]
    best_for = selected_interests[:4]
    activities = [
        Activity(
            title=f"{destination} {title}",
            category=category,
            vibe=vibe,
            duration_hours=duration_hours,
            price_eur=price_eur,
            indoor=indoor,
            morning_fit=morning_fit,
            evening_fit=evening_fit,
            description=description,
        )
        for interest in selected_interests
        for title, category, vibe, duration_hours, price_eur, indoor, morning_fit, evening_fit, description in [GENERIC_ACTIVITY_LIBRARY[interest]]
    ]
    activities.extend(
        [
            Activity(
                f"{destination} old town orientation walk",
                "culture",
                "wandering",
                1.5,
                0,
                False,
                True,
                True,
                "Use the first day to understand the city center, key districts, and easy dining options.",
            ),
            Activity(
                f"{destination} signature viewpoint stop",
                "relaxation",
                "scenic",
                1.5,
                0,
                False,
                False,
                True,
                "A short scenic payoff that gives the itinerary a strong emotional moment.",
            ),
        ]
    )
    return {
        "country": "Custom",
        "airport": "TBD",
        "best_for": best_for,
        "daily_budget": {"Budget": 120, "Comfort": 210, "Premium": 340},
        "packing": ["Comfortable walking shoes", "Phone charger", "Weather-ready layer"],
        "activities": activities,
    }


def get_destination_context(destination: str, interests: list[str]) -> dict[str, object]:
    if destination in DESTINATIONS:
        return DESTINATIONS[destination]
    return build_generic_destination(destination, interests)


def itinerary_totals(destination: str, interests: list[str], budget_style: str, itinerary: list[dict[str, object]]) -> dict[str, int]:
    lodging_food = int(get_destination_context(destination, interests)["daily_budget"][budget_style]) * len(itinerary)
    experiences = sum(int(day["daily_spend"]) for day in itinerary)
    total = lodging_food + experiences
    return {"lodging_food": lodging_food, "experiences": experiences, "total": total}


def build_ai_grounding_payload(
    destination: str,
    neighborhood: str,
    season: str,
    travel_party: str,
    budget_style: str,
    pace: str,
    interests: list[str],
    wants_nightlife: bool,
    trip_goal: str,
    must_do: str,
    avoid: str,
    notes: str,
    itinerary: list[dict[str, object]],
    totals: dict[str, int],
) -> dict[str, Any]:
    compact_notes = notes.strip()[:280]
    compact_goal = trip_goal.strip()[:160]
    compact_must_do = must_do.strip()[:120]
    compact_avoid = avoid.strip()[:120]
    return {
        "destination": destination,
        "country": get_destination_context(destination, interests)["country"],
        "airport": get_destination_context(destination, interests)["airport"],
        "base_neighborhood": neighborhood,
        "season": season,
        "travel_party": travel_party,
        "budget_style": budget_style,
        "pace": pace,
        "interests": interests,
        "wants_nightlife": wants_nightlife,
        "trip_goal": compact_goal,
        "must_do": compact_must_do,
        "avoid": compact_avoid,
        "notes": compact_notes,
        "budget_snapshot_eur": totals,
        "destination_strengths": get_destination_context(destination, interests)["best_for"],
        "suggested_days": [
            {
                "day_number": index + 1,
                "date": day["date"].isoformat(),
                "theme": day["theme"],
                "slots": [
                    {
                        "slot": item["slot"],
                        "title": item["activity"].title,
                        "category": item["activity"].category,
                        "vibe": item["activity"].vibe,
                        "price_eur": item["activity"].price_eur,
                    }
                    for item in day["items"]
                ],
            }
            for index, day in enumerate(itinerary)
        ],
    }


def generate_ollama_trip_plan(grounding_payload: dict[str, Any], day_count: int, selected_mode: str) -> AITripResponse:
    profile = get_ollama_mode_profile(selected_mode)
    compact_days = []
    for day in grounding_payload["suggested_days"]:
        compact_days.append(
            {
                "day_number": day["day_number"],
                "theme": day["theme"],
                "slots": [f"{slot['slot']}: {slot['title']}" for slot in day["slots"]],
            }
        )

    compact_payload = {
        "destination": grounding_payload["destination"],
        "base_neighborhood": grounding_payload["base_neighborhood"],
        "season": grounding_payload["season"],
        "travel_party": grounding_payload["travel_party"],
        "budget_style": grounding_payload["budget_style"],
        "pace": grounding_payload["pace"],
        "interests": grounding_payload["interests"],
        "trip_goal": grounding_payload["trip_goal"],
        "must_do": grounding_payload["must_do"],
        "avoid": grounding_payload["avoid"],
        "destination_strengths": grounding_payload["destination_strengths"],
        "suggested_days": compact_days,
    }
    prompt = dedent(
        f"""
        You are a premium travel planner.

        Create a concise but polished itinerary for exactly {day_count} day(s).
        Keep the writing elegant, practical, and compact.

        Requirements:
        - Respect the destination, pace, budget style, season, and travel-party context.
        - Use the suggested activities as grounding.
        - Keep each field short and direct.
        - Prefer realistic neighborhood flow over overexplaining.
        - Do not invent flights, exact restaurant reservations, or impossible transfers.
        - Return only JSON that matches the provided schema.

        Grounding data:
        {json.dumps(compact_payload, ensure_ascii=True, separators=(",", ":"))}
        """
    ).strip()

    payload = {
        "model": profile["model"],
        "stream": False,
        "messages": [{"role": "user", "content": prompt}],
        "format": AITripResponse.model_json_schema(),
        "options": {"temperature": profile["temperature"], "num_predict": profile["max_tokens"], "num_ctx": 4096},
    }
    request = Request(
        f"{DEFAULT_OLLAMA_URL}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=OLLAMA_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(
            f"Could not reach Ollama at {DEFAULT_OLLAMA_URL}. Make sure Ollama is running and the model is pulled."
        ) from exc

    content = body.get("message", {}).get("content", "")
    if not content:
        raise RuntimeError("Ollama returned an empty response.")
    return AITripResponse.model_validate_json(content)


def build_markdown_export(
    destination: str,
    neighborhood: str,
    season: str,
    travel_party: str,
    budget_style: str,
    itinerary: list[dict[str, object]],
    totals: dict[str, int],
    notes: str,
) -> str:
    lines = [
        f"# {destination} itinerary",
        "",
        f"- Base area: {neighborhood}",
        f"- Season: {season}",
        f"- Travel party: {travel_party}",
        f"- Budget style: {budget_style}",
        f"- Estimated total: {format_currency(totals['total'])}",
        "",
        "## Daily plan",
    ]
    for day in itinerary:
        lines.append("")
        lines.append(f"### {day['theme']} ({day['date'].strftime('%a %d %b %Y')})")
        for item in day["items"]:
            activity: Activity = item["activity"]
            lines.append(
                f"- {item['slot']}: {activity.title} | {activity.description} | {format_currency(activity.price_eur)}"
            )
    lines.extend(
        [
            "",
            "## Budget snapshot",
            f"- Lodging and food: {format_currency(totals['lodging_food'])}",
            f"- Activities and local transit buffer: {format_currency(totals['experiences'])}",
            f"- Total: {format_currency(totals['total'])}",
        ]
    )
    if notes.strip():
        lines.extend(["", "## Trip notes", notes.strip()])
    return "\n".join(lines)


def build_ai_markdown_export(
    destination: str,
    neighborhood: str,
    season: str,
    travel_party: str,
    budget_style: str,
    totals: dict[str, int],
    ai_plan: AITripResponse,
) -> str:
    lines = [
        f"# {destination} concierge itinerary",
        "",
        f"- Base area: {neighborhood}",
        f"- Season: {season}",
        f"- Travel party: {travel_party}",
        f"- Budget style: {budget_style}",
        f"- Estimated total: {format_currency(totals['total'])}",
        "",
        "## Overview",
        ai_plan.overview,
        "",
        "## Daily plan",
    ]
    for day in ai_plan.days:
        lines.extend(
            [
                "",
                f"### Day {day.day_number} - {day.title}",
                f"- Morning: {day.morning_plan}",
                f"- Afternoon: {day.afternoon_plan}",
                f"- Evening: {day.evening_plan}",
                f"- Logistics: {day.logistics_tip}",
            ]
        )
    lines.extend(
        [
            "",
            "## Concierge brief",
            f"- Hook: {ai_plan.brief.trip_hook}",
            f"- Client summary: {ai_plan.brief.client_summary}",
            "",
            "## Booking checklist",
            *[f"- {item}" for item in ai_plan.brief.booking_checklist],
            "",
            "## Upgrade idea",
            ai_plan.brief.concierge_upgrade,
        ]
    )
    return "\n".join(lines)


def render_hero(destination: str, trip_days: int, travel_party: str, best_for: list[str], ai_enabled: bool) -> None:
    chip_items = [f"{trip_days} days", travel_party, *best_for[:3]]
    if ai_enabled:
        chip_items.insert(0, "AI concierge")
    chips = "".join(
        f"<span class='chip{' ai-on' if label == 'AI concierge' else ''}'>{label}</span>" for label in chip_items
    )
    st.markdown(
        f"""
        <section class="hero">
            <div class="eyebrow">Day 04 • Travel Itinerary Builder</div>
            <div class="hero-title">Build a trip plan that feels considered, not copy-pasted.</div>
            <div class="hero-copy">
                Turn a destination, pace, and travel style into a day-by-day city itinerary with timing ideas,
                budget guidance, and a client-ready concierge brief powered by structured GenAI.
            </div>
            <div class="hero-strip">{chips}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"Planning for {destination}. Adjust the sidebar inputs to regenerate the route instantly.")


def render_metrics(destination: str, season: str, itinerary: list[dict[str, object]], totals: dict[str, int]) -> None:
    avg_daily = round(totals["total"] / max(len(itinerary), 1))
    airport = get_destination_context(destination, [])["airport"]
    cols = st.columns(4)
    cols[0].metric("Estimated total", format_currency(totals["total"]), help="Activities, food, and stay budget blended.")
    cols[1].metric("Avg daily spend", format_currency(avg_daily), help="Useful for adjusting pace or upgrade choices.")
    cols[2].metric("Best arrival airport", airport, help="Handy shortcut for booking research.")
    cols[3].metric("Season mode", season, help="Packing notes and day rhythm adapt to it.")


def render_itinerary(itinerary: list[dict[str, object]], ai_plan: AITripResponse | None = None) -> None:
    st.subheader("Day-by-day itinerary")
    ai_days = {day.day_number: day for day in ai_plan.days} if ai_plan else {}
    for index, day in enumerate(itinerary, start=1):
        ai_day = ai_days.get(index)
        with st.container(border=True):
            st.markdown(f"### {ai_day.title if ai_day else day['theme']}")
            st.caption(day["date"].strftime("%A, %d %B %Y"))
            for item in day["items"]:
                activity: Activity = item["activity"]
                ai_copy = {
                    "Morning": ai_day.morning_plan if ai_day else activity.description,
                    "Afternoon": ai_day.afternoon_plan if ai_day else activity.description,
                    "Evening": ai_day.evening_plan if ai_day else activity.description,
                }
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.markdown(f"**{item['slot']} • {activity.title}**")
                    st.write(ai_copy[item["slot"]])
                    st.caption(
                        f"{activity.category} · {activity.vibe} · {activity.duration_hours:.1f}h · "
                        f"{'Indoor backup' if activity.indoor else 'Outdoor lean'}"
                    )
                with col_b:
                    st.metric("Price", format_currency(activity.price_eur))


def render_ai_brief(ai_plan: AITripResponse) -> None:
    st.subheader("Client-facing concierge brief")
    with st.container(border=True):
        st.markdown(f"### {ai_plan.brief.trip_hook}")
        st.write(ai_plan.overview)
        st.write(ai_plan.brief.client_summary)
        st.write(f"**Upgrade idea:** {ai_plan.brief.concierge_upgrade}")

    st.markdown("**Booking checklist**")
    for item in ai_plan.brief.booking_checklist:
        st.write(f"- {item}")


def render_side_guides(destination: str, season: str, totals: dict[str, int], notes: str) -> None:
    destination_info = get_destination_context(destination, [])
    packing_list = destination_info["packing"] + SEASON_PACKING[season]
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Packing and prep")
        for item in packing_list:
            st.write(f"- {item}")
    with col2:
        st.subheader("Budget split")
        st.write(f"- Lodging and food: {format_currency(totals['lodging_food'])}")
        st.write(f"- Activities and local transit: {format_currency(totals['experiences'])}")
        st.write(f"- Total trip estimate: {format_currency(totals['total'])}")
        if notes.strip():
            st.write("")
            st.write(f"Planner note: {notes.strip()}")


def main() -> None:
    st.set_page_config(page_title="Day 04 - Travel Itinerary Builder", page_icon="🧭", layout="wide")
    inject_css()

    st.sidebar.title("Trip inputs")
    destination_choice = st.sidebar.selectbox("Destination", list(DESTINATIONS.keys()) + ["Custom"])
    custom_destination = st.sidebar.text_input(
        "Custom location",
        placeholder="Example: Lisbon, Kyoto, Cape Town",
        disabled=destination_choice != "Custom",
    )
    destination = custom_destination.strip() if destination_choice == "Custom" and custom_destination.strip() else destination_choice
    today = date.today()
    start_date = st.sidebar.date_input("Start date", value=today + timedelta(days=21))
    end_date = st.sidebar.date_input("End date", value=today + timedelta(days=24))
    budget_style = st.sidebar.selectbox("Budget style", ["Budget", "Comfort", "Premium"], index=1)
    pace = st.sidebar.selectbox("Trip pace", ["Slow", "Balanced", "Fast"], index=1)
    season = st.sidebar.selectbox("Season", ["Spring", "Summer", "Autumn", "Winter"])
    travel_party = st.sidebar.selectbox("Travel party", ["Solo", "Couple", "Friends", "Family"])
    neighborhood = st.sidebar.text_input("Base neighborhood", value="City center")
    trip_goal = st.sidebar.text_input("Trip goal", value="A polished city break with standout food, clear pacing, and memorable highlights")
    must_do = st.sidebar.text_input("Must-do highlight", placeholder="Example: sunset rooftop drink, one iconic museum, local market")
    avoid = st.sidebar.text_input("Avoid", placeholder="Example: packed nightlife, too many museums, long taxi hops")
    interests = st.sidebar.multiselect(
        "Interests",
        ["history", "food", "culture", "architecture", "art", "relaxation", "beach", "nightlife"],
        default=list(get_destination_context(destination, [])["best_for"][:3]),
    )
    wants_nightlife = st.sidebar.toggle("Bias one evening toward nightlife", value=travel_party in {"Couple", "Friends"})
    st.sidebar.markdown("### AI concierge")
    selected_ai_mode = st.sidebar.selectbox(
        "AI mode",
        ["Cheap", "Balanced", "Premium"],
        index=0,
        help="Choose the tradeoff between cost, speed, and richness of the generated itinerary copy.",
    )
    ollama_up, available_models, ollama_status = get_ollama_status()
    ai_mode_ready, ai_status = ollama_ready(selected_ai_mode)
    ai_mode_label = get_ollama_mode_profile(selected_ai_mode)["label"]
    selected_model = get_ollama_mode_profile(selected_ai_mode)["model"]
    ai_enabled_default = False
    enable_ai = st.sidebar.toggle(
        "Enable AI client-ready copy",
        value=ai_enabled_default,
        disabled=not ollama_up,
    )
    st.sidebar.caption(ai_mode_label)
    st.sidebar.caption(ai_status if ollama_up else ollama_status)
    if ollama_up:
        st.sidebar.caption(f"Selected model: `{selected_model}`")
        if available_models:
            st.sidebar.caption(f"Installed models: {', '.join(available_models[:4])}")
        if available_models and selected_model not in available_models:
            st.sidebar.warning(
                f"`{selected_model}` is not installed in Ollama yet. Pull it first or switch the mode."
            )
    st.sidebar.caption(
        f"Run `ollama serve` and pull a model such as `qwen3:4b`. Timeout is currently {OLLAMA_TIMEOUT_SECONDS}s."
    )
    notes = st.sidebar.text_area(
        "Trip notes",
        placeholder="Example: arriving late on day 1, prefer one museum max per day, vegetarian-friendly stops.",
    )

    trip_days = trip_length(start_date, end_date)
    errors = validate_trip_inputs(start_date, end_date, interests, trip_days)

    render_hero(destination, max(trip_days, 1), travel_party, list(get_destination_context(destination, interests)["best_for"]), enable_ai)

    if errors:
        for error in errors:
            st.error(error)
        st.stop()

    itinerary = build_daily_plan(destination, start_date, end_date, interests, pace, budget_style, wants_nightlife)
    totals = itinerary_totals(destination, interests, budget_style, itinerary)
    ai_plan: AITripResponse | None = None
    grounding_payload = build_ai_grounding_payload(
        destination=destination,
        neighborhood=neighborhood,
        season=season,
        travel_party=travel_party,
        budget_style=budget_style,
        pace=pace,
        interests=interests,
        wants_nightlife=wants_nightlife,
        trip_goal=trip_goal,
        must_do=must_do,
        avoid=avoid,
        notes=notes,
        itinerary=itinerary,
        totals=totals,
    )
    grounding_signature = json.dumps({"mode": selected_ai_mode, "payload": grounding_payload}, sort_keys=True)
    generate_ai = False
    if enable_ai and ollama_up and ai_mode_ready:
        if "trip_ai_cache" not in st.session_state:
            st.session_state.trip_ai_cache = {}
        ai_cache: dict[str, dict[str, Any]] = st.session_state.trip_ai_cache
        can_generate_ai = not available_models or selected_model in available_models
        generate_ai = st.sidebar.button(
            "Generate AI concierge draft",
            use_container_width=True,
            disabled=not can_generate_ai,
        )
        if grounding_signature in ai_cache:
            ai_plan = AITripResponse.model_validate(ai_cache[grounding_signature])
        if generate_ai:
            with st.spinner("Generating a client-ready itinerary..."):
                try:
                    ai_plan = generate_ollama_trip_plan(grounding_payload, len(itinerary), selected_ai_mode)
                    ai_cache[grounding_signature] = ai_plan.model_dump()
                except Exception as exc:
                    st.warning(
                        f"AI generation did not finish, so the app is showing the curated fallback plan. "
                        f"If you are using a local model, keep `ollama serve` running and try `Cheap` mode first. Details: {exc}"
                    )

    render_metrics(destination, season, itinerary, totals)

    left, right = st.columns([1.8, 1.0], gap="large")
    with left:
        render_itinerary(itinerary, ai_plan=ai_plan)
        if ai_plan:
            render_ai_brief(ai_plan)
    with right:
        st.subheader("Planner summary")
        with st.container(border=True):
            st.write(f"**Base area:** {neighborhood}")
            st.write(
                f"**Destination angle:** {destination} is strongest for "
                f"{', '.join(get_destination_context(destination, interests)['best_for'][:3])}."
            )
            st.write(f"**Trip rhythm:** {pace} pace with {PACE_TARGETS[pace]} structured blocks per day.")
            st.write(f"**Client objective:** {trip_goal}")
        if ai_plan:
            st.subheader("AI planning lens")
            with st.container(border=True):
                st.write(f"**Overview:** {ai_plan.overview}")
                st.write(f"**Upgrade angle:** {ai_plan.brief.concierge_upgrade}")
        render_side_guides(destination, season, totals, notes)

    markdown_export = (
        build_ai_markdown_export(
            destination=destination,
            neighborhood=neighborhood,
            season=season,
            travel_party=travel_party,
            budget_style=budget_style,
            totals=totals,
            ai_plan=ai_plan,
        )
        if ai_plan
        else build_markdown_export(
            destination=destination,
            neighborhood=neighborhood,
            season=season,
            travel_party=travel_party,
            budget_style=budget_style,
            itinerary=itinerary,
            totals=totals,
            notes=notes,
        )
    )

    st.subheader("Shareable export")
    st.code(markdown_export, language="markdown")
    st.download_button(
        "Download itinerary as Markdown",
        data=markdown_export.encode("utf-8"),
        file_name=f"{destination.lower()}-itinerary.md",
        mime="text/markdown",
    )


if __name__ == "__main__":
    main()
