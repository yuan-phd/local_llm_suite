# PropSwift Local LLM Pipeline — Test Suite

## Prerequisites

- Ollama installed and running (`ollama serve`)
- Qwen 3 14B model pulled (`ollama pull qwen3:14b`)
- Python 3.10+
- `requests` library (`pip install requests`)

## Files

```
test_pipeline.py   — Main test runner (classifier + listing matcher)
test_emails.py     — 12 realistic test emails with expected results
test_listings.py   — 10 simulated active listings
prompts.py         — System prompts (adapted from GPT-4o-mini originals)
schemas.py         — JSON Schema for Ollama structured output
```

## Usage

```bash
# Run all 12 test emails
python test_pipeline.py

# Run a single email (by index 0-11)
python test_pipeline.py --email 0

# Verbose mode (show raw JSON + scoring details)
python test_pipeline.py --verbose

# Combine
python test_pipeline.py --email 5 --verbose
```

## What it tests

**Call 1 — Email Classifier:** Sends each email to Qwen 3 14B with JSON Schema
constraint. Compares output against expected values (email_phase, full_name,
mentioned_rent). Reports mismatches.

**Call 2 — Listing Matcher:** Takes the property_reference from Call 1, runs the
code-based scoring logic against test listings. Falls back to LLM only when
score is below threshold or there's a tie.
