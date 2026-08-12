# Implementation Roadmap

## Overview

The project is divided into **5 phases**, each delivering a working increment. A junior developer should complete one phase at a time, testing thoroughly before moving on.

---

## Phase 1: Foundation (Week 1-2)

**Goal**: Basic pipeline that can answer simple queries

### Tasks

| # | Task | Priority | Depends On |
|---|------|----------|------------|
| 1.1 | Set up Python project, virtual env, dependencies | High | - |
| 1.2 | Download and parse DBLP schema (Turtle format) | High | 1.1 |
| 1.3 | Create data models (Question, Entity, SchemaTriple, SPARQLQuery) | High | 1.1 |
| 1.4 | Implement basic entity linking via DBLP Search API | High | 1.3 |
| 1.5 | Create 20 few-shot examples covering common query patterns | High | 1.2 |
| 1.6 | Implement basic LLM generator with OpenAI GPT-5.4-nano | High | 1.3, 1.5 |
| 1.7 | Implement SPARQL syntax validator | High | 1.3 |
| 1.8 | Implement basic executor (SPARQLWrapper to DBLP endpoint) | High | 1.3 |
| 1.9 | Wire up basic pipeline: question → entity linking → generate → validate → execute | High | 1.4-1.8 |
| 1.10 | Test with 10 simple queries (single-triple lookups) | High | 1.9 |

**Deliverable**: CLI tool that answers questions like "Papers by Michael Stonebraker"

---

## Phase 2: Schema Grounding (Week 3-4)

**Goal**: LLM uses correct predicates from DBLP schema

### Tasks

| # | Task | Priority | Depends On |
|---|------|----------|------------|
| 2.1 | Build schema index: load all classes, predicates, domain/range | High | Phase 1 |
| 2.2 | Implement schema retrieval: given question, return relevant predicates | High | 2.1 |
| 2.3 | Add schema context to LLM prompt | High | 2.2 |
| 2.4 | Implement schema-aware validation (check domain/range compatibility) | High | 2.1 |
| 2.5 | Create schema documentation for LLM prompt (clean, concise format) | Medium | 2.1 |
| 2.6 | Test with 20 queries requiring correct predicate selection | High | 2.3, 2.4 |

**Deliverable**: System selects correct predicates (e.g., `authoredBy` vs `createdBy`)

---

## Phase 3: Example Retrieval (Week 5-6)

**Goal**: Dynamic few-shot example selection improves accuracy

### Tasks

| # | Task | Priority | Depends On |
|---|------|----------|------------|
| 3.1 | Expand example corpus to 50+ question→SPARQL pairs | High | Phase 2 |
| 3.2 | Set up ChromaDB (or similar) vector store | High | 3.1 |
| 3.3 | Embed examples using sentence transformers | High | 3.2 |
| 3.4 | Implement semantic search for similar examples | High | 3.3 |
| 3.5 | Integrate retrieved examples into LLM prompt | High | 3.4 |
| 3.6 | Test with 30 diverse queries | High | 3.5 |

**Deliverable**: System retrieves relevant examples dynamically

---

## Phase 4: Validation & Repair (Week 7-8)

**Goal**: System self-corrects failed queries

### Tasks

| # | Task | Priority | Depends On |
|---|------|----------|------------|
| 4.1 | Implement comprehensive SPARQL validator | High | Phase 3 |
| 4.2 | Add result verification (empty results, unexpected patterns) | High | 4.1 |
| 4.3 | Implement repair loop: feed errors back to LLM | High | 4.2 |
| 4.4 | Add retry logic with max attempts | Medium | 4.3 |
| 4.5 | Log all attempts for debugging | Medium | 4.3 |
| 4.6 | Test with 50 queries including edge cases | High | 4.4 |

**Deliverable**: System repairs broken queries automatically

---

## Phase 5: Polish & Evaluation (Week 9-10)

**Goal**: Production-ready system with evaluation metrics

### Tasks

| # | Task | Priority | Depends On |
|---|------|----------|------------|
| 5.1 | Create evaluation dataset (100+ gold-standard queries) | High | Phase 4 |
| 5.2 | Implement metrics: exact match, triple accuracy, execution accuracy | High | 5.1 |
| 5.3 | Add confidence scoring to generated queries | Medium | 5.2 |
| 5.4 | Add logging and error reporting | Medium | 5.2 |
| 5.5 | Create simple web UI (optional) or improve CLI | Low | 5.4 |
| 5.6 | Write documentation and README | High | 5.5 |
| 5.7 | Run full evaluation and document results | High | 5.6 |

**Deliverable**: Complete system with evaluation report

---

## Query Complexity Levels

Implement support for these query types incrementally:

### Level 1: Simple Lookups (Phase 1)
```
"Which papers did X author?"
→ SELECT ?pub WHERE { ?pub dblp:authoredBy <X> }
```

### Level 2: Filtered Queries (Phase 2)
```
"Which papers did X author after 2020?"
→ SELECT ?pub WHERE { ?pub dblp:authoredBy <X> . ?pub dblp:yearOfPublication ?year . FILTER(?year > "2020") }
```

### Level 3: Multi-Hop Queries (Phase 3)
```
"Who are the co-authors of X?"
→ SELECT ?coauthor WHERE { ?pub dblp:authoredBy <X> . ?pub dblp:authoredBy ?coauthor . FILTER(?coauthor != <X>) }
```

### Level 4: Aggregations (Phase 4)
```
"How many papers did X publish?"
→ SELECT (COUNT(?pub) AS ?count) WHERE { ?pub dblp:authoredBy <X> }
```

### Level 5: Complex Queries (Phase 5)
```
"Which venue published the most papers by X in the last 5 years?"
→ SELECT ?venue (COUNT(?pub) AS ?count) WHERE { ... } GROUP BY ?venue ORDER BY DESC(?count) LIMIT 1
```

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Exact SPARQL match | >60% |
| Triple-level accuracy (S/P/O) | >80% |
| Execution accuracy (correct results) | >75% |
| Query success rate (returns results) | >90% |
