# Feature: Entity Linking

## Purpose

Map natural language entity mentions (person names, venue names, paper titles) to their correct DBLP URIs.

## User Story

As a user asking "Which papers did Michael Stonebraker publish at SIGMOD?",
I want the system to correctly identify:
- "Michael Stonebraker" → `https://dblp.org/pid/s/MichaelStonebraker`
- "SIGMOD" → `https://dblp.org/conf/sigmod`

So that the generated SPARQL uses the correct URIs.

## Input/Output

**Input**:
```python
{
    "question": "Which papers did Michael Stonebraker publish at SIGMOD?",
    "mentions": [
        {"text": "Michael Stonebraker", "type": "Person"},
        {"text": "SIGMOD", "type": "Venue"}
    ]
}
```

**Output**:
```python
{
    "entities": [
        {
            "mention": "Michael Stonebraker",
            "uri": "https://dblp.org/pid/s/MichaelStonebraker",
            "label": "Michael Stonebraker",
            "type": "Person",
            "confidence": 0.95
        },
        {
            "mention": "SIGMOD",
            "uri": "https://dblp.org/conf/sigmod",
            "label": "SIGMOD Conference",
            "type": "Conference",
            "confidence": 0.99
        }
    ]
}
```

## Implementation Steps

### Step 1: Create DBLP Search Client

```python
# src/entity_linker.py

import httpx
from typing import List, Dict
from pydantic import BaseModel

class Entity(BaseModel):
    mention: str
    uri: str
    label: str
    type: str
    confidence: float

class DBLPSearchClient:
    BASE_URL = "https://dblp.org/search/publ/api"
    
    async def search(self, query: str, entity_type: str = None) -> List[Dict]:
        """Search DBLP for entities matching query."""
        params = {
            "q": query,
            "format": "json",
            "h": 5  # Limit results
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
```

### Step 2: Implement Entity Type Detection

```python
# Use LLM or rules to detect entity type from context
# Person indicators: "author", "written by", "published by"
# Venue indicators: "at", "in", "conference", "journal"
```

### Step 3: Implement Disambiguation

For ambiguous cases (e.g., common names), return multiple candidates:

```python
async def disambiguate(self, candidates: List[Entity], context: str) -> Entity:
    """Use LLM to select best candidate given context."""
    # If only one candidate, return it
    if len(candidates) == 1:
        return candidates[0]
    
    # Otherwise, use LLM to disambiguate
    prompt = f"""Given the context: "{context}"
    
Which entity is most likely meant?
{chr(10).join(f"{i+1}. {c.label} ({c.type})" for i, c in enumerate(candidates))}

Return the number."""
    # ... call LLM ...
```

### Step 4: Cache Entity Mappings

```python
# Cache frequently used entities to avoid repeated API calls
# Use a simple JSON file or SQLite database
```

## Edge Cases

1. **Entity not found**: Return empty list, let pipeline handle gracefully
2. **Multiple matches**: Return all candidates with confidence scores
3. **Ambiguous names**: Use context for disambiguation
4. **Abbreviations**: "SIGMOD" → "SIGMOD Conference"
5. **Typos**: Consider fuzzy matching

## Testing

```python
# tests/test_entity_linker.py

async def test_person_linking():
    linker = EntityLinker()
    result = await linker.link("Michael Stonebraker")
    assert result.uri == "https://dblp.org/pid/s/MichaelStonebraker"

async def test_venue_linking():
    linker = EntityLinker()
    result = await linker.link("SIGMOD")
    assert "conf/sigmod" in result.uri
```

## Dependencies

- `httpx` for async HTTP requests
- DBLP Search API availability
- Optional: LLM for disambiguation

## Acceptance Criteria

- [ ] Correctly links person names to DBLP person URIs
- [ ] Correctly links venue names to DBLP conference/journal URIs
- [ ] Returns confidence scores
- [ ] Handles ambiguous entities gracefully
- [ ] Caches results for performance
- [ ] Average latency < 500ms per entity
