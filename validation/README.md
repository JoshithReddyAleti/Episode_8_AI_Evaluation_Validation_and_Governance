# ✅ Validation — Enterprise Data Quality for AI Systems

> *Evaluation asks "is this good?" Validation asks "is this the right shape?" You need both.*

---

## Validation vs Evaluation — The Distinction

| Validation | Evaluation |
|---|---|
| Does the output match a schema? | Is the output quality good? |
| Binary pass/fail | Continuous score |
| Runs on every request | Runs on a sample |
| Deterministic | Statistical |
| Fast (milliseconds) | Slow (seconds to minutes) |
| Prevents crashes | Measures quality |

Both are essential. Validation is the safety net; evaluation is the quality bar.

---

## The 6 Layers of Enterprise Validation

### 1. Input Validation (`input_validation.py`)

**Purpose:** Reject bad inputs before they reach the LLM.

**Checks:**
- Length limits (prevent context stuffing attacks)
- Encoding checks (valid UTF-8, no null bytes)
- Injection patterns (known prompt injection strings)
- PII scanning (block SSNs, credit cards from being sent to LLMs)
- Rate limiting (per-user, per-IP)
- Schema compliance (does the request match the expected structure?)

### 2. Output Schema Validation (`output_schema_validation.py`)

**Purpose:** Ensure LLM outputs match the expected structure.

**Pydantic-based validation:**
```python
class ExtractedData(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(ge=0, le=150)
    confidence: float = Field(ge=0, le=1)
    
    @validator('name')
    def name_no_special_chars(cls, v):
        if not re.match(r"^[a-zA-Z\s'-]+$", v):
            raise ValueError("Name contains invalid characters")
        return v

# LLM output → parse → validate → use
try:
    validated = ExtractedData.model_validate_json(llm_output)
except ValidationError as e:
    # Handle: retry, fallback, or fail
```

### 3. Pydantic Validators (`pydantic_validators.py`)

**Enterprise patterns:**
- Field validators (per-field rules)
- Root validators (cross-field consistency)
- Custom types (BranchedInt, EmailWithDomain, etc.)
- Model validators (post-parsing hooks)

### 4. Type Coercion and Fallbacks (`type_coercion_and_fallbacks.py`)

**When strict validation fails, coerce where safe:**
```
LLM returns: {"age": "25"}  # string instead of int
→ Coerce to int (safe)

LLM returns: {"age": "twenty-five"}
→ Cannot coerce → fallback strategy:
  - Retry with clearer prompt
  - Return default value
  - Fail with graceful error
```

### 5. Retry Strategies (`retry_strategies.py`)

**When validation fails, retry intelligently:**

```python
class ValidationRetryStrategy:
    def __init__(self, max_retries=3):
        self.max_retries = max_retries
    
    def execute(self, llm_call, schema):
        for attempt in range(self.max_retries):
            output = llm_call()
            try:
                return schema.model_validate_json(output)
            except ValidationError as e:
                # Add error to next prompt to help LLM correct
                llm_call.add_context(f"Previous attempt failed validation: {e}. Try again.")
        # All retries failed - return fallback
        return self.fallback()
```

### 6. Guardrail Validators (`guardrail_validators.py`)

**Post-validation semantic checks:**
- Toxicity classifier on outputs
- PII detection (didn't leak user data?)
- Topic classifier (stayed on-topic?)
- Prompt leakage detection (didn't reveal system prompt?)

### The Validation Pipeline (`validation_pipeline.py`)

**Enterprise pattern — every LLM call goes through this:**

```
Input → Input Validation → LLM → Output Schema Validation → 
  → Type Coercion (if needed) → Retry (if failed) → 
  → Guardrail Checks → Return
```

Every layer has:
- A pass path (continue)
- A retry path (fix and try again)
- A fail path (graceful degradation)
- Full logging (for audit trails)

---

## Production Validation Metrics

Track these in production:
- Validation pass rate per endpoint
- Retry rate (how often does the LLM need to be corrected?)
- Fallback rate (how often does validation fully fail?)
- Time spent in validation (should be < 5% of total request time)

---

*Previous: [← Agent Evaluation](../agent_evaluation/README.md) · Next: [Hallucination →](../hallucination/README.md)*

*Back to [main README](../../README.md)*
