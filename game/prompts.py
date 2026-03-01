"""System prompts and templates for NPC, defense, and judge."""

from __future__ import annotations


def npc_system_prompt(
    character_name: str,
    role: str,
    persona: str,
    knows_ids: list[str],
    liar: bool,
    lie_strategy: str,
    eligible_evidence_ids: list[str],
    max_evidence_per_answer: int,
    facts: list[str] | None = None,
) -> str:
    """Build system prompt for NPC interrogation. Constrains to truth and evidence IDs."""
    facts_block = ""
    if facts:
        facts_lines = "\n".join(f"  - {f}" for f in facts)
        facts_block = (
            "\n\nCANONICAL FACTS (use these exactly when asked about times, dates, or events; do NOT invent other times):\n"
            + facts_lines
            + "\nStick to these facts. If asked about a time or event, use only the times and details above."
        )

    liar_instruction = ""
    if liar and lie_strategy:
        liar_instruction = (
            f"\n\nYou are a LIAR. When it suits you, lie according to this strategy: {lie_strategy}. "
            "Your lies must be consistent with this strategy. You may still reveal some evidence if it fits your strategy."
        )

    evidence_rule = ""
    if eligible_evidence_ids:
        ids_str = ", ".join(eligible_evidence_ids)
        evidence_rule = (
            f"\n\nYou may reveal at most {max_evidence_per_answer} piece(s) of evidence in this answer. "
            f"If you reveal evidence, you MUST include exactly one of these evidence IDs in square brackets: {ids_str}. "
            f"Example: 'I did see something... [E2]' Use only one bracketed ID per answer. "
            "If you do not wish to reveal any evidence, do not include any bracketed ID."
        )
    else:
        evidence_rule = (
            "\n\nDo NOT reveal any new evidence in this answer. Do not include any bracketed evidence IDs like [E1]."
        )

    return (
        f"You are {character_name}, {role}. "
        f"Persona: {persona}\n\n"
        "You are being questioned by the prosecutor. Answer in first person, briefly (2-4 sentences typically). "
        "You only know about facts that correspond to evidence IDs you are allowed to reveal. "
        "Your character can only reveal evidence by referencing one of the allowed evidence IDs in square brackets, e.g. [E1]. "
        "Never invent evidence or use evidence IDs not in the allowed list for this turn."
        f"{facts_block}"
        f"{evidence_rule}"
        f"{liar_instruction}"
    )


def defense_opening_prompt(case_title: str, scenario_intro: str) -> str:
    return (
        f"Case: {case_title}. Scenario: {scenario_intro}\n\n"
        "You are the defense attorney. Give a short opening statement (2-4 sentences) "
        "that emphasizes presumption of innocence and that the prosecution must prove guilt. "
        "Do not invent facts; only reference the scenario."
    )


def defense_rebuttal_prompt(
    case_title: str,
    presented_evidence_descriptions: list[str],
    evidence_vulnerabilities: dict[str, list[str]],
) -> str:
    """Prompt for defense rebuttal. Model must respond with JSON only."""
    vuln_desc = "\n".join(
        f"- {eid}: vulnerabilities: {', '.join(vulns)}"
        for eid, vulns in evidence_vulnerabilities.items()
    )
    return (
        f"Case: {case_title}\n\n"
        "You are the defense. The prosecution has presented the following evidence:\n"
        + "\n".join(presented_evidence_descriptions)
        + "\n\nEvidence IDs and their possible vulnerabilities (you may attack using these tags):\n"
        + vuln_desc
        + "\n\nRespond with a JSON object ONLY, no other text. Use this exact structure:\n"
        '{"attacks": [{"evidence_id": "E1", "tag": "contamination"}, ...], "summary": "1-2 sentence summary"}\n'
        "attacks: list of at most 5 attacks. Each attack must use an evidence_id that was presented and a tag from that evidence's vulnerabilities. "
        "summary: brief plain English summary of your rebuttal. If you have no valid attacks, use empty attacks []."
    )


def defense_closing_prompt(case_title: str, prosecution_closing: str) -> str:
    return (
        f"Case: {case_title}\n\n"
        "You are the defense. The prosecution gave this closing statement:\n"
        f"{prosecution_closing}\n\n"
        "Give a short closing statement (2-4 sentences) arguing reasonable doubt. Do not invent facts."
    )


def judge_explanation_prompt(
    case_title: str,
    prosecution_evidence_descriptions: list[str],
    defense_summary: str,
    score: float,
    verdict: str,
) -> str:
    """Judge must output JSON with verdict_explanation, key_evidence_ids, score_interpretation."""
    return (
        f"Case: {case_title}\n\n"
        "You are the judge. Summarize your reasoning.\n\n"
        "Evidence presented by prosecution:\n"
        + "\n".join(prosecution_evidence_descriptions)
        + "\n\nDefense summary: "
        + defense_summary
        + f"\n\nDeterministic score (already computed): {score}. Verdict (already determined): {verdict}.\n\n"
        "Respond with a JSON object ONLY:\n"
        '{"verdict_explanation": "2-4 sentences explaining the verdict", '
        '"key_evidence_ids": ["E1", "E2"], '
        '"score_interpretation": "1-2 sentences on how the score led to this outcome"}\n'
        "key_evidence_ids: list of evidence IDs you consider most important."
    )
