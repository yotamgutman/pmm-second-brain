"""
CLI for exercising the PMM agent tools without the Streamlit UI.

Examples:
    python -m agent.cli battle-card OpsChain
    python -m agent.cli battle-card Routely
    python -m agent.cli release-note
    python -m agent.cli comparison-table
    python -m agent.cli customer-story "Brightline Logistics"
    python -m agent.cli customer-story "Hearth & Co."
    python -m agent.cli drift-check

By default this uses LLM_PROVIDER from your .env (anthropic). Pass
--mock to force the dependency-free mock provider, useful for a quick
end-to-end check with no API key.
"""

import argparse
import os

from dotenv import load_dotenv

from agent import render, tools

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="PMM agent tool runner")
    parser.add_argument(
        "command",
        choices=[
            "battle-card",
            "release-note",
            "comparison-table",
            "customer-story",
            "drift-check",
        ],
    )
    parser.add_argument("argument", nargs="?", help="Competitor or customer name, if required")
    parser.add_argument("--mock", action="store_true", help="Force LLM_PROVIDER=mock for this run")
    args = parser.parse_args()

    if args.mock:
        os.environ["LLM_PROVIDER"] = "mock"

    if args.command == "battle-card":
        if not args.argument:
            parser.error("battle-card requires a competitor name (OpsChain or Routely)")
        data = tools.generate_battle_card(args.argument)
        print(render.render_battle_card(data))

    elif args.command == "release-note":
        data = tools.draft_release_note(args.argument or "AutoSync")
        print(render.render_release_note(data))

    elif args.command == "comparison-table":
        data = tools.generate_comparison_table()
        print(render.render_comparison_table(data))

    elif args.command == "customer-story":
        if not args.argument:
            parser.error("customer-story requires a customer name (Brightline Logistics or Hearth & Co.)")
        data = tools.generate_customer_story(args.argument)
        print(render.render_customer_story(data))

    elif args.command == "drift-check":
        data = tools.check_messaging_drift()
        print(render.render_drift_report(data))


if __name__ == "__main__":
    main()
