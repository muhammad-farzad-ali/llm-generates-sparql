# Option 1: Remove Hardcoded Filters - Implementation Plan

## Goal

Remove hardcoded `DBLP_KEY_CLASSES` and `DBLP_KEY_PREDICATES` lists so that the system uses the **complete** DBLP schema from `data/schema.ttl`.

## Current State

### Files to Modify

| File | Current Issue | Fix |
|------|---------------|-----|
| `src/config.py` | Hardcoded `DBLP_KEY_CLASSES` (24 items) and `DBLP_KEY_PREDICATES` (70+ items) | Empty these lists |
| `src/schema_retriever.py` | `get_relevant_schema()` filters by hardcoded lists | Return all classes/properties |
| `src/validator.py` | `_validate_predicates_and_classes()` uses hardcoded sets | Use schema context only |
| `src/llm_generator.py` | Prompt includes all schema elements | Limit to top 30 predicates |

## Implementation Steps

### Step 1: Merge feature branch

```bash
git merge feature/phase1-implementation --no-edit
```

### Step 2: Edit `src/config.py`

Remove or empty the hardcoded lists:

```python
DBLP_KEY_CLASSES = []    # Use all classes from schema
DBLP_KEY_PREDICATES = [] # Use all predicates from schema
```

### Step 3: Edit `src/schema_retriever.py`

Update `get_relevant_schema()` to return ALL classes and properties:

```python
def get_relevant_schema(self, entity_types=None):
    """Get schema context - returns ALL classes and properties."""
    return SchemaContext(classes=self.classes, properties=self.properties)
```

Also remove the import of `DBLP_KEY_CLASSES` and `DBLP_KEY_PREDICATES`.

### Step 4: Edit `src/validator.py`

Update `_validate_predicates_and_classes()`:

```python
def _validate_predicates_and_classes(self, sparql, schema_context):
    errors = []
    where_clause = self._extract_where_clause(sparql)
    if not where_clause:
        return errors

    # Use schema context if available
    if not schema_context:
        return errors

    known_predicates = {p.label for p in schema_context.properties}
    known_classes = {c.label for c in schema_context.classes}

    # ... validation logic using known_predicates and known_classes
```

Remove the import of `DBLP_KEY_PREDICATES` and `DBLP_KEY_CLASSES`.

### Step 5: Edit `src/llm_generator.py`

Limit schema context in prompt to top 30 predicates:

```python
def _build_prompt(self, ...):
    limited_schema = SchemaContext(
        classes=schema_context.classes,  # All classes (~24)
        properties=schema_context.properties[:30]  # Top 30 predicates
    )
    parts.append(schema_formatter(limited_schema))
```

### Step 6: Test and verify

```bash
# Start server
python main.py

# Test schema endpoint
curl http://localhost:8000/api/v1/schema

# Test query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Papers by Michael Stonebraker", "execute": true}'
```

## Risks

| Risk | Mitigation |
|------|------------|
| Too many predicates overwhelm LLM | Limit to top 30 in prompt |
| Validation too strict | Use schema context only, skip if not provided |
| Longer prompts increase cost | GPT-5.4-nano is cheap |

## Success Criteria

- [ ] Schema endpoint returns all 24+ classes
- [ ] Schema endpoint returns all 70+ predicates
- [ ] Existing queries still work correctly
- [ ] No validation errors for known DBLP predicates
