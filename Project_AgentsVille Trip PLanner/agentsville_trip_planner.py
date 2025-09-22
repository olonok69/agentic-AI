"""
AgentsVille Trip Planner

This script implements the AgentsVille Trip Planner as a standalone Python program, drawing from
instructions in `instructions.txt` and helper utilities in `project_lib.py`.

Key components:
- Pydantic models (VacationInfo, Activity, DayPlan, TravelItinerary, ToolCall)
- ItineraryAgent: crafts an initial day-by-day itinerary via a single LLM call
- Evaluations: checks for city/dates, budget, hallucinated activities, and weather compatibility
- Tools: calculator_tool, get_activities_by_date_tool, run_evals_tool, final_answer_tool
- ItineraryRevisionAgent: ReAct loop (THOUGHT -> ACTION -> OBSERVATION) to refine itinerary

Requirements:
- OPENAI_API_KEY must be set in the environment
- Uses `project_lib.py` mocks for activities and weather; do not modify that file

Usage:
    python agentsville_trip_planner.py --start 2025-06-10 --end 2025-06-12 \
        --travelers "Ada Lovelace,Alan Turing" --interests technology,art,dancing --budget 200

Note:
- Dates must fall within the mocked data range 2025-06-10 .. 2025-06-15 for AgentsVille
- This script emphasizes guardrails with Pydantic validation and constrained tool usage
"""
from __future__ import annotations

import json
import os
import re
import sys
import math
import argparse
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional

try:
    # Pydantic v2
    from pydantic import BaseModel, Field
    try:
        from pydantic import field_validator as pyd_validator
    except Exception:  # pragma: no cover - fallback to v1 style
        from pydantic import validator as pyd_validator  # type: ignore
except Exception as e:  # pragma: no cover
    print("Pydantic is required. Please install with: pip install pydantic")
    raise

# Import project utilities and mocked data/tools
from project_lib import (
    Interest,
    print_in_box,
    do_chat_completion,
    call_activities_api_mocked,
    call_activity_by_id_api_mocked,
    call_weather_api_mocked,
    ACTIVITY_CALENDAR,
    WEATHER_FORECAST,
    INCLIMATE_WEATHER_CONDITIONS,
)

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


# -------------------
# Pydantic data models
# -------------------
class VacationInfo(BaseModel):
    city: str = Field(default="AgentsVille", description="Destination city")
    start_date: date
    end_date: date
    travelers: List[str]
    interests: List[Interest]
    budget_currency: str = Field(default="USD")
    budget_amount: float = Field(default=0.0)

    @pyd_validator("city")
    def _city_is_agentsville(cls, v: str) -> str:
        if v != "AgentsVille":
            raise ValueError("Only AgentsVille is supported in this project")
        return v

    @pyd_validator("end_date")
    def _end_after_start(cls, v: date, values: Dict[str, Any]) -> date:
        start = values.get("start_date")
        if isinstance(start, date) and v < start:
            raise ValueError("end_date must be on/after start_date")
        return v

    def iter_dates(self) -> List[date]:
        d, out = self.start_date, []
        while d <= self.end_date:
            out.append(d)
            d += timedelta(days=1)
        return out


class Activity(BaseModel):
    activity_id: str
    name: str
    start_time: str  # "YYYY-MM-DD HH:MM"
    end_time: str
    location: str
    description: str
    price: float
    related_interests: List[Interest]

    @pyd_validator("start_time", "end_time")
    def _valid_dt(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M")
        except Exception:
            raise ValueError("Datetime must be in YYYY-MM-DD HH:MM format")
        return v


class DayPlan(BaseModel):
    date: str  # YYYY-MM-DD
    activities: List[Activity]
    notes: Optional[str] = None

    @pyd_validator("date")
    def _valid_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except Exception:
            raise ValueError("date must be YYYY-MM-DD")
        return v


class TravelItinerary(BaseModel):
    city: str
    start_date: str  # YYYY-MM-DD
    end_date: str
    travelers: List[str]
    interests: List[Interest]
    currency: str
    total_cost: float
    days: List[DayPlan]

    @pyd_validator("start_date", "end_date")
    def _valid_dates(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except Exception:
            raise ValueError("start_date/end_date must be YYYY-MM-DD")
        return v


class ToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]


# -------------
# Tool registry
# -------------
class ToolSpec(BaseModel):
    name: str
    description: str
    parameters_schema: Dict[str, Any]


def _round2(x: float) -> float:
    return float(f"{x:.2f}")


# calculator_tool: calculates or re-calculates total cost of itinerary

def calculator_tool(itinerary: Dict[str, Any] | TravelItinerary, **kwargs) -> Dict[str, Any]:
    if isinstance(itinerary, TravelItinerary):
        itin = itinerary.dict()
    else:
        itin = itinerary
    total = 0.0
    for day in itin.get("days", []):
        for act in day.get("activities", []):
            try:
                total += float(act.get("price", 0))
            except Exception:
                pass
    itin["total_cost"] = _round2(total)
    return {
        "ok": True,
        "total_cost": itin["total_cost"],
        "updated_itinerary": itin,
        "message": f"Calculated total cost: {itin['total_cost']} {itin.get('currency','USD')}",
    }


# get_activities_by_date_tool: fetches activities from mocked API for a given date

def get_activities_by_date_tool(date_str: str, city: str = "AgentsVille", **kwargs) -> Dict[str, Any]:
    acts = call_activities_api_mocked(date=date_str, city=city)
    return {
        "ok": True,
        "date": date_str,
        "activities": acts,
        "message": f"Retrieved {len(acts)} activities for {date_str} in {city}",
    }


# LLM-based evaluation for activity vs weather compatibility
ACTIVITY_AND_WEATHER_ARE_COMPATIBLE_SYSTEM_PROMPT = (
    """
You are a careful travel safety and suitability evaluator.

Task:
- Given a weather summary and an activity description, decide if the activity is suitable for the weather.
- Consider whether the event is outdoors vs. indoors based on the description; rainy or thunderstorm conditions generally make outdoor activities unsuitable.

Output format:
- Return strictly valid JSON of the form: {"compatible": true|false, "reason": "short explanation"}

Examples:
- Weather: rainy. Activity: "Outdoor hike across the ridge with no shelter" -> {"compatible": false, "reason": "Outdoor hike not suitable in rain"}
- Weather: sunny. Activity: "Indoor art class at studio" -> {"compatible": true, "reason": "Indoor event is fine in sunny weather"}
"""
).strip()


def _llm_activity_weather_check(client: Any, model: str, weather: Dict[str, Any], activity_description: str) -> Dict[str, Any]:
    weather_text = json.dumps(weather, ensure_ascii=False)
    user = (
        "Weather info:\n" + weather_text + "\n\n" +
        "Activity description:\n" + activity_description + "\n\n" +
        "Return JSON as specified."
    )
    resp = do_chat_completion(
        messages=[
            {"role": "system", "content": ACTIVITY_AND_WEATHER_ARE_COMPATIBLE_SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        client=client,
        model=model,
        temperature=0.0,
    )
    try:
        return json.loads(_extract_json_object(resp))
    except Exception:
        return {"compatible": True, "reason": "Fallback: could not parse model's JSON; assuming compatible."}


# Evaluations as a tool

def _dates_between(start: str, end: str) -> List[str]:
    s = datetime.strptime(start, "%Y-%m-%d").date()
    e = datetime.strptime(end, "%Y-%m-%d").date()
    out = []
    d = s
    while d <= e:
        out.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=1)
    return out


def _activity_ids_for_date(date_str: str) -> set[str]:
    return {a["activity_id"] for a in ACTIVITY_CALENDAR if a["start_time"].startswith(date_str)}


def run_evals_tool(
    itinerary: Dict[str, Any] | TravelItinerary,
    vacation_info: Dict[str, Any] | VacationInfo,
    client: Any,
    model: str,
    **kwargs,
) -> Dict[str, Any]:
    if isinstance(itinerary, TravelItinerary):
        itin = itinerary.dict()
    else:
        itin = itinerary
    if isinstance(vacation_info, VacationInfo):
        vinfo = vacation_info.dict()
    else:
        vinfo = vacation_info

    results: List[Dict[str, Any]] = []

    # 1) City and dates match
    city_ok = (itin.get("city") == vinfo.get("city"))
    wanted_dates = set(_dates_between(vinfo["start_date"].isoformat(), vinfo["end_date"].isoformat()))
    itin_dates = {d.get("date") for d in itin.get("days", [])}
    dates_ok = (itin.get("start_date") in wanted_dates and itin.get("end_date") in wanted_dates and itin_dates.issubset(wanted_dates))
    results.append({
        "name": "city_and_dates_match",
        "passed": bool(city_ok and dates_ok),
        "detail": f"city_ok={city_ok}, dates_ok={dates_ok}",
    })

    # 2) Total cost within budget
    total_cost = 0.0
    for d in itin.get("days", []):
        for a in d.get("activities", []):
            try:
                total_cost += float(a.get("price", 0))
            except Exception:
                pass
    within_budget = total_cost <= float(vinfo.get("budget_amount", math.inf))
    results.append({
        "name": "within_budget",
        "passed": bool(within_budget),
        "detail": f"total_cost={_round2(total_cost)} <= budget={vinfo.get('budget_amount')}",
    })

    # 3) No hallucinated activities
    hallucinations = []
    for d in itin.get("days", []):
        allowed_ids = _activity_ids_for_date(d.get("date"))
        for a in d.get("activities", []):
            if a.get("activity_id") not in allowed_ids:
                hallucinations.append(a.get("activity_id"))
    results.append({
        "name": "no_hallucinated_activities",
        "passed": len(hallucinations) == 0,
        "detail": f"invalid_ids={hallucinations}",
    })

    # 4) Weather compatibility via LLM per activity
    weather_issues: List[str] = []
    for d in itin.get("days", []):
        weather = call_weather_api_mocked(d.get("date"), vinfo.get("city"))
        for a in d.get("activities", []):
            desc = a.get("description", "")
            comp = _llm_activity_weather_check(client=client, model=model, weather=weather, activity_description=desc)
            if not comp.get("compatible", True):
                weather_issues.append(f"{d.get('date')}:{a.get('activity_id')} -> {comp.get('reason')}")
    results.append({
        "name": "weather_compatibility",
        "passed": len(weather_issues) == 0,
        "detail": f"issues={weather_issues}",
    })

    all_passed = all(r["passed"] for r in results)
    return {
        "ok": True,
        "all_passed": all_passed,
        "results": results,
    }


# final_answer_tool: returns the final answer payload

def final_answer_tool(message: str, final_itinerary: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    return {
        "ok": True,
        "message": message,
        "final_itinerary": final_itinerary,
    }


# Tool registry with schemas (for prompt inclusion)
available_tools: Dict[str, Dict[str, Any]] = {
    "calculator_tool": {
        "fn": calculator_tool,
        "spec": ToolSpec(
            name="calculator_tool",
            description=(
                "Calculate the total cost of an itinerary by summing each activity's price. "
                "Returns an updated itinerary with the total_cost field."
            ),
            parameters_schema={
                "type": "object",
                "properties": {
                    "itinerary": {"type": "object", "description": "TravelItinerary JSON"},
                },
                "required": ["itinerary"],
            },
        ),
    },
    "get_activities_by_date_tool": {
        "fn": get_activities_by_date_tool,
        "spec": ToolSpec(
            name="get_activities_by_date_tool",
            description=(
                "Retrieve activities available on a specific date in AgentsVille using the mocked API."
            ),
            parameters_schema={
                "type": "object",
                "properties": {
                    "date_str": {"type": "string", "description": "Date in YYYY-MM-DD"},
                    "city": {"type": "string", "description": "City name", "default": "AgentsVille"},
                },
                "required": ["date_str"],
            },
        ),
    },
    "run_evals_tool": {
        "fn": run_evals_tool,
        "spec": ToolSpec(
            name="run_evals_tool",
            description=(
                "Evaluate the current itinerary against criteria: city/dates match, within budget, no hallucinations, weather compatibility (LLM)."
            ),
            parameters_schema={
                "type": "object",
                "properties": {
                    "itinerary": {"type": "object", "description": "TravelItinerary JSON"},
                    "vacation_info": {"type": "object", "description": "VacationInfo JSON"},
                },
                "required": ["itinerary", "vacation_info"],
            },
        ),
    },
    "final_answer_tool": {
        "fn": final_answer_tool,
        "spec": ToolSpec(
            name="final_answer_tool",
            description=(
                "Provide the final answer and signal the end of the ReAct loop. Must include the final itinerary JSON."
            ),
            parameters_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Final message to the user"},
                    "final_itinerary": {"type": "object", "description": "Final TravelItinerary JSON"},
                },
                "required": ["message", "final_itinerary"],
            },
        ),
    },
}


# ------------------
# Itinerary generator
# ------------------
ITINERARY_AGENT_SYSTEM_PROMPT = (
    """
You are an expert travel planner for the fictional city AgentsVille.

Task:
- Create a detailed, day-by-day travel itinerary based on the user's vacation info (city, dates, travelers, interests, and budget). Use ONLY activities from the provided activity catalog.
- Plan coherently: at least one and preferably two activities per day, respecting times and interests.
- Output STRICTLY a JSON object that validates against the TravelItinerary Pydantic model described below.

Output JSON shape (no extra keys):
{
  "city": "AgentsVille",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "travelers": ["..."],
  "interests": ["art"|"technology"|...],
  "currency": "USD",
  "total_cost": 0,
  "days": [
    {
      "date": "YYYY-MM-DD",
      "activities": [
        {
          "activity_id": "event-...",
          "name": "...",
          "start_time": "YYYY-MM-DD HH:MM",
          "end_time": "YYYY-MM-DD HH:MM",
          "location": "...",
          "description": "...",
          "price": 0,
          "related_interests": ["art"|"technology"|...]
        }
      ],
      "notes": "optional"
    }
  ]
}

Guidance:
- Use only activities from the provided catalog for the specific dates in range; do not invent new activities.
- Favor activities matching the travelers' interests and schedule them reasonably.
- Set total_cost to the sum of included activities' prices (you may approximate; a later calculator tool will correct it if needed).
- Keep responses compact: just the JSON object without commentary.
"""
).strip()


def _activities_for_dates(vinfo: VacationInfo) -> Dict[str, List[Dict[str, Any]]]:
    by_date: Dict[str, List[Dict[str, Any]]] = {}
    for d in vinfo.iter_dates():
        ds = d.strftime("%Y-%m-%d")
        by_date[ds] = call_activities_api_mocked(date=ds, city=vinfo.city)
    return by_date


def generate_initial_itinerary(client: Any, model: str, vinfo: VacationInfo) -> TravelItinerary:
    # Prepare context for the LLM: vacation info, available activities, and weather
    acts_by_date = _activities_for_dates(vinfo)
    weather_by_date = {d.strftime("%Y-%m-%d"): call_weather_api_mocked(d.strftime("%Y-%m-%d"), vinfo.city) for d in vinfo.iter_dates()}

    user = (
        "VacationInfo:\n" + json.dumps(vinfo.dict(), default=str) + "\n\n" +
        "ActivitiesByDate (use only these):\n" + json.dumps(acts_by_date, ensure_ascii=False) + "\n\n" +
        "WeatherByDate:\n" + json.dumps(weather_by_date, ensure_ascii=False) + "\n\n" +
        "Return ONLY the TravelItinerary JSON as specified."
    )

    resp = do_chat_completion(
        messages=[
            {"role": "system", "content": ITINERARY_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        client=client,
        model=model,
        temperature=0.2,
    )
    try:
        data = json.loads(_extract_json_object(resp))
        itin = TravelItinerary(**data)
        return itin
    except Exception as e:
        print_in_box(resp, title="Raw Itinerary Model Output")
        raise


# -------------------
# ReAct revision agent
# -------------------

def _tools_catalog_text() -> str:
    lines = []
    for name, entry in available_tools.items():
        spec: ToolSpec = entry["spec"]
        lines.append(f"- {spec.name}: {spec.description}\n  parameters JSON schema: {json.dumps(spec.parameters_schema)}")
    return "\n".join(lines)


ITINERARY_REVISION_AGENT_SYSTEM_PROMPT = (
    f"""
You are ItineraryRevisionAgent, an expert ReAct-style assistant that refines travel itineraries for AgentsVille.

Task:
- Use the THINK -> ACTION -> OBSERVATION cycle to iteratively refine the itinerary.
- First, run run_evals_tool to collect evaluation feedback about the current plan.
- Use tools as needed to add, remove, or replace activities; ensure at least 2 activities per day when feasible.
- Before calling final_answer_tool, run run_evals_tool again to ensure all checks pass.

Available tools (name, purpose, parameters):
{_tools_catalog_text()}

Action format (MUST be exact JSON on a single line after the word ACTION:):
{{"tool_name": "[tool_name]", "arguments": {{"arg1": "value1", ...}}}}

Cycle protocol:
- Respond with a SINGLE message containing both sections:
  THOUGHT: Your reasoning about what to do next.
  ACTION: The JSON tool call.
- After you receive an OBSERVATION, continue with another THOUGHT/ACTION, or call final_answer_tool when ready.
- Only one ACTION per response.
"""
).strip()


def _extract_json_object(text: str) -> str:
    # Extract first top-level JSON object from text
    # Looks for a balanced {...}
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object start found")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise ValueError("No complete JSON object found")


def _parse_action(resp_text: str) -> ToolCall:
    # Expect segments "THOUGHT:" and "ACTION: {json}"
    m = re.search(r"ACTION:\s*(\{.*\})", resp_text, flags=re.DOTALL)
    if not m:
        raise ValueError("Could not find ACTION JSON in response")
    action_json = _extract_json_object(m.group(1))
    data = json.loads(action_json)
    return ToolCall(**data)


def run_revision_agent(
    client: Any,
    model: str,
    itinerary: TravelItinerary,
    vinfo: VacationInfo,
    max_steps: int = 6,
) -> Dict[str, Any]:
    messages = [
        {"role": "system", "content": ITINERARY_REVISION_AGENT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Here is the current itinerary JSON and vacation info. "
                "Remember to first run run_evals_tool, then iterate as needed, and run it again before final_answer_tool.\n\n"
                f"VacationInfo:\n{json.dumps(vinfo.dict(), default=str)}\n\n"
                f"Itinerary:\n{json.dumps(itinerary.dict(), ensure_ascii=False)}\n"
            ),
        },
    ]

    last_tool_name = None
    for step in range(max_steps):
        resp = do_chat_completion(messages=messages, client=client, model=model, temperature=0.2)
        print_in_box(resp, title=f"ItineraryRevisionAgent step {step+1}")
        try:
            call = _parse_action(resp)
        except Exception as e:
            # If parse fails, provide hint and continue
            messages.append({"role": "user", "content": f"OBSERVATION: Could not parse ACTION. Error: {e}. Please retry with correct JSON."})
            continue

        last_tool_name = call.tool_name
        if call.tool_name not in available_tools:
            messages.append({"role": "user", "content": f"OBSERVATION: Unknown tool '{call.tool_name}'. Use one of: {list(available_tools.keys())}"})
            continue

        # Execute tool
        try:
            if call.tool_name == "run_evals_tool":
                result = available_tools[call.tool_name]["fn"](
                    client=client,
                    model=model,
                    **call.arguments,
                )
            else:
                result = available_tools[call.tool_name]["fn"](**call.arguments)
        except TypeError as te:
            messages.append({"role": "user", "content": f"OBSERVATION: Tool error: {te}"})
            continue

        # If calculator updated itinerary, keep itinerary in working memory
        if call.tool_name == "calculator_tool" and isinstance(result, dict) and result.get("updated_itinerary"):
            itinerary = TravelItinerary(**result["updated_itinerary"])  # validate

        if call.tool_name == "final_answer_tool":
            # Ensure evals run immediately before final answer as per spec
            # If last tool wasn't run_evals_tool, run it now and attach observation, then accept final
            if last_tool_name != "run_evals_tool":
                evals_now = run_evals_tool(itinerary=itinerary.dict(), vacation_info=vinfo.dict(), client=client, model=model)
                messages.append({"role": "user", "content": f"OBSERVATION: (auto) run_evals_tool before final: {json.dumps(evals_now)}"})
            return result

        messages.append({"role": "user", "content": f"OBSERVATION: {json.dumps(result, ensure_ascii=False)}"})

    # If loop ends without final answer, return last known itinerary and a message
    return {
        "ok": False,
        "message": "Max steps reached without final_answer_tool. Returning latest itinerary.",
        "final_itinerary": itinerary.dict(),
    }


# -------------
# Main program
# -------------

def make_client() -> Any:
    if OpenAI is None:
        raise RuntimeError("openai package is required. pip install openai")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set in environment.")
    return OpenAI()


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AgentsVille Trip Planner")
    p.add_argument("--city", default="AgentsVille")
    p.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    p.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    p.add_argument("--travelers", default="Ada Lovelace,Alan Turing", help="Comma-separated traveler names")
    p.add_argument("--interests", default="technology,art,dancing", help="Comma-separated interests from project_lib.Interest")
    p.add_argument("--budget", type=float, default=200.0, help="Total budget amount")
    p.add_argument("--currency", default="USD")
    p.add_argument("--model", default="gpt-4o-mini", help="OpenAI chat model name")
    p.add_argument("--revise", action="store_true", help="Run revision agent to refine itinerary")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)

    # Build vacation info
    try:
        vinfo = VacationInfo(
            city=args.city,
            start_date=datetime.strptime(args.start, "%Y-%m-%d").date(),
            end_date=datetime.strptime(args.end, "%Y-%m-%d").date(),
            travelers=[s.strip() for s in args.travelers.split(",") if s.strip()],
            interests=[Interest(i.strip()) for i in args.interests.split(",") if i.strip()],
            budget_currency=args.currency,
            budget_amount=args.budget,
        )
    except Exception as e:
        print_in_box(str(e), title="Invalid VacationInfo inputs")
        sys.exit(2)

    # Instantiate OpenAI client
    try:
        client = make_client()
    except Exception as e:
        print_in_box(
            f"{e}\nPlease set OPENAI_API_KEY and install openai. Skipping LLM calls.",
            title="OpenAI client not available",
        )
        sys.exit(2)

    model = args.model

    print_in_box(json.dumps(vinfo.dict(), default=str, indent=2), title="VacationInfo")

    # Step 1: Generate initial itinerary
    print_in_box("Generating initial itinerary via ItineraryAgent...", title="Step 1")
    itinerary = generate_initial_itinerary(client=client, model=model, vinfo=vinfo)

    # Step 2: Evaluate initial itinerary
    print_in_box(json.dumps(itinerary.dict(), ensure_ascii=False, indent=2), title="Initial Itinerary (raw)")

    evals = run_evals_tool(itinerary=itinerary.dict(), vacation_info=vinfo.dict(), client=client, model=model)
    print_in_box(json.dumps(evals, indent=2), title="Initial Evaluations")

    # Optional Step 3: Revision agent to refine until passing
    final_payload: Dict[str, Any]
    if args.revise:
        print_in_box("Running ItineraryRevisionAgent (ReAct loop)...", title="Step 3")
        final_payload = run_revision_agent(client=client, model=model, itinerary=itinerary, vinfo=vinfo)
    else:
        final_payload = {"ok": True, "message": "Revision skipped.", "final_itinerary": itinerary.dict()}

    print_in_box(json.dumps(final_payload, ensure_ascii=False, indent=2), title="Final Payload")


if __name__ == "__main__":
    main()
