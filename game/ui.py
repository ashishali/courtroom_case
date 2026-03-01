"""CLI rendering and input helpers for Courtroom Quest."""

from __future__ import annotations

from game.models import GameState, Phase

# Decoration line patterns (ASCII, work in any terminal)
_LINE = 58
_PATTERN = "= * " * 15  # repeat to fill width
_BAR = "=" * _LINE


def print_welcome_banner() -> None:
    """Show at app start, right after running python3 main.py."""
    print()
    print(_BAR)
    print("    C O U R T R O O M   Q U E S T")
    print("    Investigate  ·  Present  ·  Verdict")
    print(_BAR)
    print(_PATTERN[: _LINE])
    print()


def print_case_start_banner(case_title: str) -> None:
    """Show at the beginning of a case (after choosing or loading)."""
    print()
    print(_PATTERN[: _LINE])
    print(_BAR)
    print("  CASE OPENED:  " + case_title)
    print(_BAR)
    print(_PATTERN[: _LINE])
    print()


def print_goodbye_banner() -> None:
    """Show when user quits or when the case ends."""
    print()
    print(_PATTERN[: _LINE])
    print(_BAR)
    print("    Thanks for playing.  Case closed.")
    print(_BAR)
    print()


def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def print_phase_banner(
    phase: Phase,
    questions_remaining: int | None = None,
    points: int | None = None,
) -> None:
    if phase == Phase.INVESTIGATION:
        q = f" (questions left: {questions_remaining})" if questions_remaining is not None else ""
        pts = f"  Points: {points}" if points is not None else ""
        print(f"\n--- Investigation{q}{pts} ---\n")
    elif phase == Phase.COURTROOM:
        print("\n--- Courtroom ---\n")
    elif phase == Phase.ENDED:
        print("\n--- Case closed ---\n")


def print_help_investigation() -> None:
    print("Commands:")
    print("  talk <character_name>   Start or continue questioning this character")
    print("  ask <question>         Ask the active character a question (uses 1 question)")
    print("  notes                  Show discovered evidence summaries")
    print("  evidence               List discovered evidence IDs and descriptions")
    print("  hints                  What evidence to look for (story clues, no spoilers)")
    print("  clues                  Exact instructions: who to ask and what to ask (-5 pts per clue)")
    print("  accuse <suspect_name>  Accuse someone (risky; may end game)")
    print("  trial                  Go to trial (when ready)")
    print("  help                   Show this help")
    print("  quit                   Exit the game")
    print("\nExamples:")
    print("  talk Sam")
    print("  ask Where were you at 5 PM?")
    print("  hints   (what to look for)")
    print("  clues   (who to ask and what to ask; costs 5 pts per clue)")
    print("  evidence")
    print()


def print_help_courtroom() -> None:
    print("You are in the courtroom. Follow the prompts for:")
    print("  Opening statement, evidence selection, closing statement.")
    print("  quit  to exit.")
    print()


def print_character_list(state: GameState) -> None:
    if not state.case:
        return
    names = [c.name for c in state.case.characters]
    print("Characters:", ", ".join(names))
    print()


def print_notes(state: GameState) -> None:
    if not state.case:
        return
    if not state.discovered_evidence_ids:
        print("No evidence discovered yet.")
        print()
        return
    print("Discovered evidence (summaries):")
    for eid in sorted(state.discovered_evidence_ids):
        ev = state.case.get_evidence(eid)
        if ev:
            print(f"  [{eid}] {ev.description[:80]}{'...' if len(ev.description) > 80 else ''}")
    print()


def print_evidence_full(state: GameState) -> None:
    if not state.case:
        return
    if not state.discovered_evidence_ids:
        print("No evidence discovered yet.")
        print()
        return
    print("Discovered evidence (IDs and full descriptions):")
    for eid in sorted(state.discovered_evidence_ids):
        ev = state.case.get_evidence(eid)
        if ev:
            print(f"  {eid}: {ev.description}")
    print()


def print_hints(state: GameState) -> None:
    """Show evidence hints in story language only: what to look for, no codes."""
    if not state.case:
        return
    case = state.case
    total = len(case.evidence)
    found_ids = state.discovered_evidence_ids
    critical_ids = set(case.critical_evidence_ids)
    missing_critical_ids = [eid for eid in case.critical_evidence_ids if eid not in found_ids]

    print("--- Evidence hints ---")
    if case.hints_intro:
        print(f"  {case.hints_intro}")
        print()
    print(f"  There are {total} pieces of evidence to find in this case.")
    print()
    print("  Evidence you can look for:")
    for ev in case.evidence:
        line = f"    • {ev.hint_or_short_description()}"
        if ev.critical:
            line += " (essential for a Guilty verdict)"
        print(line)
    print()
    print(f"  You have found {len(found_ids)} so far.")
    if found_ids:
        for eid in sorted(found_ids):
            ev = case.get_evidence(eid)
            if ev:
                print(f"    • {ev.hint_or_short_description()}")
    else:
        print("    (None yet. Talk to everyone and ask about times, who was where, and what they saw.)")
    print()
    if missing_critical_ids:
        print("  Still missing (essential for the case):")
        for eid in missing_critical_ids:
            ev = case.get_evidence(eid)
            if ev:
                print(f"    • {ev.hint_or_short_description()}")
    else:
        print("  You have found all evidence that is essential for a Guilty verdict.")
    print()


def print_clues(state: GameState) -> list[str]:
    """Show clue instructions (who to ask, what to ask) for each evidence. Returns list of evidence IDs shown (each costs 5 pts when first viewed)."""
    if not state.case:
        return []
    case = state.case
    shown: list[str] = []
    print("--- Clues (exact instructions; viewing costs 5 points per clue) ---")
    for ev in case.evidence:
        if not ev.clue_instruction:
            continue
        shown.append(ev.id)
        print(f"  To get: {ev.hint_or_short_description()}")
        print(f"    → {ev.clue_instruction}")
    if not shown:
        print("  (No clues defined for this case.)")
    print()
    return shown


def print_verdict(verdict: str, score: float, explanation: str) -> None:
    print("\n" + "=" * 60)
    print(f"  VERDICT: {verdict}")
    print(f"  Score: {score}")
    print("=" * 60)
    print("\nJudge's explanation:")
    print(explanation)
    print()
