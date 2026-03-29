"""
Test applicant data for ranking tests.
Simulates what rank_listing() would assemble from the database.
"""

# Listing context — the property being applied for
TEST_LISTING_FOR_RANKING = {
    "address": "45 Crofton Road, London SE4 1AF",
    "monthly_rent": 1500,
    "currency": "GBP",
    "min_annual_income": 45000,  # 30 × 1500
}

# Applicants — a mix of strong, borderline, and weak cases
TEST_APPLICANTS = [
    # -----------------------------------------------------------------------
    # 0: Strong applicant — verified payslip, permanent, good income
    # -----------------------------------------------------------------------
    {
        "applicant_id": "aaa-1111",
        "name": "Alice Smith",
        "email": "alice@example.com",
        "extracted_summary": {
            "full_name": "Alice Smith",
            "gross_monthly_income": 4500,
            "net_monthly_income": 3200,
            "employer": "Barclays PLC",
            "employment_type": "permanent",
            "employment_status": "Full-Time Permanent",
            "pay_date": "2026-03-31",
            "tax_code": "1257L",
            "bank_name": "HSBC",
            "average_monthly_balance": 8200,
            "income_deposits_consistent": True,
            "provided_documents": ["payslip", "bank_statement"],
            "desired_move_in_date": "2026-07-01",
            "tenancy_length_months": 12,
            "household_type": "Couple",
            "number_of_adults": 2,
            "number_of_children": 0,
            "pets": "No pets",
            "anomalies": [],
        },
        "expected_tier": "🟢 Strong match",
        "expected_score_range": (75, 100),
    },
    # -----------------------------------------------------------------------
    # 1: Decent applicant — self-reported income, no payslip yet
    # -----------------------------------------------------------------------
    {
        "applicant_id": "bbb-2222",
        "name": "Ben Taylor",
        "email": "ben.t@example.com",
        "extracted_summary": {
            "full_name": "Ben Taylor",
            "gross_monthly_income": 3800,
            "employment_status": "Full-Time Permanent",
            "employer": "NHS Greater Manchester",
            "desired_move_in_date": "2026-08-01",
            "tenancy_length_months": 12,
            "household_type": "Single",
            "number_of_adults": 1,
            "number_of_children": 0,
            "anomalies": [],
        },
        "expected_tier": "🟡 Possible match",
        "expected_score_range": (50, 79),
    },
    # -----------------------------------------------------------------------
    # 2: Weak applicant — part-time, low income, no documents
    # -----------------------------------------------------------------------
    {
        "applicant_id": "ccc-3333",
        "name": "Chloe Adams",
        "email": "chloe.a@example.com",
        "extracted_summary": {
            "full_name": "Chloe Adams",
            "gross_monthly_income": 1800,
            "employment_status": "Part-Time",
            "employer": "Costa Coffee",
            "desired_move_in_date": "ASAP",
            "household_type": "Single",
            "number_of_adults": 1,
            "number_of_children": 0,
            "pets": "1 cat",
            "anomalies": [],
        },
        "expected_tier": "🔴 Weak match",
        "expected_score_range": (0, 49),
    },
    # -----------------------------------------------------------------------
    # 3: Self-employed contractor — decent income but unverified
    # -----------------------------------------------------------------------
    {
        "applicant_id": "ddd-4444",
        "name": "David Chen",
        "email": "david.c@example.com",
        "extracted_summary": {
            "full_name": "David Chen",
            "gross_monthly_income": 5500,
            "employment_status": "Self-Employed / Company Director",
            "employment_duration": "3 years",
            "desired_move_in_date": "2026-09-01",
            "tenancy_length_months": 24,
            "household_type": "Family",
            "number_of_adults": 2,
            "number_of_children": 1,
            "advance_rent_months": 6,
            "pets": "1 dog (Labrador)",
            "anomalies": [],
        },
        "expected_tier": "🟡 Possible match",
        "expected_score_range": (50, 85),
    },
    # -----------------------------------------------------------------------
    # 5: Minimal info — just an email enquiry, almost nothing extracted
    # -----------------------------------------------------------------------
    {
        "applicant_id": "eee-5555",
        "name": "Emma Jones",
        "email": "emma.j@example.com",
        "extracted_summary": {
            "full_name": "Emma Jones",
            "anomalies": [],
        },
        "expected_tier": "⚪ Insufficient",
        "expected_score_range": (0, 30),
    },
]
