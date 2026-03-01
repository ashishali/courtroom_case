# Courtroom Quest

A complete, runnable CLI game that works **fully offline** except for calling your local **Ollama** server for LLM responses. Two phases: **Investigation** (interrogate characters, gather evidence) and **Courtroom** (present case, defense rebuts, judge rules). The truth and evidence are defined in a JSON case file; the LLM roleplays NPCs and opposition but stays constrained to that truth. The **final verdict is deterministic** (scoring rules), not vibes.

## Requirements

- **Python 3.10+**
- **Ollama** running locally (default: `http://localhost:11434`)
- No external paid APIs; no extra Python packages required (standard library only)

## Install

1. Clone or copy this project.

## How to run

Run without `--case` to **choose a case from a menu**:

```bash
python3 main.py
```

You will see a list of cases (e.g. The Stolen Pen, The Missing Lunch, The Broken Vase, The Copied Report, The Stolen Keys). Enter a number to start.

To run a specific case:

```bash
python3 main.py --case cases/pen_stolen_case.json
```

Dry-run (no Ollama calls; stubbed responses for testing):

```bash
python3 main.py --dry-run
```

## How to change models

Set environment variables before running:

- `OLLAMA_BASE_URL` — Ollama API base (default: `http://localhost:11434`)
- `OLLAMA_NPC_MODEL` — model for NPCs during investigation (default: `llama3`)
- `OLLAMA_DEFENSE_MODEL` — model for defense attorney (default: `llama3`)
- `OLLAMA_JUDGE_MODEL` — model for judge explanation (default: `llama3`)

Example:

```bash
export OLLAMA_NPC_MODEL=llama3.2
export OLLAMA_DEFENSE_MODEL=llama3.2
export OLLAMA_JUDGE_MODEL=llama3.2
python main.py --case cases/pen_stolen_case.json
```

You can also change the defaults at the top of `main.py` (e.g. `OLLAMA_NPC_MODEL = "llama3.2"`).

## How to pull Ollama models

Install Ollama from the official site, then in a terminal:

```bash
ollama pull llama3
```

Other models you can use (pull first, then set env vars or edit `main.py`):

```bash
ollama pull llama3.2
ollama pull mistral
ollama pull phi3
```

Use the same model name in `OLLAMA_NPC_MODEL`, `OLLAMA_DEFENSE_MODEL`, and `OLLAMA_JUDGE_MODEL` if you only have one model.

## Troubleshooting

### Connection refused to localhost:11434

- **Ollama not running**  
  Start Ollama (e.g. open the Ollama app or run `ollama serve` in a terminal). Then run the game again.

- **Wrong host/port**  
  If Ollama is on another host or port, set:
  ```bash
  export OLLAMA_BASE_URL=http://YOUR_HOST:PORT
  ```

- **Firewall / VPN**  
  Ensure nothing is blocking local access to port 11434.

- **Test Ollama**  
  In a terminal:
  ```bash
  curl http://localhost:11434/api/tags
  ```
  If this fails, fix Ollama first; the game uses the same base URL.

### Timeouts

If the LLM is slow, the client uses a 120-second timeout. For very slow models, you can increase it by editing `DEFAULT_TIMEOUT` in `game/ollama_client.py`.

### Dry-run

If the game fails only when calling Ollama, run with `--dry-run` to confirm the rest of the flow (investigation commands, courtroom steps, scoring) works without the server.

## Project layout

- `main.py` — Entry point; config (env/top-of-file); investigation + courtroom loops.
- `game/`
  - `engine.py` — State machine, evidence unlock rules, NPC/rebuttal/judge orchestration.
  - `ollama_client.py` — HTTP wrapper for Ollama (`/api/chat` with `/api/generate` fallback).
  - `models.py` — Dataclasses: Case, Character, Evidence, GameState, Phase, Verdict.
  - `scoring.py` — Deterministic scoring and verdict (critical gate, weights, chains, defense undermining).
  - `prompts.py` — System prompts and templates for NPC, defense, judge.
  - `ui.py` — CLI helpers (help, notes, evidence, phase banner, verdict).
- `cases/`
  - `pen_stolen_case.json` — The Stolen Pen (office pen goes missing).
  - `missing_lunch_case.json` — The Missing Lunch (lunch taken from office fridge).
  - `broken_vase_case.json` — The Broken Vase (lobby vase broken; delivery/accident).
  - `copied_report_case.json` — The Copied Report (confidential report printed and taken).
  - `stolen_keys_case.json` — The Stolen Keys (storage room keys missing from desk).
  - `schema.md` — JSON schema description for case files.

## Gameplay summary

**Investigation:**  
`talk <name>`, `ask <question>`, `notes`, `evidence`, `accuse <name>` (optional), `trial`, `help`, `quit`. You have a fixed question budget; evidence is unlocked when conditions in the case JSON are met. NPCs only reveal evidence by referencing IDs like `[E2]` when the engine allows it.

**Courtroom:**  
Opening statement → defense opening → you choose evidence to present (limited pieces) → defense rebuttal (LLM outputs JSON with attack tags) → your closing → defense closing → judge. Verdict is computed by `scoring.py` (critical evidence gate, evidence weights, chain bonus, defense undermining); the judge LLM only explains and cites evidence.

## Optional tests

Run the minimal validation script (JSON schema and scoring logic):

```bash
python3 tests/test_validation.py
```
(Use `python` if that is your Python 3 command.)

(Requires the `tests/` folder and script; see below.)
