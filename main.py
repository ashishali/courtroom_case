#!/usr/bin/env python3
"""
Courtroom Quest - CLI game. Investigation + Courtroom phases.
Uses local Ollama for LLM responses. Run with:
  python main.py --case cases/pen_stolen_case.json
  python main.py --case cases/pen_stolen_case.json --dry-run
"""

from __future__ import annotations

import os
import sys
import argparse
from pathlib import Path

# Config (top of main.py / env)
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_NPC_MODEL = os.environ.get("OLLAMA_NPC_MODEL", "llama3")
OLLAMA_DEFENSE_MODEL = os.environ.get("OLLAMA_DEFENSE_MODEL", "llama3")
OLLAMA_JUDGE_MODEL = os.environ.get("OLLAMA_JUDGE_MODEL", "llama3")

# Add project root for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from game.engine import GameEngine
from game.models import Phase
from game.ui import (
    print_character_list,
    print_clues,
    print_evidence_full,
    print_goodbye_banner,
    print_header,
    print_help_courtroom,
    print_help_investigation,
    print_hints,
    print_notes,
    print_phase_banner,
    print_case_start_banner,
    print_verdict,
    print_welcome_banner,
)


def run_investigation(engine: GameEngine) -> bool:
    """Returns True if player chose to go to trial, False if quit."""
    state = engine.state
    case = engine.case

    print_case_start_banner(case.title)
    print_header(f"Courtroom Quest — {case.title}")
    print(case.scenario_intro)
    print()
    print_phase_banner(
        Phase.INVESTIGATION,
        state.questions_remaining,
        engine.get_investigation_points(),
    )
    print_character_list(state)
    print_help_investigation()

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print_goodbye_banner()
            print("Goodbye.")
            return False
        if not line:
            continue

        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()
        rest = (parts[1] if len(parts) > 1 else "").strip()

        if cmd == "quit":
            print_goodbye_banner()
            print("Goodbye.")
            return False

        if cmd == "help":
            print_help_investigation()
            continue

        if cmd == "notes":
            print_notes(state)
            continue

        if cmd == "evidence":
            print_evidence_full(state)
            continue

        if cmd == "hints":
            print_hints(state)
            continue

        if cmd == "clues":
            ids_shown = print_clues(state)
            engine.record_clues_viewed(ids_shown)
            print(f"Points: {engine.get_investigation_points()} (evidence +10 each, clues viewed -5 each)")
            continue

        if cmd == "talk":
            if not rest:
                print("Usage: talk <character_name>")
                continue
            if state.questions_remaining <= 0:
                print("No questions left. Use 'trial' to go to court or 'quit'.")
                continue
            if not engine.start_talking(rest):
                print(f"Unknown character: {rest}. Characters: {[c.name for c in case.characters]}")
                continue
            print(f"Now talking to {state.active_character}. Use 'ask <question>' to question them.")
            continue

        if cmd == "ask":
            if not state.active_character:
                print("Use 'talk <character_name>' first to choose who to question.")
                continue
            if state.questions_remaining <= 0:
                print("No questions left.")
                continue
            if not rest:
                print("Usage: ask <your question>")
                continue
            print(f"\n[{state.active_character}] ", end="")
            try:
                reply = engine.npc_reply(state.active_character, rest)
            except Exception as e:
                print(f"Error: {e}")
                continue
            print(reply)
            print_phase_banner(
                Phase.INVESTIGATION,
                state.questions_remaining,
                engine.get_investigation_points(),
            )
            continue

        if cmd == "accuse":
            if not rest:
                print("Usage: accuse <suspect_name>")
                continue
            # Optional early accuse: treat as risky; we end investigation and go to trial with no bonus
            print("You have accused someone. Proceeding to trial with current evidence.")
            engine.go_to_trial()
            return True

        if cmd == "trial":
            if not engine.can_go_to_trial():
                print("You have not found all critical evidence. Going to trial anyway (risky).")
            engine.go_to_trial()
            return True

        print(f"Unknown command: {cmd}. Type 'help' for commands.")
    return False


def run_courtroom(engine: GameEngine) -> None:
    state = engine.state
    case = engine.case

    print_header(f"Courtroom — {case.title}")
    print_phase_banner(Phase.COURTROOM)
    print(f"You have {state.trial_points} trial points (from evidence +10 each, clues -5 each).")
    print("You can spend 15 points per defense attack to cancel it after the rebuttal.\n")

    # 1) Opening statement (player)
    print("Give your opening statement (prosecution):")
    try:
        opening = input("> ").strip() or "(No opening statement.)"
    except (EOFError, KeyboardInterrupt):
        opening = "(No opening statement.)"
    print()

    # 2) Defense opening (LLM)
    print("Defense opening:")
    defense_open = engine.defense_opening()
    print(defense_open)
    print()

    # 3) Evidence presentation: player selects up to N
    max_present = case.reveal_rules.max_evidence_presentation
    discovered = sorted(state.discovered_evidence_ids)
    if not discovered:
        print("You have no evidence to present.")
    else:
        print(f"Select up to {max_present} evidence IDs to present (comma-separated, e.g. E1,E2,E3):")
        for eid in discovered:
            ev = case.get_evidence(eid)
            if ev:
                print(f"  {eid}: {ev.description[:60]}...")
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            raw = ""
        chosen = [x.strip() for x in raw.replace(",", " ").split() if x.strip()]
        engine.set_presented_evidence(chosen)
    print()

    # 4) Defense rebuttal (LLM) -> attacks parsed
    print("Defense rebuttal:")
    descs = []
    for eid in state.presented_evidence_ids:
        ev = case.get_evidence(eid)
        if ev:
            descs.append(f"{eid}: {ev.description}")
    summary, attacks = engine.defense_rebuttal(state.presented_evidence_ids)
    print(summary)
    if attacks:
        print("(Defense attacked evidence:", attacks, ")")
    print()

    # 4b) Spend trial points to cancel defense attacks (go back a level)
    num_attacks = len(state.defense_attacks)
    if num_attacks > 0 and state.trial_points > 0:
        from game.models import POINTS_PER_ATTACK_CANCEL
        max_cancel = min(num_attacks, state.trial_points // POINTS_PER_ATTACK_CANCEL)
        print(f"You have {state.trial_points} trial points. Cancel a defense attack for {POINTS_PER_ATTACK_CANCEL} points each.")
        print(f"Defense made {num_attacks} attack(s). You can cancel up to {max_cancel}.")
        try:
            raw = input(f"How many attacks to cancel? (0 to {max_cancel}) ").strip()
            n = int(raw) if raw else 0
            n = max(0, min(n, max_cancel))
        except (EOFError, ValueError, KeyboardInterrupt):
            n = 0
        if n > 0:
            cancelled = engine.spend_points_cancel_attacks(n)
            print(f"Cancelled {cancelled} attack(s). {state.trial_points} points remaining.")
    print()

    # 5) Closing: player then defense
    print("Give your closing statement (prosecution):")
    try:
        closing = input("> ").strip() or "(No closing statement.)"
    except (EOFError, KeyboardInterrupt):
        closing = "(No closing statement.)"
    print("Defense closing:")
    defense_closing = engine.defense_closing(closing)
    print(defense_closing)
    print()

    # 6) Judge decision (deterministic verdict + LLM explanation)
    prosecution_evidence_descriptions = [
        f"{eid}: {case.get_evidence(eid).description}"
        for eid in state.presented_evidence_ids
        if case.get_evidence(eid)
    ]
    verdict, score, explanation = engine.judge_decision(
        prosecution_evidence_descriptions, summary
    )
    print_verdict(verdict.value, score, explanation)
    engine.end_game()
    print_goodbye_banner()


def get_available_cases(cases_dir: Path) -> list[tuple[str, Path]]:
    """Return list of (title, path) for each case JSON in cases_dir."""
    import json
    result: list[tuple[str, Path]] = []
    for path in sorted(cases_dir.glob("*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            title = data.get("title", path.stem)
            result.append((title, path))
        except (OSError, json.JSONDecodeError):
            continue
    return result


def choose_case(cases_dir: Path) -> Path | None:
    """Show menu of cases; return selected path or None if quit."""
    cases = get_available_cases(cases_dir)
    if not cases:
        print(f"No case files found in {cases_dir}")
        return None
    print("\n  Courtroom Quest — Choose a case\n")
    for i, (title, path) in enumerate(cases, 1):
        print(f"  {i}. {title}")
    print(f"  {len(cases) + 1}. Quit")
    print()
    while True:
        try:
            raw = input("Enter number (1–{}): ".format(len(cases) + 1)).strip()
            n = int(raw)
        except (EOFError, ValueError, KeyboardInterrupt):
            return None
        if 1 <= n <= len(cases):
            return cases[n - 1][1]
        if n == len(cases) + 1:
            return None
        print("Invalid choice. Try again.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Courtroom Quest - CLI investigation and courtroom game with Ollama."
    )
    parser.add_argument(
        "--case",
        type=str,
        default=None,
        metavar="PATH",
        help="Path to case JSON file. If omitted, you will choose from a list.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not call Ollama; use stubbed responses for testing",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    cases_dir = project_root / "cases"

    print_welcome_banner()

    if args.case:
        case_path = Path(args.case)
        if not case_path.is_absolute():
            case_path = project_root / case_path
        if not case_path.is_file():
            print(f"Case file not found: {case_path}")
            sys.exit(1)
    else:
        case_path = choose_case(cases_dir)
        if case_path is None:
            print_goodbye_banner()
            print("Goodbye.")
            sys.exit(0)

    engine = GameEngine(
        case_path,
        ollama_base_url=OLLAMA_BASE_URL,
        ollama_npc_model=OLLAMA_NPC_MODEL,
        ollama_defense_model=OLLAMA_DEFENSE_MODEL,
        ollama_judge_model=OLLAMA_JUDGE_MODEL,
        dry_run=args.dry_run,
    )

    if engine.dry_run:
        print("(Dry-run mode: no Ollama calls.)\n")

    if run_investigation(engine):
        run_courtroom(engine)


if __name__ == "__main__":
    main()
