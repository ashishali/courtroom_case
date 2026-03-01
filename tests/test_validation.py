"""
Minimal validation: case JSON schema and scoring logic.
Run from project root: python tests/test_validation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow importing game package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game.models import Case, Verdict
from game.scoring import (
    compute_defense_undermining,
    compute_evidence_coverage,
    compute_chain_bonus,
    critical_gate_passed,
    compute_final_score,
    get_verdict,
)


def load_case_from_repo() -> Case:
    path = Path(__file__).resolve().parent.parent / "cases" / "pen_stolen_case.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return Case.from_dict(data)


def test_case_schema() -> None:
    """Validate sample case has required fields and consistent IDs."""
    case = load_case_from_repo()
    assert case.title
    assert case.scenario_intro
    assert len(case.characters) >= 1
    assert len(case.evidence) >= 1
    assert case.critical_evidence_ids
    evidence_ids = {e.id for e in case.evidence}
    for eid in case.critical_evidence_ids:
        assert eid in evidence_ids, f"Critical evidence {eid} not in evidence list"
    for chain_ids in case.chains.values():
        for eid in chain_ids:
            assert eid in evidence_ids, f"Chain references unknown evidence {eid}"
    for c in case.characters:
        for eid in c.knows:
            assert eid in evidence_ids, f"Character {c.name} knows unknown evidence {eid}"
    print("Case schema: OK")


def test_scoring_deterministic() -> None:
    """Test scoring and verdict thresholds."""
    case = load_case_from_repo()
    discovered = {"E1", "E2", "E3", "E4", "E5"}
    presented = ["E1", "E2", "E3", "E4"]
    attacks: list[dict[str, str]] = []

    cov = compute_evidence_coverage(case, discovered, presented)
    assert cov == 3 + 2 + 4 + 3, "Evidence coverage = E1+E2+E3+E4 weights"
    bonus = compute_chain_bonus(case, discovered, presented)
    assert bonus >= 0
    under = compute_defense_undermining(case, presented, attacks)
    assert under == 0

    verdict, score = get_verdict(case, discovered, presented, attacks)
    assert critical_gate_passed(case, discovered, presented) is True
    assert score >= 12, "Full critical + good evidence => score >= 12"
    assert verdict == Verdict.GUILTY

    # Missing critical => Not Guilty
    presented_bad = ["E2", "E4"]
    verdict2, _ = get_verdict(case, discovered, presented_bad, [])
    assert verdict2 == Verdict.NOT_GUILTY

    # Defense undermining: valid attack on E1
    attacks2 = [{"evidence_id": "E1", "tag": "inconsistent_witness"}]
    under2 = compute_defense_undermining(case, ["E1", "E3"], attacks2)
    assert under2 == 1.0
    score2 = compute_final_score(case, discovered, ["E1", "E3"], attacks2)
    assert score2 == (3 + 4) + 0 - 1  # coverage + chain - undermine

    print("Scoring logic: OK")


def main() -> None:
    test_case_schema()
    test_scoring_deterministic()
    print("All validation passed.")


if __name__ == "__main__":
    main()
