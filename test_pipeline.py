"""
PropSwift Local LLM Pipeline — Test Script
Tests email classifier (Call 1), listing matcher (Call 2), and ranking (Call 3)
using Ollama + Qwen 3 14B.

Usage:
    python test_pipeline.py              # run all simulated email tests
    python test_pipeline.py --real       # run real email tests
    python test_pipeline.py --email 0    # run single email by index
    python test_pipeline.py --rank       # run ranking test
    python test_pipeline.py --verbose    # show full model output
"""

import argparse
import json
import time
import requests
from test_emails import TEST_EMAILS
from test_emails_real import REAL_TEST_EMAILS
from test_listings import TEST_LISTINGS
from test_ranking_data import TEST_LISTING_FOR_RANKING, TEST_APPLICANTS
from prompts import EMAIL_CLASSIFIER_SYSTEM, LISTING_MATCHER_SYSTEM, RANKER_SYSTEM
from schemas import EMAIL_CLASSIFIER_SCHEMA, RANKER_SCHEMA

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
OLLAMA_BASE = "http://localhost:11434"
MODEL = "qwen3:14b"


# ---------------------------------------------------------------------------
# Call 1 — Email Classifier
# ---------------------------------------------------------------------------
def classify_email(
    sender_name: str | None,
    subject: str,
    body: str,
    attachments: list[str] | None = None,
) -> dict:
    """Classify an email using the local LLM. Returns parsed JSON dict."""

    # Build user message (same format as the GPT-4o-mini pipeline)
    parts = []
    if sender_name:
        parts.append(f"Sender display name: {sender_name}")
    parts.append(f"Subject: {subject}")
    parts.append(f"Body preview (500 chars): {body[:500]}")
    attachment_str = ", ".join(attachments) if attachments else "none"
    parts.append(f"Attachment filenames: {attachment_str}")
    user_message = "\n".join(parts)

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": EMAIL_CLASSIFIER_SYSTEM},
            {"role": "user", "content": user_message},
        ],
        "think": False,
        "stream": False,
        "format": EMAIL_CLASSIFIER_SCHEMA,
    }

    start = time.time()
    resp = requests.post(f"{OLLAMA_BASE}/api/chat", json=payload, timeout=120)
    elapsed = time.time() - start

    resp.raise_for_status()
    data = resp.json()
    content = data["message"]["content"]

    result = json.loads(content)
    result["_elapsed_seconds"] = round(elapsed, 2)

    # Normalise full_name to title case
    if result.get("full_name"):
        result["full_name"] = result["full_name"].strip().title()

    return result


# ---------------------------------------------------------------------------
# Call 2 — Listing Matcher (code scoring + LLM fallback)
# ---------------------------------------------------------------------------
_CONFIDENT_SCORE_THRESHOLD = 3


def _normalise(text: str) -> str:
    """Lowercase, strip spaces."""
    return text.lower().strip().replace(" ", "")


def _normalise_keep_spaces(text: str) -> str:
    """Lowercase, strip outer spaces, collapse inner whitespace."""
    return " ".join(text.lower().split())


def _score_listing(
    listing: dict,
    property_reference: str | None,
    mentioned_rent: float | None,
) -> int:
    """Score a listing against extracted hints. See project plan for point table."""
    if not property_reference:
        return 0

    score = 0
    hint = _normalise_keep_spaces(property_reference)

    # listing_reference: +10
    lr = listing.get("listing_reference")
    if lr:
        lr_norm = _normalise_keep_spaces(lr)
        if lr_norm in hint or hint in lr_norm:
            score += 10

    # address_line1: +8
    addr = listing.get("address_line1", "")
    if addr:
        addr_norm = _normalise_keep_spaces(addr)
        if addr_norm in hint or hint in addr_norm:
            score += 8

    # postcode: +6
    pc = listing.get("postcode", "")
    if pc:
        if _normalise(pc) in _normalise(property_reference):
            score += 6

    # city: +2 (but not if city name is part of a street name in the hint)
    city = listing.get("city", "")
    if city:
        city_norm = _normalise_keep_spaces(city)
        # Simple heuristic: skip if "city road/street/lane/drive" appears in hint
        street_suffixes = ["road", "street", "lane", "drive", "avenue", "way", "close"]
        city_is_street = any(f"{city_norm} {s}" in hint for s in street_suffixes)
        if city_norm in hint and not city_is_street:
            score += 2

    # monthly_rent: +5 (±10%), +3 bonus (±0.5%)
    rent = listing.get("monthly_rent")
    if rent and mentioned_rent:
        try:
            rent = float(rent)
            mentioned_rent = float(mentioned_rent)
            if rent > 0 and abs(rent - mentioned_rent) / rent <= 0.10:
                score += 5
                if abs(rent - mentioned_rent) / rent <= 0.005:
                    score += 3
        except (ValueError, TypeError):
            pass

    return score


def _llm_match_listing(
    property_reference: str,
    listings: list[dict],
) -> str:
    """Call LLM to match property reference to a listing. Returns UUID or 'NEW'."""

    listings_for_llm = [
        {
            "id": l["id"],
            "address_line1": l.get("address_line1", ""),
            "city": l.get("city", ""),
            "postcode": l.get("postcode", ""),
            "listing_reference": l.get("listing_reference"),
        }
        for l in listings
    ]

    user_message = (
        f"Property reference: \"{property_reference}\"\n\n"
        f"Existing listings:\n{json.dumps(listings_for_llm, indent=2)}"
    )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": LISTING_MATCHER_SYSTEM},
            {"role": "user", "content": user_message},
        ],
        "think": False,
        "stream": False,
    }

    resp = requests.post(f"{OLLAMA_BASE}/api/chat", json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["message"]["content"].strip()


def find_listing(
    property_reference: str | None,
    mentioned_rent: float | None,
    listings: list[dict],
) -> dict:
    """
    Full listing match logic:
    1. Score all listings
    2. If confident (score >= 3, no tie) → use code result
    3. Otherwise → LLM fallback
    Returns dict with match result and debug info.
    """
    if not listings:
        return {"matched_id": None, "method": "no_listings", "scores": {}}

    # Score all listings
    scores = {}
    for l in listings:
        s = _score_listing(l, property_reference, mentioned_rent)
        scores[l["id"]] = {"score": s, "address": l.get("address_line1", "")}

    # No property reference → fall back to oldest listing
    if not property_reference:
        oldest = listings[0]["id"]
        return {"matched_id": oldest, "method": "no_reference_fallback", "scores": scores}

    # Find best score(s)
    max_score = max(s["score"] for s in scores.values())

    # All zero → auto-create
    if max_score == 0:
        return {"matched_id": None, "method": "no_match_auto_create", "scores": scores}

    # Check for tie
    top_ids = [lid for lid, s in scores.items() if s["score"] == max_score]
    is_tie = len(top_ids) > 1

    # Confident and no tie → code result
    if max_score >= _CONFIDENT_SCORE_THRESHOLD and not is_tie:
        return {"matched_id": top_ids[0], "method": "code_scoring", "scores": scores}

    # Otherwise → LLM fallback
    llm_result = _llm_match_listing(property_reference, listings)

    # Validate LLM result
    valid_ids = {l["id"] for l in listings}
    if llm_result in valid_ids:
        return {"matched_id": llm_result, "method": "llm_fallback", "scores": scores}
    else:
        return {"matched_id": None, "method": "llm_said_new", "scores": scores}


# ---------------------------------------------------------------------------
# Call 3 — Applicant Ranking
# ---------------------------------------------------------------------------
def rank_applicants(
    listing_data: dict,
    applicants: list[dict],
) -> dict:
    """Rank applicants for a listing using the local LLM. Returns parsed JSON."""

    # Build the user message (same structure as the production pipeline)
    applicants_for_llm = []
    for a in applicants:
        applicants_for_llm.append({
            "applicant_id": a["applicant_id"],
            "name": a["name"],
            "email": a["email"],
            "extracted_summary": a["extracted_summary"],
        })

    user_message = json.dumps({
        "listing": listing_data,
        "applicants": applicants_for_llm,
    }, indent=2)

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": RANKER_SYSTEM},
            {"role": "user", "content": user_message},
        ],
        "think": False,
        "stream": False,
        "format": RANKER_SCHEMA,
    }

    start = time.time()
    resp = requests.post(f"{OLLAMA_BASE}/api/chat", json=payload, timeout=300)
    elapsed = time.time() - start

    resp.raise_for_status()
    data = resp.json()
    content = data["message"]["content"]

    result = json.loads(content)
    result["_elapsed_seconds"] = round(elapsed, 2)
    return result


def run_ranking_test(verbose: bool = False):
    """Run the ranking test with test applicant data."""
    print(f"\n{'='*70}")
    print("RANKING TEST")
    print(f"{'='*70}")
    print(f"\nListing: {TEST_LISTING_FOR_RANKING['address']}")
    print(f"Monthly rent: £{TEST_LISTING_FOR_RANKING['monthly_rent']}")
    print(f"Applicants: {len(TEST_APPLICANTS)}")

    try:
        result = rank_applicants(TEST_LISTING_FOR_RANKING, TEST_APPLICANTS)
        print(f"\nCompleted in {result.get('_elapsed_seconds')}s")

        ranked = result.get("ranked_applicants", [])
        print(f"\n--- Results ({len(ranked)} applicants ranked) ---\n")

        for r in ranked:
            print(f"  #{r['rank']} {r['name']} ({r['email']})")
            print(f"     Score: {r['match_score']}  Tier: {r['tier']}")
            print(f"     Affordability: {r.get('affordability_outcome', 'N/A')}")
            print(f"     Employment: {r.get('employment_status', 'N/A')}")
            print(f"     Move-in: {r.get('move_in_date', 'N/A')}")
            print(f"     Occupants: {r.get('occupants', 'N/A')}")
            if r.get("red_flags"):
                print(f"     Red flags: {r['red_flags']}")
            if r.get("missing_documents"):
                print(f"     Missing docs: {r['missing_documents']}")
            if r.get("key_details"):
                print(f"     Key details: {r['key_details']}")
            print(f"     Summary: {r.get('summary', '')}")
            print()

        # Check against expected values
        print("--- Validation ---\n")
        applicant_map = {a["applicant_id"]: a for a in TEST_APPLICANTS}
        all_ok = True
        for r in ranked:
            aid = r["applicant_id"]
            expected = applicant_map.get(aid, {})
            exp_tier = expected.get("expected_tier")
            exp_range = expected.get("expected_score_range")
            score = r["match_score"]
            tier = r["tier"]
            issues = []

            if exp_tier and tier != exp_tier:
                issues.append(f"tier: expected={exp_tier}, got={tier}")
            if exp_range and not (exp_range[0] <= score <= exp_range[1]):
                issues.append(f"score {score} outside expected range {exp_range}")

            if issues:
                all_ok = False
                print(f"  ⚠ {r['name']}: {'; '.join(issues)}")
            else:
                print(f"  ✓ {r['name']}: score={score}, tier={tier}")

        if verbose:
            print(f"\n--- Full JSON ---\n{json.dumps(result, indent=2, ensure_ascii=False)}")

    except Exception as e:
        print(f"\n  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------
def run_single_test(idx: int, email: dict, listings: list[dict], verbose: bool = False):
    """Run classifier + listing matcher on one test email."""
    print(f"\n{'='*70}")
    print(f"TEST {idx}: {email['subject']}")
    print(f"{'='*70}")

    # --- Call 1: Classify ---
    print("\n--- Call 1: Email Classifier ---")
    try:
        result = classify_email(
            sender_name=email.get("sender_name"),
            subject=email["subject"],
            body=email["body"],
            attachments=email.get("attachments"),
        )
        print(f"  Phase:     {result.get('email_phase')}")
        print(f"  Confidence:{result.get('confidence')}")
        print(f"  Name:      {result.get('full_name')}")
        print(f"  Property:  {result.get('property_reference')}")
        print(f"  Rent:      {result.get('mentioned_rent')}")
        print(f"  Time:      {result.get('_elapsed_seconds')}s")

        if verbose:
            print(f"\n  Raw JSON: {json.dumps(result, indent=4)}")

        # Check against expected values if provided
        expected = email.get("expected", {})
        mismatches = []
        for key, exp_val in expected.items():
            got_val = result.get(key)
            if got_val != exp_val:
                mismatches.append(f"    {key}: expected={exp_val}, got={got_val}")
        if mismatches:
            print(f"\n  ⚠ MISMATCHES:")
            for m in mismatches:
                print(m)
        elif expected:
            print(f"\n  ✓ All expected fields match")

    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        result = {}

    # --- Call 2: Listing Matcher ---
    prop_ref = result.get("property_reference")
    rent = result.get("mentioned_rent")

    print(f"\n--- Call 2: Listing Matcher ---")
    try:
        match = find_listing(prop_ref, rent, listings)
        print(f"  Matched ID: {match['matched_id']}")
        print(f"  Method:     {match['method']}")
        if verbose:
            print(f"  Scores:     {json.dumps(match['scores'], indent=4)}")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")

    return result


def main():
    parser = argparse.ArgumentParser(description="PropSwift Local LLM Pipeline Test")
    parser.add_argument("--email", type=int, default=None, help="Run single email by index")
    parser.add_argument("--real", action="store_true", help="Use real emails instead of simulated")
    parser.add_argument("--rank", action="store_true", help="Run ranking test")
    parser.add_argument("--verbose", action="store_true", help="Show full model output")
    args = parser.parse_args()

    # Select email set
    emails = REAL_TEST_EMAILS if args.real else TEST_EMAILS
    label = "real" if args.real else "simulated"

    # Check Ollama is running
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        if not any(MODEL in m for m in models):
            print(f"✗ Model '{MODEL}' not found. Available: {models}")
            print(f"  Run: ollama pull {MODEL}")
            return
        print(f"✓ Ollama is running, model '{MODEL}' available")
    except requests.ConnectionError:
        print(f"✗ Cannot connect to Ollama at {OLLAMA_BASE}")
        print("  Make sure Ollama is running (open the Ollama app or run 'ollama serve')")
        return

    # Run tests
    if args.rank:
        run_ranking_test(args.verbose)
    else:
        listings = TEST_LISTINGS
        if args.email is not None:
            if 0 <= args.email < len(emails):
                run_single_test(args.email, emails[args.email], listings, args.verbose)
            else:
                print(f"✗ Email index {args.email} out of range (0-{len(emails)-1})")
        else:
            print(f"\nRunning {len(emails)} {label} test emails...\n")
            for i, email in enumerate(emails):
                run_single_test(i, email, listings, args.verbose)

    print(f"\n{'='*70}")
    print("Done.")


if __name__ == "__main__":
    main()
