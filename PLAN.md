# Option 1: Remove Hardcoded Filters

## Goal

Remove hardcoded `DBLP_KEY_CLASSES` and `DBLP_KEY_PREDICATES` lists so that the system uses the **complete** DBLP schema from `data/schema.ttl`.

## Current Problem

The schema retriever filters classes and predicates using hardcoded lists:

```python
# src/schema_retriever.py lines 64-75
def get_relevant_schema(self, entity_types=None):
    relevant_classes = [
        c for c in self.classes if any(k in c.label for k in DBLP_KEY_CLASSES)
    ]
    relevant_properties = [
        p for p in self.properties if any(k in p.label for k in DBLP_KEY_PREDICATES)
    ]
```

This means only ~24 classes and ~70 predicates are used, but the schema has:
- **24 classes** (currently filtered, all included)
- **70+ predicates** (only ~70 used, some missing)

## What Changes

### File: `src/config.py`

**Remove or empty these lists:**
```python
DBLP_KEY_CLASSES = []    # Use all classes from schema
DBLP_KEY_PREDICATES = [] # Use all predicates from schema
```

### File: `src/schema_retriever.py`

**Change `get_relevant_schema()`:**
```python
def get_relevant_schema(self, entity_types=None):
    # Use ALL classes and predicates from schema
    return SchemaContext(classes=self.classes, properties=self.properties)
```

### File: `src/validator.py`

**Update `_validate_predicates_and_classes()`:**
- Remove hardcoded set checks
- Use the schema context passed in for validation

## What Stays the Same

- `KNOWN_PERSON_URIS` and `KNOWN_VENUE_URIS` remain hardcoded (separate concern)
- Entity linker unchanged
- LLM generator unchanged
- Example retriever unchanged

## Risks

| Risk | Mitigation |
|------|------------|
| Too many predicates overwhelm LLM | Limit to top 30 most relevant in prompt |
| Validation becomes too strict | Keep validation lenient for unknown predicates |
| Longer prompts increase cost | Use GPT-5.4-nano (cheap) |

## Implementation Steps

1. Edit `src/config.py` - empty `DBLP_KEY_CLASSES` and `DBLP_KEY_PREDICATES`
2. Edit `src/schema_retriever.py` - return all classes/properties
3. Edit `src/validator.py` - use schema context instead of hardcoded sets
4. Test with sample queries
5. Commit and push

## Testing

```bash
# Test schema endpoint returns all classes
curl http://localhost:8000/api/v1/schema | python -m json.tool | grep "count"

# Test query still works
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Papers by Michael Stonebraker", "execute": true}'
```

## Success Criteria

- [ ] Schema endpoint returns all 24+ classes
- [ ] Schema endpoint returns all 70+ predicates
- [ ] Existing queries still work correctly
- [ ] No validation errors for known DBLP predicates
