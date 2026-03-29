"""
PropSwift Vision Test — Extract structured data from payslips and bank statements
using local Qwen2.5-VL via Ollama.

Usage:
    python test_vision.py                    # run all tests
    python test_vision.py --file 0           # run single file by index
    python test_vision.py --verbose          # show full JSON output

Prerequisites:
    pip install PyMuPDF requests
    ollama pull qwen2.5vl:7b
"""

import argparse
import base64
import json
import time
import requests
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    print("✗ PyMuPDF not installed. Run: pip install PyMuPDF")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
OLLAMA_BASE = "http://localhost:11434"
VISION_MODEL = "qwen2.5vl:7b"

EXTRACTOR_SYSTEM = """\
You are a document data extractor for a UK residential lettings platform.
Extract all factual financial and employment data from this document image.

Return valid JSON only (no markdown). Extract these fields where present:
- document_type: "payslip" | "bank_statement" | "p60" | "sa302" | "other"
- employee_name or account_holder: full name as shown on document
- employer or bank_name: organisation name
- gross_monthly_income: numeric, monthly gross pay (null if not shown)
- net_monthly_income: numeric, monthly net/take-home pay (null if not shown)
- annual_gross_income: numeric, annual gross from YTD figures (null if not shown)
- employment_type: "permanent" | "contract" | "part_time" | "zero_hours" | null
- pay_date: date of payment in YYYY-MM-DD format (null if not shown)
- tax_code: tax code if shown (null if not shown)
- ni_number: NI number if shown (null if not shown)
- average_monthly_balance: for bank statements (null if not applicable)
- bank_name: bank name for statements (null if not applicable)
- anomalies: list of any inconsistencies or concerns found (empty list if none)
- document_quality: "clear" | "partial" | "illegible"

Only extract what is clearly visible. Do not guess or infer missing values."""

EXTRACTOR_SCHEMA = {
    "type": "object",
    "properties": {
        "document_type": {"type": "string"},
        "employee_name": {"type": ["string", "null"]},
        "account_holder": {"type": ["string", "null"]},
        "employer": {"type": ["string", "null"]},
        "bank_name": {"type": ["string", "null"]},
        "gross_monthly_income": {"type": ["number", "null"]},
        "net_monthly_income": {"type": ["number", "null"]},
        "annual_gross_income": {"type": ["number", "null"]},
        "employment_type": {"type": ["string", "null"]},
        "pay_date": {"type": ["string", "null"]},
        "tax_code": {"type": ["string", "null"]},
        "ni_number": {"type": ["string", "null"]},
        "average_monthly_balance": {"type": ["number", "null"]},
        "anomalies": {"type": "array", "items": {"type": "string"}},
        "document_quality": {"type": "string"},
    },
    "required": ["document_type", "document_quality"],
}


# ---------------------------------------------------------------------------
# Test files — update paths to match your local setup
# ---------------------------------------------------------------------------
TEST_FILES = [
    # 0: Standard payslip — TechCorp, David Chen, £55k
    {
        "path": "test_doc/test_payslip_1_standard.pdf",
        "description": "Standard payslip — TechCorp, David Chen, £55k/year",
        "expected": {
            "document_type": "payslip",
            "employee_name": "David Chen",
            "employer": "TechCorp Ltd",
            "gross_monthly_income": 4583.33,
            "net_monthly_income": 3083.33,
            "tax_code": "1257L",
            "employment_type": "permanent",
        },
    },
    # 1: NHS part-time payslip — Priya Sharma, Band 5 Nurse
    {
        "path": "test_doc/test_payslip_2_nhs_parttime.pdf",
        "description": "NHS part-time payslip — Priya Sharma, Band 5, 22.5hrs/week",
        "expected": {
            "document_type": "payslip",
            "employee_name": "Priya Sharma",
            "employer": "NHS Greater Manchester",
            "gross_monthly_income": 1850.00,
            "net_monthly_income": 1587.42,
            "tax_code": "1257L",
        },
    },
    # 2: High earner payslip — Blackstone, James Chen-Williams, £75k
    {
        "path": "test_doc/test_payslip_3_high_earner.pdf",
        "description": "High earner payslip — Blackstone, James Chen-Williams, £75k/year",
        "expected": {
            "document_type": "payslip",
            "employee_name": "James Chen-Williams",
            "employer": "Blackstone Financial Services",
            "gross_monthly_income": 6250.00,
            "net_monthly_income": 4318.75,
            "tax_code": "1257L",
        },
    },
    # 3: Bank statement — HSBC, David Chen
    {
        "path": "test_doc/test_bank_statement.pdf",
        "description": "Bank statement — HSBC, David Chen, Feb 2026",
        "expected": {
            "document_type": "bank_statement",
            "account_holder": "David Chen",
            "bank_name": "HSBC",
        },
    },
    # 4: Meridian Consulting payslip — David Thompson, £55k
    {
        "path": "test_doc/test_payslip.pdf",
        "description": "Meridian Consulting payslip — David Thompson, £55k/year",
        "expected": {
            "document_type": "payslip",
            "employee_name": "David Thompson",
            "employer": "Meridian Consulting",
            "gross_monthly_income": 4583.33,
            "net_monthly_income": 3447.18,
            "tax_code": "1257L",
        },
    },
]


# ---------------------------------------------------------------------------
# PDF to base64 images
# ---------------------------------------------------------------------------
def pdf_to_base64_images(pdf_path: str) -> list[str]:
    """Convert PDF pages to base64-encoded PNG images."""
    doc = fitz.open(pdf_path)
    images = []
    try:
        for page in doc:
            pix = page.get_pixmap(dpi=150)
            png_bytes = pix.tobytes("png")
            images.append(base64.b64encode(png_bytes).decode())
            del pix, png_bytes
    finally:
        doc.close()
    return images


# ---------------------------------------------------------------------------
# Vision extraction
# ---------------------------------------------------------------------------
def extract_document(pdf_path: str) -> dict:
    """Extract structured data from a PDF using Qwen2.5-VL."""
    images_b64 = pdf_to_base64_images(pdf_path)

    payload = {
        "model": VISION_MODEL,
        "messages": [
            {"role": "system", "content": EXTRACTOR_SYSTEM},
            {
                "role": "user",
                "content": "Extract all financial and employment data from this document as JSON per the system instructions.",
                "images": images_b64,
            },
        ],
        "stream": False,
        "format": EXTRACTOR_SCHEMA,
        "options": {
            "num_ctx": 8192,
        },
    }

    start = time.time()
    resp = requests.post(
        f"{OLLAMA_BASE}/api/chat",
        json=payload,
        timeout=300,
    )
    elapsed = time.time() - start

    resp.raise_for_status()
    data = resp.json()
    content = data["message"]["content"]

    result = json.loads(content)
    result["_elapsed_seconds"] = round(elapsed, 2)
    return result


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------
def run_single_test(idx: int, test: dict, verbose: bool = False):
    """Run extraction on one PDF and compare against expected values."""
    print(f"\n{'='*70}")
    print(f"TEST {idx}: {test['description']}")
    print(f"{'='*70}")

    import os
    if not os.path.exists(test["path"]):
        print(f"  ✗ File not found: {test['path']}")
        print(f"    Make sure PDF files are in the current directory")
        return None

    try:
        result = extract_document(test["path"])

        # Print key fields
        print(f"\n  Document type:  {result.get('document_type')}")
        print(f"  Name:           {result.get('employee_name') or result.get('account_holder')}")
        print(f"  Employer/Bank:  {result.get('employer') or result.get('bank_name')}")
        print(f"  Gross monthly:  {result.get('gross_monthly_income')}")
        print(f"  Net monthly:    {result.get('net_monthly_income')}")
        print(f"  Annual gross:   {result.get('annual_gross_income')}")
        print(f"  Employment:     {result.get('employment_type')}")
        print(f"  Tax code:       {result.get('tax_code')}")
        print(f"  NI number:      {result.get('ni_number')}")
        print(f"  Pay date:       {result.get('pay_date')}")
        print(f"  Doc quality:    {result.get('document_quality')}")
        print(f"  Anomalies:      {result.get('anomalies', [])}")
        print(f"  Time:           {result.get('_elapsed_seconds')}s")

        # Compare against expected
        expected = test.get("expected", {})
        mismatches = []
        for key, exp_val in expected.items():
            got_val = result.get(key)
            # For numbers, allow small tolerance
            if isinstance(exp_val, (int, float)) and isinstance(got_val, (int, float)):
                if abs(exp_val - got_val) > 1.0:  # £1 tolerance
                    mismatches.append(f"    {key}: expected={exp_val}, got={got_val}")
            elif got_val != exp_val:
                # Case-insensitive string comparison
                if isinstance(exp_val, str) and isinstance(got_val, str):
                    if exp_val.lower() not in got_val.lower() and got_val.lower() not in exp_val.lower():
                        mismatches.append(f"    {key}: expected={exp_val}, got={got_val}")
                else:
                    mismatches.append(f"    {key}: expected={exp_val}, got={got_val}")

        if mismatches:
            print(f"\n  ⚠ MISMATCHES:")
            for m in mismatches:
                print(m)
        elif expected:
            print(f"\n  ✓ All expected fields match")

        if verbose:
            print(f"\n  Full JSON:\n{json.dumps(result, indent=4, ensure_ascii=False)}")

        return result

    except Exception as e:
        print(f"\n  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(description="PropSwift Vision Extraction Test")
    parser.add_argument("--file", type=int, default=None, help="Run single file by index")
    parser.add_argument("--verbose", action="store_true", help="Show full JSON output")
    args = parser.parse_args()

    # Check Ollama and model
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        if not any(VISION_MODEL in m for m in models):
            print(f"✗ Model '{VISION_MODEL}' not found. Available: {models}")
            print(f"  Run: ollama pull {VISION_MODEL}")
            return
        print(f"✓ Ollama is running, model '{VISION_MODEL}' available")
    except requests.ConnectionError:
        print(f"✗ Cannot connect to Ollama at {OLLAMA_BASE}")
        return

    # Run tests
    if args.file is not None:
        if 0 <= args.file < len(TEST_FILES):
            run_single_test(args.file, TEST_FILES[args.file], args.verbose)
        else:
            print(f"✗ File index {args.file} out of range (0-{len(TEST_FILES)-1})")
    else:
        print(f"\nRunning {len(TEST_FILES)} document extraction tests...\n")
        for i, test in enumerate(TEST_FILES):
            run_single_test(i, test, args.verbose)

    print(f"\n{'='*70}")
    print("Done.")


if __name__ == "__main__":
    main()
