"""
JSON Schemas for Ollama structured output.
Passed to the 'format' parameter to constrain model output.
"""

EMAIL_CLASSIFIER_SCHEMA = {
    "type": "object",
    "properties": {
        "email_phase": {
            "type": "string",
            "enum": [
                "initial_interest",
                "viewing_request",
                "post_viewing",
                "document_submission",
                "questionnaire_reply",
                "offer",
                "unknown",
            ],
        },
        "confidence": {
            "type": "number",
        },
        "property_reference": {
            "type": ["string", "null"],
        },
        "mentioned_rent": {
            "type": ["number", "null"],
        },
        "full_name": {
            "type": ["string", "null"],
        },
    },
    "required": [
        "email_phase",
        "confidence",
        "property_reference",
        "mentioned_rent",
        "full_name",
    ],
}


RANKER_SCHEMA = {
    "type": "object",
    "properties": {
        "ranked_applicants": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "rank": {"type": "integer"},
                    "applicant_id": {"type": "string"},
                    "name": {"type": ["string", "null"]},
                    "email": {"type": "string"},
                    "match_score": {"type": "integer"},
                    "tier": {"type": "string"},
                    "affordability_outcome": {"type": ["string", "null"]},
                    "employment_status": {"type": ["string", "null"]},
                    "move_in_date": {"type": ["string", "null"]},
                    "tenancy_length_months": {"type": ["integer", "null"]},
                    "occupants": {"type": ["string", "null"]},
                    "red_flags": {"type": "array", "items": {"type": "string"}},
                    "missing_documents": {"type": "array", "items": {"type": "string"}},
                    "key_details": {"type": "array", "items": {"type": "string"}},
                    "summary": {"type": "string"},
                },
                "required": [
                    "rank", "applicant_id", "name", "email", "match_score",
                    "tier", "affordability_outcome", "employment_status",
                    "move_in_date", "tenancy_length_months", "occupants",
                    "red_flags", "missing_documents", "key_details", "summary",
                ],
            },
        },
        "disclaimer": {"type": "string"},
    },
    "required": ["ranked_applicants", "disclaimer"],
}
