# Case JSON Schema

A case file defines the scenario, characters, evidence, and rules for "Courtroom Quest."

## Top-level fields

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Display name of the case |
| `scenario_intro` | string | Short narrative shown at start of investigation (should set up the story clearly) |
| `hints_intro` | string | (Optional) Narrative summary of what to look for; shown in the **hints** command. Should match the story. |
| `characters` | array | List of character objects (see below) |
| `suspects` | array of strings | Character names who are possible culprits |
| `truth` | object | Internal truth (culprit, timeline, motive, method); not shown to player |
| `evidence` | array | List of evidence items (see below) |
| `chains` | object | Named evidence chains for bonus scoring |
| `reveal_rules` | object | Global settings for evidence revelation |
| `critical_evidence_ids` | array of strings | Evidence IDs that must be discovered AND presented for Guilty |

## Character object

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Display name (used in `talk <name>`) |
| `role` | string | e.g. "witness", "suspect", "bystander" |
| `persona` | string | Personality and background for LLM roleplay |
| `knows` | array of strings | Evidence IDs this character can potentially reveal (e.g. `["E1","E3"]`) |
| `liar` | boolean | If true, character may lie |
| `lie_strategy` | string | How they lie when `liar` is true (e.g. "deny involvement", "blame others") |
| `facts` | array of strings | (Optional) Canonical facts this character knows—especially **times and dates** (e.g. "The delivery arrived at 2:05 PM."). The LLM must use these exactly when answering about times or events; do not invent other times. |

## Evidence item

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique ID (e.g. `"E1"`) — used internally; not shown in hints |
| `type` | string | e.g. "physical", "testimony", "document" |
| `description` | string | Full description for notes/evidence list |
| `hint` | string | (Optional) Short narrative clue for **hints** only: what this evidence is in story terms (e.g. "Testimony from the cleaner about who was still at the desk"). If omitted, a short form of `description` may be used. |
| `clue_instruction` | string | (Optional) Exact instruction for **clues** command: who to talk to and what to ask to get this evidence (e.g. "Talk to Jordan. Ask who was at the desk when they started cleaning."). Viewing clues costs 5 points each. |
| `weight` | number | Points toward prosecution score when presented |
| `critical` | boolean | If true, must be discovered and presented for Guilty |
| `vulnerabilities` | array of strings | Tags defense can use to undermine (e.g. `["contamination","chain_of_custody"]`) |
| `reveal_conditions` | object | When this evidence can be revealed (see below) |

## reveal_conditions

| Field | Type | Description |
|-------|------|-------------|
| `required_characters_talked_to` | array of strings | Character names player must have talked to (optional) |
| `required_evidence_ids_found` | array of strings | Evidence IDs that must already be discovered (optional) |
| `min_questions_asked_to_that_character` | number | Min questions asked to the character who knows this evidence (optional) |
| `keywords` | array of strings | If player's question matches any (case-insensitive), evidence may be eligible (optional) |

If a field is omitted, that condition is not required. All listed conditions must be satisfied for the evidence to be eligible for revelation.

## chains

Object mapping chain names to arrays of evidence IDs. Example:

```json
"chains": {
  "timeline_chain": ["E1", "E3"],
  "physical_chain": ["E2", "E4"]
}
```

If the player presents all evidence in a chain, a bonus (+3 per chain) is applied.

## reveal_rules

| Field | Type | Description |
|-------|------|-------------|
| `max_evidence_per_answer` | number | Max evidence IDs the NPC may reveal in one reply (default 1) |
| `question_budget` | number | Total questions allowed during investigation (e.g. 20) |
| `max_evidence_presentation` | number | Max evidence pieces player can present in courtroom (e.g. 5) |

## critical_evidence_ids

Array of evidence IDs that are required for a Guilty verdict. If any is not discovered by the player or not presented at trial, the maximum verdict is Not Guilty.

## Points (evidence and clues)

- **Evidence:** Each piece of evidence you discover gives **+10 points**.
- **Clues:** Viewing the **clues** screen shows exact instructions (who to ask, what to ask) for each evidence. Each clue you view costs **5 points** (deducted once per clue when first viewed).
- **Trial:** Your points are carried into the courtroom. After the defense rebuttal, you can spend **15 points per defense attack** to cancel it (undo that argument), improving your final score. Points cannot go below zero.
