"""Dataclasses and types for Courtroom Quest."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Phase(str, Enum):
    INVESTIGATION = "investigation"
    COURTROOM = "courtroom"
    ENDED = "ended"


class Verdict(str, Enum):
    GUILTY = "Guilty"
    NOT_GUILTY = "Not Guilty"
    MISTRIAL = "Mistrial"


@dataclass
class RevealConditions:
    required_characters_talked_to: list[str] = field(default_factory=list)
    required_evidence_ids_found: list[str] = field(default_factory=list)
    min_questions_asked_to_that_character: int = 0
    keywords: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> RevealConditions:
        if not d:
            return cls()
        return cls(
            required_characters_talked_to=d.get("required_characters_talked_to", []),
            required_evidence_ids_found=d.get("required_evidence_ids_found", []),
            min_questions_asked_to_that_character=d.get("min_questions_asked_to_that_character", 0),
            keywords=d.get("keywords", []),
        )


# Points: +10 per evidence discovered, -5 per clue viewed. Spent at trial to cancel defense attacks.
POINTS_PER_EVIDENCE = 10
POINTS_PER_CLUE = 5  # deducted when a clue is viewed
POINTS_PER_ATTACK_CANCEL = 15


@dataclass
class Evidence:
    id: str
    type: str
    description: str
    hint: str  # narrative clue for hints (story language, no codes)
    clue_instruction: str  # exact instruction: who to ask and what to ask (costs 5 pts when viewed)
    weight: int
    critical: bool
    vulnerabilities: list[str]
    reveal_conditions: RevealConditions

    def hint_or_short_description(self, max_len: int = 72) -> str:
        """Text to show in hints: prefer hint, else shortened description."""
        if self.hint.strip():
            return self.hint.strip()
        if len(self.description) <= max_len:
            return self.description
        return self.description[: max_len - 3].rsplit(" ", 1)[0] + "..."

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Evidence:
        return cls(
            id=d["id"],
            type=d.get("type", "physical"),
            description=d["description"],
            hint=str(d.get("hint", "")).strip(),
            clue_instruction=str(d.get("clue_instruction", "")).strip(),
            weight=int(d.get("weight", 1)),
            critical=bool(d.get("critical", False)),
            vulnerabilities=list(d.get("vulnerabilities", [])),
            reveal_conditions=RevealConditions.from_dict(d.get("reveal_conditions")),
        )


@dataclass
class Character:
    name: str
    role: str
    persona: str
    knows: list[str]
    liar: bool
    lie_strategy: str
    facts: list[str]  # Canonical facts (times, events) this character must use when answering; no inventing

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Character:
        return cls(
            name=d["name"],
            role=d.get("role", "witness"),
            persona=d.get("persona", ""),
            knows=list(d.get("knows", [])),
            liar=bool(d.get("liar", False)),
            lie_strategy=d.get("lie_strategy", ""),
            facts=list(d.get("facts", [])),
        )


@dataclass
class RevealRules:
    max_evidence_per_answer: int = 1
    question_budget: int = 20
    max_evidence_presentation: int = 5

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> RevealRules:
        if not d:
            return cls()
        return cls(
            max_evidence_per_answer=int(d.get("max_evidence_per_answer", 1)),
            question_budget=int(d.get("question_budget", 20)),
            max_evidence_presentation=int(d.get("max_evidence_presentation", 5)),
        )


@dataclass
class Case:
    title: str
    scenario_intro: str
    hints_intro: str  # narrative summary for hints (story-aligned)
    characters: list[Character]
    suspects: list[str]
    truth: dict[str, Any]
    evidence: list[Evidence]
    chains: dict[str, list[str]]
    reveal_rules: RevealRules
    critical_evidence_ids: list[str]

    def get_character(self, name: str) -> Character | None:
        for c in self.characters:
            if c.name.lower() == name.lower():
                return c
        return None

    def get_evidence(self, eid: str) -> Evidence | None:
        for e in self.evidence:
            if e.id == eid:
                return e
        return None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Case:
        return cls(
            title=d["title"],
            scenario_intro=d["scenario_intro"],
            hints_intro=str(d.get("hints_intro", "")).strip(),
            characters=[Character.from_dict(c) for c in d["characters"]],
            suspects=list(d.get("suspects", [])),
            truth=dict(d.get("truth", {})),
            evidence=[Evidence.from_dict(e) for e in d["evidence"]],
            chains={k: list(v) for k, v in d.get("chains", {}).items()},
            reveal_rules=RevealRules.from_dict(d.get("reveal_rules")),
            critical_evidence_ids=list(d.get("critical_evidence_ids", [])),
        )


@dataclass
class GameState:
    phase: Phase = Phase.INVESTIGATION
    case: Case | None = None
    discovered_evidence_ids: set[str] = field(default_factory=set)
    questions_remaining: int = 20
    questions_asked_per_character: dict[str, int] = field(default_factory=dict)
    characters_talked_to: set[str] = field(default_factory=set)
    active_character: str | None = None
    conversation_history: list[tuple[str, str]] = field(default_factory=list)
    presented_evidence_ids: list[str] = field(default_factory=list)
    defense_attacks: list[dict[str, str]] = field(default_factory=list)
    clues_viewed: set[str] = field(default_factory=set)  # evidence ids whose clue was viewed (-5 pts each)
    trial_points: int = 0  # set when going to trial: max(0, 10*evidence - 5*clues_viewed)
    final_score: float = 0.0
    verdict: Verdict | None = None
    judge_explanation: str = ""
    dry_run: bool = False
