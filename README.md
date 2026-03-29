# PropSwift Local LLM Test Suite

Test scripts for evaluating local LLM deployment (Ollama + Qwen 3 14B) as an alternative to OpenAI API calls in PropSwift.

## Prerequisites

- [Ollama](https://ollama.com/download/mac) installed and running
- Qwen 3 14B model: `ollama pull qwen3:14b`
- Python 3.10+
- `pip install requests`

## Files

| File | Purpose |
|---|---|
| `test_pipeline.py` | Main test runner — email classifier, listing matcher, ranking |
| `test_emails.py` | 12 simulated test emails covering all 7 classification phases |
| `test_emails_real.py` | 15 real-world test emails |
| `test_listings.py` | 10 simulated listings for matcher testing |
| `test_ranking_data.py` | 5 applicants for ranking testing |
| `prompts.py` | System prompts (classifier, listing matcher, ranking) |
| `schemas.py` | JSON Schema definitions for Ollama structured output |
| `ollama_adapter.py` | Sync adapter — drop-in replacement for OpenAI SDK |
| `ollama_adapter_async.py` | Async adapter — drop-in replacement for AsyncOpenAI (used in PropSwift) |
| `test_adapter.py` | Adapter verification tests |
| `local-llm-project-plan.md` | Full project documentation, test results, and future plans |

## Usage

```bash
# Run all 12 simulated email tests
python test_pipeline.py

# Run all 15 real email tests
python test_pipeline.py --real

# Run a single email by index
python test_pipeline.py --email 0

# Run ranking test (5 applicants)
python test_pipeline.py --rank

# Verbose mode (show full JSON output)
python test_pipeline.py --rank --verbose

# Test the Ollama adapter
python test_adapter.py
```

## Results Summary

**Email Classifier:** 10/12 simulated, 12/15 real emails correctly classified. Rent vs income distinction 100% accurate.

**Listing Matcher:** All addresses correctly matched via code scoring. LLM fallback rarely triggered.

**Ranking:** Correct relative ordering every time. Absolute scores too high — deterministic scoring should be moved to code.

See `local-llm-project-plan.md` for full details.
