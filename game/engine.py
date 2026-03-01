"""State machine and game logic for Courtroom Quest."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from game.models import (
    Case,
    GameState,
    Phase,
    POINTS_PER_ATTACK_CANCEL,
    POINTS_PER_CLUE,
    POINTS_PER_EVIDENCE,
    Verdict,
)
from game.ollama_client import chat as ollama_chat
from game.prompts import (
    defense_closing_prompt,
    defense_opening_prompt,
    defense_rebuttal_prompt,
    judge_explanation_prompt,
    npc_system_prompt,
)
from game.scoring import get_verdict


def load_case(path: str | Path) -> Case:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return Case.from_dict(data)


def get_eligible_evidence_for_character(
    case: Case,
    character_name: str,
    state: GameState,
    question_text: str,
) -> list[str]:
    """
    Returns list of evidence IDs this character can reveal this turn, given
    reveal_conditions and that the character knows them.
    """
    char = case.get_character(character_name)
    if not char:
        return []

    eligible: list[str] = []
    for eid in char.knows:
        if eid in state.discovered_evidence_ids:
            continue
        ev = case.get_evidence(eid)
        if not ev:
            continue
        rc = ev.reveal_conditions

        if rc.required_characters_talked_to:
            if not all(
                c in state.characters_talked_to for c in rc.required_characters_talked_to
            ):
                continue
        if rc.required_evidence_ids_found:
            if not all(
                e in state.discovered_evidence_ids for e in rc.required_evidence_ids_found
            ):
                continue
        n = state.questions_asked_per_character.get(character_name, 0)
        if n < rc.min_questions_asked_to_that_character:
            continue
        if rc.keywords:
            q = (question_text or "").lower()
            if not any(kw.lower() in q for kw in rc.keywords):
                continue
        eligible.append(eid)
    return eligible


def extract_evidence_ids_from_response(text: str) -> list[str]:
    """Find bracketed evidence IDs like [E1], [E2] in NPC response."""
    if not text:
        return []
    pattern = r"\[(E\d+)\]"
    return list(dict.fromkeys(re.findall(pattern, text)))  # preserve order, no dupes


def parse_defense_rebuttal_json(response: str) -> tuple[list[dict[str, str]], str]:
    """Parse defense JSON: attacks and summary. Tolerates markdown code blocks."""
    summary = ""
    attacks: list[dict[str, str]] = []
    text = response.strip()
    # Strip optional ```json ... ```
    if "```" in text:
        start = text.find("```")
        if start != -1:
            rest = text[start + 3:]
            if rest.lower().startswith("json"):
                rest = rest[4:].lstrip()
            end = rest.find("```")
            if end != -1:
                text = rest[:end].strip()
            else:
                text = rest.strip()
    try:
        data = json.loads(text)
        attacks = list(data.get("attacks", []))
        if not isinstance(attacks, list):
            attacks = []
        else:
            attacks = [
                {"evidence_id": str(a.get("evidence_id", "")), "tag": str(a.get("tag", ""))}
                for a in attacks
                if isinstance(a, dict)
            ]
        summary = str(data.get("summary", ""))
    except json.JSONDecodeError:
        pass
    return (attacks, summary)


def parse_judge_explanation_json(response: str) -> tuple[str, list[str], str]:
    """Parse judge JSON: verdict_explanation, key_evidence_ids, score_interpretation."""
    explanation = ""
    key_ids: list[str] = []
    score_interp = ""
    text = response.strip()
    if "```" in text:
        start = text.find("```")
        if start != -1:
            rest = text[start + 3:]
            if rest.lower().startswith("json"):
                rest = rest[4:].lstrip()
            end = rest.find("```")
            if end != -1:
                text = rest[:end].strip()
            else:
                text = rest.strip()
    try:
        data = json.loads(text)
        explanation = str(data.get("verdict_explanation", ""))
        key_ids = list(data.get("key_evidence_ids", []))
        if not isinstance(key_ids, list):
            key_ids = []
        else:
            key_ids = [str(x) for x in key_ids]
        score_interp = str(data.get("score_interpretation", ""))
    except json.JSONDecodeError:
        pass
    return (explanation, key_ids, score_interp)


class GameEngine:
    def __init__(
        self,
        case_path: str | Path,
        ollama_base_url: str,
        ollama_npc_model: str,
        ollama_defense_model: str,
        ollama_judge_model: str,
        dry_run: bool = False,
    ):
        self.case = load_case(case_path)
        self.base_url = ollama_base_url
        self.npc_model = ollama_npc_model
        self.defense_model = ollama_defense_model
        self.judge_model = ollama_judge_model
        self.dry_run = dry_run
        rules = self.case.reveal_rules
        self.state = GameState(
            phase=Phase.INVESTIGATION,
            case=self.case,
            questions_remaining=rules.question_budget,
            dry_run=dry_run,
        )

    def npc_reply(
        self,
        character_name: str,
        question: str,
        chat_fn: Callable[..., str] | None = None,
    ) -> str:
        """Get NPC response; optionally reveal one eligible evidence ID."""
        char = self.case.get_character(character_name)
        if not char:
            return "I'm not here."
        eligible = get_eligible_evidence_for_character(
            self.case, character_name, self.state, question
        )
        max_ev = self.case.reveal_rules.max_evidence_per_answer
        # Limit to max_evidence_per_answer for prompt
        eligible_limited = eligible[:max_ev] if eligible else []

        system = npc_system_prompt(
            character_name=char.name,
            role=char.role,
            persona=char.persona,
            knows_ids=char.knows,
            liar=char.liar,
            lie_strategy=char.lie_strategy,
            eligible_evidence_ids=eligible_limited,
            max_evidence_per_answer=self.case.reveal_rules.max_evidence_per_answer,
            facts=char.facts,
        )
        messages = [{"role": "system", "content": system}]
        for user, assistant in self.state.conversation_history:
            messages.append({"role": "user", "content": user})
            messages.append({"role": "assistant", "content": assistant})
        messages.append({"role": "user", "content": question})

        dry_response = ""
        if self.dry_run:
            if eligible_limited:
                dry_response = f"(dry-run) I might know something. [{eligible_limited[0]}]"
            else:
                dry_response = "(dry-run) I don't have anything to add about that."

        chat_fn = chat_fn or ollama_chat
        response = chat_fn(
            self.base_url,
            self.npc_model,
            messages,
            dry_run=self.dry_run,
            dry_run_response=dry_response,
        )

        # Consume question budget
        self.state.questions_remaining = max(0, self.state.questions_remaining - 1)
        self.state.questions_asked_per_character[character_name] = (
            self.state.questions_asked_per_character.get(character_name, 0) + 1
        )
        self.state.conversation_history.append((question, response))

        # Unlock at most one evidence from response
        found_ids = extract_evidence_ids_from_response(response)
        for eid in found_ids:
            if eid in eligible and eid not in self.state.discovered_evidence_ids:
                self.state.discovered_evidence_ids.add(eid)
                break  # at most one per answer

        return response

    def start_talking(self, character_name: str) -> bool:
        """Set active character. Returns True if valid."""
        if self.case.get_character(character_name):
            self.state.active_character = character_name
            self.state.characters_talked_to.add(character_name)
            self.state.conversation_history = []
            return True
        return False

    def can_go_to_trial(self) -> bool:
        """True if all critical evidence is discovered."""
        return all(
            eid in self.state.discovered_evidence_ids
            for eid in self.case.critical_evidence_ids
        )

    def go_to_trial(self) -> None:
        self.state.phase = Phase.COURTROOM
        self.state.active_character = None
        self.state.conversation_history = []
        self.state.trial_points = max(
            0,
            POINTS_PER_EVIDENCE * len(self.state.discovered_evidence_ids)
            - POINTS_PER_CLUE * len(self.state.clues_viewed),
        )

    def get_investigation_points(self) -> int:
        """Current points from evidence (+10 each) minus clues viewed (-5 each)."""
        return max(
            0,
            POINTS_PER_EVIDENCE * len(self.state.discovered_evidence_ids)
            - POINTS_PER_CLUE * len(self.state.clues_viewed),
        )

    def record_clues_viewed(self, evidence_ids: list[str]) -> None:
        """Mark these evidence IDs' clues as viewed (each costs 5 points)."""
        self.state.clues_viewed.update(evidence_ids)

    def spend_points_cancel_attacks(self, num_to_cancel: int) -> int:
        """Cancel up to num_to_cancel defense attacks. Returns number actually cancelled."""
        cost = POINTS_PER_ATTACK_CANCEL * num_to_cancel
        if cost > self.state.trial_points or num_to_cancel <= 0:
            return 0
        # Remove that many attacks (from the end so order is predictable)
        n = min(num_to_cancel, len(self.state.defense_attacks))
        for _ in range(n):
            self.state.defense_attacks.pop()
        self.state.trial_points -= POINTS_PER_ATTACK_CANCEL * n
        return n

    def defense_opening(self, chat_fn: Callable[..., str] | None = None) -> str:
        prompt = defense_opening_prompt(
            self.case.title, self.case.scenario_intro
        )
        messages = [{"role": "user", "content": prompt}]
        chat_fn = chat_fn or ollama_chat
        return chat_fn(
            self.base_url,
            self.defense_model,
            messages,
            dry_run=self.dry_run,
            dry_run_response="(dry-run) The defense emphasizes presumption of innocence.",
        )

    def defense_rebuttal(
        self,
        presented_evidence_ids: list[str],
        chat_fn: Callable[..., str] | None = None,
    ) -> tuple[str, list[dict[str, str]]]:
        """Returns (summary, attacks). Attacks are stored on state."""
        descs = []
        vulns: dict[str, list[str]] = {}
        for eid in presented_evidence_ids:
            ev = self.case.get_evidence(eid)
            if ev:
                descs.append(f"- {eid}: {ev.description}")
                vulns[eid] = ev.vulnerabilities
        prompt = defense_rebuttal_prompt(
            self.case.title, descs, vulns
        )
        messages = [{"role": "user", "content": prompt}]
        chat_fn = chat_fn or ollama_chat
        raw = chat_fn(
            self.base_url,
            self.defense_model,
            messages,
            dry_run=self.dry_run,
            dry_run_response='{"attacks":[{"evidence_id":"E2","tag":"inconsistent_witness"}],"summary":"Dry-run rebuttal."}',
        )
        attacks, summary = parse_defense_rebuttal_json(raw)
        self.state.defense_attacks = attacks
        return (summary, attacks)

    def defense_closing(
        self,
        prosecution_closing: str,
        chat_fn: Callable[..., str] | None = None,
    ) -> str:
        prompt = defense_closing_prompt(self.case.title, prosecution_closing)
        messages = [{"role": "user", "content": prompt}]
        chat_fn = chat_fn or ollama_chat
        return chat_fn(
            self.base_url,
            self.defense_model,
            messages,
            dry_run=self.dry_run,
            dry_run_response="(dry-run) Defense closing: reasonable doubt.",
        )

    def judge_decision(
        self,
        prosecution_evidence_descriptions: list[str],
        defense_summary: str,
        chat_fn: Callable[..., str] | None = None,
    ) -> tuple[Verdict, float, str]:
        """Compute verdict deterministically; get LLM explanation. Returns (verdict, score, explanation)."""
        verdict, score = get_verdict(
            self.case,
            self.state.discovered_evidence_ids,
            self.state.presented_evidence_ids,
            self.state.defense_attacks,
        )
        self.state.final_score = score
        self.state.verdict = verdict

        prompt = judge_explanation_prompt(
            self.case.title,
            prosecution_evidence_descriptions,
            defense_summary,
            score,
            verdict.value,
        )
        messages = [{"role": "user", "content": prompt}]
        chat_fn = chat_fn or ollama_chat
        raw = chat_fn(
            self.base_url,
            self.judge_model,
            messages,
            dry_run=self.dry_run,
            dry_run_response=(
                '{"verdict_explanation":"Dry-run explanation.","key_evidence_ids":["E1"],"score_interpretation":"Score led to this outcome."}'
            ),
        )
        explanation, key_ids, score_interp = parse_judge_explanation_json(raw)
        self.state.judge_explanation = explanation or score_interp or "(No explanation parsed.)"
        return (verdict, score, self.state.judge_explanation)

    def set_presented_evidence(self, evidence_ids: list[str]) -> None:
        max_n = self.case.reveal_rules.max_evidence_presentation
        self.state.presented_evidence_ids = [
            eid for eid in evidence_ids
            if eid in self.state.discovered_evidence_ids
        ][:max_n]

    def end_game(self) -> None:
        self.state.phase = Phase.ENDED
