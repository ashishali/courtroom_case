"""Deterministic scoring and verdict for the courtroom phase."""

from __future__ import annotations

from game.models import Case, Verdict


# Thresholds (as specified)
VERDICT_GUILTY_THRESHOLD = 12
VERDICT_MISTRIAL_MIN = 8
MAX_DEFENSE_UNDERMINING = 5
CHAIN_BONUS = 3


def compute_evidence_coverage(
    case: Case,
    discovered_evidence_ids: set[str],
    presented_evidence_ids: list[str],
) -> float:
    """Sum weights of presented evidence that was discovered by the player."""
    total = 0.0
    for eid in presented_evidence_ids:
        if eid not in discovered_evidence_ids:
            continue
        ev = case.get_evidence(eid)
        if ev:
            total += ev.weight
    return total


def compute_chain_bonus(
    case: Case,
    discovered_evidence_ids: set[str],
    presented_evidence_ids: list[str],
) -> float:
    """+3 per chain where all evidence in the chain was presented and discovered."""
    bonus = 0.0
    presented_set = set(presented_evidence_ids)
    for chain_name, chain_ids in case.chains.items():
        if not chain_ids:
            continue
        if all(
            eid in discovered_evidence_ids and eid in presented_set
            for eid in chain_ids
        ):
            bonus += CHAIN_BONUS
    return bonus


def compute_defense_undermining(
    case: Case,
    presented_evidence_ids: list[str],
    attacks: list[dict[str, str]],
) -> float:
    """
    Defense can reduce score by up to -5. Each valid attack (evidence_id + tag
    matching that evidence's vulnerabilities) counts. Cap total reduction at 5.
    """
    reduction = 0.0
    # Per evidence, one successful attack counts (e.g. -1 each, cap total -5)
    used_evidence: set[str] = set()
    for a in attacks:
        eid = (a.get("evidence_id") or "").strip()
        tag = (a.get("tag") or "").strip().lower()
        if not eid or not tag:
            continue
        if eid not in presented_evidence_ids:
            continue
        if eid in used_evidence:
            continue
        ev = case.get_evidence(eid)
        if not ev:
            continue
        vulns = [v.lower() for v in ev.vulnerabilities]
        if tag in vulns:
            used_evidence.add(eid)
            reduction += 1.0
            if reduction >= MAX_DEFENSE_UNDERMINING:
                break
    return min(reduction, MAX_DEFENSE_UNDERMINING)


def critical_gate_passed(
    case: Case,
    discovered_evidence_ids: set[str],
    presented_evidence_ids: list[str],
) -> bool:
    """True iff all critical evidence was discovered AND presented."""
    presented_set = set(presented_evidence_ids)
    for eid in case.critical_evidence_ids:
        if eid not in discovered_evidence_ids:
            return False
        if eid not in presented_set:
            return False
    return True


def compute_final_score(
    case: Case,
    discovered_evidence_ids: set[str],
    presented_evidence_ids: list[str],
    defense_attacks: list[dict[str, str]],
) -> float:
    """
    Final score = evidence coverage + chain bonus - defense undermining.
    """
    coverage = compute_evidence_coverage(
        case, discovered_evidence_ids, presented_evidence_ids
    )
    chain_bonus = compute_chain_bonus(
        case, discovered_evidence_ids, presented_evidence_ids
    )
    undermining = compute_defense_undermining(
        case, presented_evidence_ids, defense_attacks
    )
    return coverage + chain_bonus - undermining


def get_verdict(
    case: Case,
    discovered_evidence_ids: set[str],
    presented_evidence_ids: list[str],
    defense_attacks: list[dict[str, str]],
) -> tuple[Verdict, float]:
    """
    Returns (verdict, final_score). Verdict is determined ONLY by:
    - If critical gate fails => Not Guilty
    - Else if score >= 12 => Guilty
    - Else if 8 <= score < 12 => Mistrial
    - Else => Not Guilty
    """
    score = compute_final_score(
        case, discovered_evidence_ids, presented_evidence_ids, defense_attacks
    )
    if not critical_gate_passed(case, discovered_evidence_ids, presented_evidence_ids):
        return (Verdict.NOT_GUILTY, score)
    if score >= VERDICT_GUILTY_THRESHOLD:
        return (Verdict.GUILTY, score)
    if VERDICT_MISTRIAL_MIN <= score < VERDICT_GUILTY_THRESHOLD:
        return (Verdict.MISTRIAL, score)
    return (Verdict.NOT_GUILTY, score)
