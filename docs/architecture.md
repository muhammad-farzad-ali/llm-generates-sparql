# Architecture Overview

## System Goal

Build a **KG-grounded Text-to-SPARQL system** that converts natural language questions into correct SPARQL queries for the DBLP Knowledge Graph.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                           │
│                   (CLI or simple web UI)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Query Pipeline                             │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Entity   │→ │ Schema   │→ │ Example  │→ │   LLM    │       │
│  │ Linking  │  │ Retrieval│  │ Retrieval│  │ Generator│       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│       │                            │              │             │
│       ▼                            ▼              ▼             │
│  ┌──────────┐              ┌──────────┐  ┌──────────┐          │
│  │  DBLP    │              │  Vector  │  │   SPARQL │          │
│  │  Search  │              │   Store  │  │ Validator│          │
│  └──────────┘              └──────────┘  └──────────┘          │
│                                              │                 │
│                                              ▼                 │
│                                       ┌──────────┐             │
│                                       │ Executor │             │
│                                       │ + Repair │             │
│                                       └──────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DBLP SPARQL Endpoint                         │
│               https://sparql.dblp.org/sparql                   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Entity Linking Module
- **Purpose**: Map natural language entity mentions to DBLP URIs
- **Input**: "Michael Stonebraker"
- **Output**: `<https://dblp.org/pid/s/MichaelStonebraker>`
- **Method**: DBLP Search API + LLM disambiguation

### 2. Schema Retrieval Module
- **Purpose**: Retrieve relevant schema triples for the query
- **Input**: Question + linked entities
- **Output**: Relevant classes, predicates, domain/range info
- **Method**: Pre-built schema index with semantic search

### 3. Example Retrieval Module
- **Purpose**: Find similar past queries for few-shot prompting
- **Input**: Natural language question
- **Output**: 3-5 similar question→SPARQL pairs
- **Method**: Vector similarity search on example corpus

### 4. LLM Generator
- **Purpose**: Generate SPARQL from grounded context
- **Input**: Question + schema + entities + examples
- **Output**: SPARQL query
- **Method**: OpenAI GPT-5.4-nano with structured prompting

### 5. SPARQL Validator
- **Purpose**: Verify query correctness before execution
- **Input**: Generated SPARQL
- **Output**: Valid/Invalid + error details
- **Checks**: Syntax, schema compliance, type compatibility

### 6. Executor & Repair Module
- **Purpose**: Execute query and handle failures
- **Input**: Validated SPARQL
- **Output**: Results or repaired query
- **Method**: Execute against DBLP endpoint, LLM-based repair on failure

## Data Flow

```
Question: "Which papers did Michael Stonebraker publish at SIGMOD?"

Step 1: Entity Linking
  "Michael Stonebraker" → <https://dblp.org/pid/s/MichaelStonebraker>
  "SIGMOD" → <https://dblp.org/conf/sigmod>

Step 2: Schema Retrieval
  Relevant predicates:
  - dblp:authoredBy (Publication → Person)
  - dblp:publishedInStream (Publication → Stream)
  - dblp:title (Publication → string)

Step 3: Example Retrieval
  Similar: "Papers by John Doe at VLDB" → SELECT ?pub WHERE { ... }

Step 4: LLM Generation
  SELECT ?pub ?title
  WHERE {
    ?pub dblp:authoredBy <https://dblp.org/pid/s/MichaelStonebraker> .
    ?pub dblp:publishedInStream <https://dblp.org/conf/sigmod> .
    ?pub dblp:title ?title .
  }

Step 5: Validation
  ✓ Valid syntax
  ✓ Valid predicates
  ✓ Compatible types

Step 6: Execution
  → Returns list of papers
```

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM | OpenAI GPT-5.4-nano | Low cost ($0.10/1M input), fast, adequate for SPARQL |
| Language | Python | Rich ecosystem for NLP/LLM, SPARQL libraries |
| Vector Store | ChromaDB | Lightweight, local, no external service needed |
| SPARQL Client | SPARQLWrapper | Standard Python SPARQL client |
| Validation | Custom + SPARQLParser | Schema validation is custom, syntax uses parser |

## File Structure

```
llm-generates-sparql/
├── docs/
│   ├── architecture.md          # This file
│   ├── tech-stack.md            # Technology choices
│   ├── coding-standards.md      # Code style guide
│   └── decisions/               # Architecture Decision Records
│
├── specs/
│   ├── roadmap.md               # Implementation roadmap
│   └── features/
│       ├── entity-linking.md    # Entity linking spec
│       ├── schema-retrieval.md  # Schema retrieval spec
│       ├── example-retrieval.md # Example retrieval spec
│       ├── llm-generator.md     # LLM generation spec
│       ├── validator.md         # SPARQL validation spec
│       └── executor.md          # Execution & repair spec
│
├── memory/
│   ├── current-state.md         # Project status
│   └── lessons-learned.md       # Insights during development
│
├── src/
│   ├── __init__.py
│   ├── pipeline.py              # Main orchestrator
│   ├── entity_linker.py         # Entity linking
│   ├── schema_retriever.py      # Schema retrieval
│   ├── example_retriever.py     # Example retrieval
│   ├── llm_generator.py         # LLM SPARQL generation
│   ├── validator.py             # SPARQL validation
│   ├── executor.py              # Query execution
│   ├── models.py                # Data models
│   └── config.py                # Configuration
│
├── data/
│   ├── schema.ttl               # DBLP schema (Turtle)
│   ├── examples.json            # Few-shot examples
│   └── entities/                # Entity index
│
├── tests/
│   ├── test_entity_linker.py
│   ├── test_validator.py
│   └── test_pipeline.py
│
├── requirements.txt
└── README.md
```
