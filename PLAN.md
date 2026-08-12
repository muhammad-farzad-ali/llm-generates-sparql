# Option 2: Dynamic Entity Linking

## Goal

Remove hardcoded `KNOWN_PERSON_URIS` and `KNOWN_VENUE_URIS` so that the system discovers DBLP entity URIs **dynamically** via the DBLP Search API.

## Current Problem

Person and venue URIs are hardcoded in `src/config.py`:

```python
KNOWN_PERSON_URIS = {
    "michael stonebraker": "https://dblp.org/pid/s/MichaelStonebraker",
    "donald knuth": "https://dblp.org/pid/k/DonaldEKnuth",
    # ... only 8 persons
}

KNOWN_VENUE_URIS = {
    "sigmod": "https://dblp.org/streams/conf/sigmod",
    # ... only 14 venues
}
```

This means:
- Only 8 authors are "known"
- Only 14 venues are "known"
- Any other entity requires API call or fails

## What Changes

### File: `src/config.py`

**Remove:**
```python
KNOWN_PERSON_URIS = { ... }  # DELETE this dict
KNOWN_VENUE_URIS = { ... }   # DELETE this dict
```

### File: `src/entity_linker.py`

**Change `link()` method:**
```python
def link(self, mention, entity_hint=None):
    # 1. Check cache first (fast)
    if mention_lower in self.entity_cache:
        return Entity(...)

    # 2. If person hint or likely person, search author API
    if entity_hint == "Person":
        return self._search_and_link_person(mention)

    # 3. If venue hint, search venue API
    if entity_hint in ("Conference", "Journal", "Venue"):
        return self._search_and_link_venue(mention)

    # 4. Try author API first, then venue API
    person = self._search_and_link_person(mention)
    if person and person.confidence > 0.7:
        return person

    venue = self._search_and_link_venue(mention)
    if venue and venue.confidence > 0.7:
        return venue

    # 5. Fallback: publication search
    return self._link_from_publication_search(mention)
```

**Add `_search_and_link_person()`:**
```python
def _search_and_link_person(self, mention):
    candidates = self._search_author(mention)
    if candidates:
        best = candidates[0]
        uri = best.get("author-url", "")
        if uri:
            self._cache_entity(mention, uri, "Person")
            return Entity(mention=mention, uri=uri, ...)
    return None
```

**Add `_search_and_link_venue()`:**
```python
def _search_and_link_venue(self, mention):
    candidates = self._search_venue(mention)
    if candidates:
        best = candidates[0]
        uri = best.get("url", "")
        if uri:
            self._cache_entity(mention, uri, "Venue")
            return Entity(mention=mention, uri=uri, ...)
    return None
```

### File: `data/entity_cache.json`

**Keep as-is** - serves as warm cache for performance. New entities are added dynamically.

## What Stays the Same

- `DBLP_KEY_CLASSES` and `DBLP_KEY_PREDICATES` remain (separate concern)
- Schema retriever unchanged
- LLM generator unchanged
- Example retriever unchanged
- Cache file format unchanged

## Benefits

| Benefit | Description |
|---------|-------------|
| No maintenance | No need to manually add new authors/venues |
| Always current | Uses live DBLP data |
| Infinite coverage | Can link any person/venue in DBLP |

## Risks

| Risk | Mitigation |
|------|------------|
| API latency (1-3s per lookup) | Cache results aggressively |
| API rate limits | Add retry logic, local cache fallback |
| API unavailable | Fallback to publication search |
| Wrong entity selected | Return multiple candidates, use LLM to disambiguate |

## Implementation Steps

1. Edit `src/config.py` - remove `KNOWN_PERSON_URIS` and `KNOWN_VENUE_URIS`
2. Edit `src/entity_linker.py` - add `_search_and_link_person()` and `_search_and_link_venue()`
3. Edit `src/entity_linker.py` - update `link()` to use dynamic search
4. Keep `data/entity_cache.json` as warm cache
5. Test with 10 different authors and venues
6. Commit and push

## Testing

```bash
# Test unknown author (not in hardcoded list)
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Papers by Andrew Ng", "execute": true}'

# Test unknown venue (not in hardcoded list)
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Papers at NeurIPS 2023", "execute": true}'

# Check entity cache grew
cat data/entity_cache.json | python -m json.tool
```

## Success Criteria

- [ ] System can link "Andrew Ng" to correct DBLP URI
- [ ] System can link "NeurIPS" to correct DBLP URI
- [ ] Entity cache grows dynamically
- [ ] Existing queries still work
- [ ] Latency < 3s for first lookup, < 100ms for cached
