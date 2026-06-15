"""
LLM client wrapper — a provider-agnostic JSON-completion interface for the
agent tools.

Set LLM_PROVIDER in .env:

  anthropic (default) — requires ANTHROPIC_API_KEY. Uses Claude Sonnet.
  openai              — requires OPENAI_API_KEY. Lazy-imports the openai
                         package (not in requirements.txt by default).
  mock                — returns canned, hand-written JSON responses.
                         No API key, no network call. This is what powers
                         the "demo mode" of the Streamlit app and the
                         test suite: every tool's retrieval + prompt +
                         rendering pipeline runs end-to-end, only the
                         final generation step is replaced with a fixture.
"""

import json
import os

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Mock responses — hand-written, grounded in vault content. Used when
# LLM_PROVIDER=mock so the app/tests run with zero API keys.
# ---------------------------------------------------------------------------
MOCK_RESPONSES = {
    "battle_card_opschain": {
        "competitor": "OpsChain",
        "positioning_summary": (
            "OpsChain competes on compliance and governance, not ease of use. "
            "FlowPilot wins on setup speed and UI simplicity, but currently lacks "
            "the audit log and field-level permissions OpsChain offers on every "
            "plan — a gap that has cost real deals with compliance-sensitive "
            "prospects."
        ),
        "objections": [
            {
                "objection": "OpsChain has a full audit log and granular, field-level permissions built in.",
                "counter": (
                    "FlowPilot's Audit Log is on the near-term roadmap. For "
                    "prospects without strict compliance requirements, FlowPilot's "
                    "faster setup and simpler admin experience outweigh this gap."
                ),
                "proof_point": (
                    "Two recent enterprise losses (Meridian Health Group, Carrow "
                    "Industrial) cited audit log / SOC 2 Type II as the deciding "
                    "factor — not price or usability."
                ),
            },
            {
                "objection": "OpsChain is the safer, more 'enterprise-grade' choice for a larger org.",
                "counter": (
                    "OpsChain's implementation typically takes 6-8 weeks and often "
                    "requires a dedicated solutions engineer, versus FlowPilot's "
                    "self-serve setup. For most mid-market teams, that overhead "
                    "outweighs compliance features they don't yet need."
                ),
                "proof_point": (
                    "Win/loss notes consistently cite OpsChain's implementation "
                    "time and dated UI as reasons mid-market prospects choose "
                    "FlowPilot instead."
                ),
            },
        ],
        "win_themes": [
            "Setup speed and ease of use vs. OpsChain's 6-8 week implementation",
            "Lower total cost for teams without hard compliance requirements",
        ],
    },
    "battle_card_routely": {
        "competitor": "Routely",
        "positioning_summary": (
            "Routely competes on price and simplicity for very small teams, but "
            "its lack of integrations forces customers into the same manual CSV "
            "workflows FlowPilot eliminated with AutoSync. FlowPilot now has a "
            "clear, concrete advantage for any team that has outgrown "
            "spreadsheet-based data syncing."
        ),
        "objections": [
            {
                "objection": "Routely is cheaper and faster to set up.",
                "counter": (
                    "Routely's low price comes with no native integrations — all "
                    "data movement is manual CSV export/import. AutoSync gives "
                    "FlowPilot customers automated, 15-minute sync to Salesforce, "
                    "HubSpot, and NetSuite, directly removing a recurring weekly task."
                ),
                "proof_point": (
                    "Hearth & Co. switched from Routely to FlowPilot specifically "
                    "because of AutoSync, after spending hours per week reconciling "
                    "CRM data manually on Routely."
                ),
            },
            {
                "objection": "Our team is small and doesn't need advanced permissions.",
                "counter": (
                    "That may be true today, but Routely's all-or-nothing "
                    "permissions model becomes a real constraint as teams grow. "
                    "FlowPilot supports more structured access without the jump to "
                    "OpsChain's complexity."
                ),
                "proof_point": (
                    "No FlowPilot win/loss data currently cites this as a blocker — "
                    "a natural growth-stage conversation to raise proactively."
                ),
            },
        ],
        "win_themes": [
            "AutoSync directly replaces Routely's manual CSV-only workflow",
            "Better fit for teams that have outgrown 'set up in an afternoon' simplicity",
        ],
    },
    "release_note_autosync": {
        "feature_name": "AutoSync",
        "headline": "AutoSync: automatic data sync with Salesforce, HubSpot, and NetSuite",
        "summary": (
            "AutoSync replaces manual CSV export/import with continuous, "
            "automated synchronization between FlowPilot and the tools your "
            "team already uses. Available now on all Business and Enterprise plans."
        ),
        "details": [
            "Syncs data every 15 minutes across Salesforce, HubSpot, and NetSuite",
            "One-time OAuth connection per integration — no CSV mapping required",
            "Conflict resolution via most-recent-write-wins, with a full sync log in the admin panel",
            "Available now on all Business and Enterprise workspaces",
        ],
        "known_limitations": [
            "A rare duplicate-entry issue can occur with NetSuite during very "
            "high-volume sync windows (e.g., end-of-month batch updates). A fix "
            "is targeted for an upcoming sprint.",
        ],
    },
    "comparison_table": {
        "rows": [
            {
                "dimension": "Data sync & integrations",
                "flowpilot": "Automated sync (AutoSync) every 15 min — Salesforce, HubSpot, NetSuite",
                "opschain": "Native integrations, setup via solutions engineer",
                "routely": "Manual CSV export/import only",
            },
            {
                "dimension": "Audit log & compliance",
                "flowpilot": "Not yet available (on roadmap)",
                "opschain": "Full audit log on all plans, SOC 2 Type II",
                "routely": "No audit log or activity history",
            },
            {
                "dimension": "Permissions",
                "flowpilot": "Role-based, workspace level",
                "opschain": "Granular, field-level permissions",
                "routely": "All-or-nothing (admin vs. everyone)",
            },
            {
                "dimension": "Setup time",
                "flowpilot": "Self-serve, same day",
                "opschain": "6-8 weeks, often with a solutions engineer",
                "routely": "Same day",
            },
            {
                "dimension": "Best fit",
                "flowpilot": "Mid-market ops teams outgrowing manual workflows",
                "opschain": "Regulated industries with strict compliance needs",
                "routely": "Very small teams with simple workflows",
            },
        ],
    },
    "customer_story_brightline-logistics": {
        "customer_name": "Brightline Logistics",
        "headline": "How Brightline Logistics eliminated weekly manual data exports with AutoSync",
        "challenge": (
            "Brightline's operations team spent roughly 45 minutes every week "
            "manually exporting data from Salesforce, reformatting it, and "
            "importing it into FlowPilot to keep approval data in sync with "
            "their CRM — an easy step to forget, which led to data drift when missed."
        ),
        "solution": (
            "Brightline joined the AutoSync beta, which automatically syncs data "
            "between FlowPilot and Salesforce every 15 minutes, removing the "
            "manual export/import step entirely."
        ),
        "result": (
            "With their main pain point resolved, Brightline expanded from a "
            "pilot to a full rollout, and the team is now discussing extending "
            "FlowPilot to their warehouse operations group."
        ),
        "quote": (
            "If that ships, it removes basically my only complaint about the "
            "tool. — Marcus Webb, Operations Manager"
        ),
    },
    "customer_story_hearth-and-co": {
        "customer_name": "Hearth & Co.",
        "headline": "Hearth & Co. saves hours a week after switching from manual CSV workflows to AutoSync",
        "challenge": (
            "As a former Routely customer, Hearth & Co.'s operations team relied "
            "entirely on manual CSV exports and imports to move data between "
            "systems, consuming significant time every week."
        ),
        "solution": (
            "After switching to FlowPilot, Hearth & Co. turned on AutoSync, which "
            "automatically syncs their data with NetSuite and other connected "
            "systems every 15 minutes."
        ),
        "result": (
            "The team no longer spends Friday afternoons reconciling "
            "spreadsheets, and the time savings have made a strong enough "
            "internal case to consider expanding FlowPilot seats to the finance "
            "team. A minor NetSuite sync edge case during a high-volume batch was "
            "identified and is being addressed."
        ),
        "quote": (
            "Genuinely a game-changer for us... our team isn't spending Friday "
            "afternoons reconciling spreadsheets anymore. — Jordan Lee, "
            "Operations Director"
        ),
    },
    "drift_check": {
        "flags": [
            {
                "external_claim": (
                    "Keeping your data in sync is simple: export your data from "
                    "FlowPilot as a CSV file, then import it into your other tools "
                    "whenever you need an update."
                ),
                "internal_reality": (
                    "AutoSync shipped on May 26, 2026 and automatically syncs data "
                    "with Salesforce, HubSpot, and NetSuite every 15 minutes — "
                    "manual CSV export/import is no longer the primary sync method "
                    "for Business and Enterprise customers."
                ),
                "source": "product/autosync-spec.md",
                "severity": "high",
            },
            {
                "external_claim": "Full control over when and how your data moves between systems.",
                "internal_reality": (
                    "With AutoSync, sync timing is automated on a 15-minute "
                    "interval rather than fully manual; the 'full control' framing "
                    "is outdated for customers on AutoSync."
                ),
                "source": "product/autosync-spec.md",
                "severity": "medium",
            },
        ],
    },
}


def complete_json(system_prompt: str, user_prompt: str, mock_key: str | None = None) -> dict:
    """Send a prompt requesting a JSON response, return the parsed dict."""
    provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()

    if provider == "mock":
        if mock_key not in MOCK_RESPONSES:
            raise ValueError(f"No mock response registered for '{mock_key}'")
        return MOCK_RESPONSES[mock_key]

    raw_text = _call_llm(provider, system_prompt, user_prompt)
    return _parse_json(raw_text)


def _call_llm(provider: str, system_prompt: str, user_prompt: str) -> str:
    if provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")

    if provider == "openai":
        from openai import OpenAI  # optional dependency

        client = OpenAI()  # reads OPENAI_API_KEY from env
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content

    raise ValueError(f"Unknown LLM_PROVIDER: '{provider}' (expected anthropic | openai | mock)")


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return json.loads(text.strip())
