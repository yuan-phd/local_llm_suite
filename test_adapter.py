"""
Test the Ollama adapter — verify it works as a drop-in replacement for OpenAI SDK.
Run: python test_adapter.py
"""

import json
from ollama_adapter import OllamaClient, create_llm_client
from prompts import EMAIL_CLASSIFIER_SYSTEM, RANKER_SYSTEM
from schemas import EMAIL_CLASSIFIER_SCHEMA, RANKER_SCHEMA

MODEL = "qwen3:14b"


def test_basic_connection():
    """Test basic connectivity and model availability."""
    print("--- Test 1: Connection ---")
    client = OllamaClient()
    if not client.is_available():
        print("  ✗ Ollama not running")
        return False
    models = client.list_models()
    has_model = any(MODEL in m for m in models)
    status = "found" if has_model else "not found"
    print(f"  {'✓' if has_model else '✗'} Model '{MODEL}' {status}")
    print(f"  Available: {models}")
    return has_model


def test_simple_call():
    """Test basic chat completion without structured output."""
    print("\n--- Test 2: Simple call (think=False) ---")
    client = OllamaClient()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Say hello in one sentence."}],
        think=False,
    )
    content = response.choices[0].message.content
    reasoning = response.choices[0].message.reasoning
    print(f"  Content:   {content}")
    print(f"  Reasoning: {'None' if not reasoning else reasoning[:80] + '...'}")
    print(f"  Tokens:    {response.usage.total_tokens}")
    print(f"  ✓ think=False: reasoning {'absent' if not reasoning else 'PRESENT (unexpected)'}")


def test_simple_call_with_thinking():
    """Test chat completion with thinking enabled."""
    print("\n--- Test 3: Simple call (think=True) ---")
    client = OllamaClient()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "What is 15 × 30?"}],
        think=True,
    )
    content = response.choices[0].message.content
    reasoning = response.choices[0].message.reasoning
    print(f"  Content:   {content}")
    print(f"  Reasoning: {'None' if not reasoning else reasoning[:80] + '...'}")
    print(f"  ✓ think=True: reasoning {'present' if reasoning else 'ABSENT (unexpected)'}")


def test_json_object_format():
    """Test response_format: json_object (OpenAI style)."""
    print("\n--- Test 4: response_format json_object ---")
    client = OllamaClient()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Return a JSON with fields: name and age, for a person named Bob who is 30."}],
        response_format={"type": "json_object"},
        think=False,
    )
    content = response.choices[0].message.content
    print(f"  Raw: {content}")
    try:
        parsed = json.loads(content)
        print(f"  Parsed: {parsed}")
        print(f"  ✓ Valid JSON")
    except json.JSONDecodeError as e:
        print(f"  ✗ Invalid JSON: {e}")


def test_json_schema_format():
    """Test response_format: json_schema (OpenAI structured output style)."""
    print("\n--- Test 5: response_format json_schema ---")
    client = OllamaClient()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You classify fruit."},
            {"role": "user", "content": "Is a tomato a fruit or vegetable?"},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "classification",
                "schema": {
                    "type": "object",
                    "properties": {
                        "item": {"type": "string"},
                        "category": {"type": "string", "enum": ["fruit", "vegetable", "both"]},
                        "confidence": {"type": "number"},
                    },
                    "required": ["item", "category", "confidence"],
                },
            },
        },
        think=False,
    )
    content = response.choices[0].message.content
    print(f"  Raw: {content}")
    try:
        parsed = json.loads(content)
        print(f"  Parsed: {parsed}")
        has_fields = all(k in parsed for k in ["item", "category", "confidence"])
        print(f"  {'✓' if has_fields else '✗'} All required fields present")
    except json.JSONDecodeError as e:
        print(f"  ✗ Invalid JSON: {e}")


def test_ollama_native_schema():
    """Test passing Ollama-native schema dict directly (our current approach)."""
    print("\n--- Test 6: Ollama-native schema (format dict) ---")
    client = OllamaClient()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": EMAIL_CLASSIFIER_SYSTEM},
            {
                "role": "user",
                "content": (
                    "Sender display name: Jamie Morris\n"
                    "Subject: hi about the flat on Crofton Road\n"
                    "Body preview (500 chars): hiya, saw your ad for the flat on crofton road "
                    "in lewisham. is it still available? me and my girlfriend are looking to move "
                    "in around august. cheers, Jamie Morris\n"
                    "Attachment filenames: none"
                ),
            },
        ],
        response_format=EMAIL_CLASSIFIER_SCHEMA,  # Ollama-native schema dict
        think=False,
    )
    content = response.choices[0].message.content
    print(f"  Raw: {content}")
    try:
        parsed = json.loads(content)
        print(f"  Phase: {parsed.get('email_phase')}")
        print(f"  Name:  {parsed.get('full_name')}")
        print(f"  ✓ Email classifier works through adapter")
    except json.JSONDecodeError as e:
        print(f"  ✗ Invalid JSON: {e}")


def test_factory():
    """Test the factory function."""
    print("\n--- Test 7: Factory function ---")
    local_client = create_llm_client(use_local=True)
    print(f"  Local client type: {type(local_client).__name__}")
    assert type(local_client).__name__ == "OllamaClient"
    print(f"  ✓ Factory returns OllamaClient when use_local=True")

    # Don't test OpenAI client creation (needs API key)
    print(f"  (Skipping OpenAI client test — no API key)")


def main():
    print("=" * 60)
    print("Ollama Adapter Tests")
    print("=" * 60)

    if not test_basic_connection():
        return

    test_simple_call()
    test_simple_call_with_thinking()
    test_json_object_format()
    test_json_schema_format()
    test_ollama_native_schema()
    test_factory()

    print(f"\n{'=' * 60}")
    print("All tests complete.")


if __name__ == "__main__":
    main()
