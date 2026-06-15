"""
Render the structured dicts returned by agent.tools into markdown for
display in the Streamlit app (or anywhere else).
"""


def _sources_footer(data: dict) -> str:
    sources = data.get("sources") or []
    if not sources:
        return ""
    listed = ", ".join(f"`{s}`" for s in sources)
    return f"\n\n---\n**Sources:** {listed}"


def render_battle_card(data: dict) -> str:
    lines = [f"# Battle Card: {data['competitor']}", "", "## Positioning", data["positioning_summary"], ""]

    lines.append("## Objections & Counters")
    for obj in data["objections"]:
        lines.append(f"**Objection:** {obj['objection']}")
        lines.append(f"**Counter:** {obj['counter']}")
        lines.append(f"**Proof point:** {obj['proof_point']}")
        lines.append("")

    lines.append("## Win Themes")
    for theme in data["win_themes"]:
        lines.append(f"- {theme}")

    return "\n".join(lines) + _sources_footer(data)


def render_release_note(data: dict) -> str:
    lines = [f"# {data['headline']}", "", data["summary"], "", "## What's New"]
    for detail in data["details"]:
        lines.append(f"- {detail}")

    limitations = data.get("known_limitations") or []
    if limitations:
        lines += ["", "## Known Limitations"]
        for item in limitations:
            lines.append(f"- {item}")

    return "\n".join(lines) + _sources_footer(data)


def render_comparison_table(data: dict) -> str:
    rows = data["rows"]
    header = "| Dimension | FlowPilot | OpsChain | Routely |"
    divider = "|---|---|---|---|"
    body = [
        f"| {r['dimension']} | {r['flowpilot']} | {r['opschain']} | {r['routely']} |"
        for r in rows
    ]
    table = "\n".join([header, divider] + body)
    return f"# FlowPilot vs. OpsChain vs. Routely\n\n{table}" + _sources_footer(data)


def render_customer_story(data: dict) -> str:
    lines = [
        f"# {data['headline']}",
        "",
        "*Draft for human review — verify quote and details before publishing.*",
        "",
        "## Challenge",
        data["challenge"],
        "",
        "## Solution",
        data["solution"],
        "",
        "## Result",
        data["result"],
        "",
        "## Customer Quote",
        f"> {data['quote']}",
    ]
    return "\n".join(lines) + _sources_footer(data)


def render_drift_report(data: dict) -> str:
    flags = data.get("flags") or []
    if not flags:
        return "# Messaging Drift Check\n\nNo drift detected — external messaging matches internal reality." + _sources_footer(data)

    severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}

    lines = ["# Messaging Drift Check", "", f"Found **{len(flags)}** potential mismatch(es) between external messaging and internal reality.", ""]
    for flag in flags:
        emoji = severity_emoji.get(flag.get("severity", "").lower(), "•")
        lines.append(f"## {emoji} {flag['severity'].title()} severity")
        lines.append(f"**External claim:** {flag['external_claim']}")
        lines.append(f"**Internal reality:** {flag['internal_reality']}")
        lines.append(f"**Source:** `{flag['source']}`")
        lines.append("")

    return "\n".join(lines) + _sources_footer(data)


def render_qa_result(data: dict) -> str:
    if data.get("answer") is None:
        # Mock mode: an arbitrary question can't be matched to a canned
        # answer, so show the raw retrieved context instead.
        lines = [
            "*Demo mode (`LLM_PROVIDER=mock`): showing the raw retrieved "
            "context below instead of a synthesized answer. Set "
            "`LLM_PROVIDER=anthropic` with an API key for a generated answer.*",
            "",
        ]
        for c in data.get("context_chunks", []):
            lines.append(f"**{c['source']} — {c['heading']}**")
            lines.append(c["text"])
            lines.append("")
        return "\n".join(lines)

    return data["answer"] + _sources_footer(data)
