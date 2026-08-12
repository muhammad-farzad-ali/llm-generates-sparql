# DBLP Text-to-SPARQL System

A KG-grounded system that converts natural language questions into correct SPARQL queries for the DBLP Computer Science Bibliography.

## Quick Start

```bash
# 1. Clone and setup
cd llm-generates-sparql
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env with your OpenAI API key

# 4. Run
python -m src.pipeline "Which papers did Michael Stonebraker author?"
```

## Documentation

| Document | Location |
|----------|----------|
| Architecture | [docs/architecture.md](docs/architecture.md) |
| Roadmap | [specs/roadmap.md](specs/roadmap.md) |
| Tech Stack | [docs/tech-stack.md](docs/tech-stack.md) |
| Coding Standards | [docs/coding-standards.md](docs/coding-standards.md) |
| Glossary | [docs/glossary.md](docs/glossary.md) |

## Feature Specs

| Component | Spec |
|-----------|------|
| Entity Linking | [specs/features/entity-linking.md](specs/features/entity-linking.md) |
| Schema Retrieval | [specs/features/schema-retrieval.md](specs/features/schema-retrieval.md) |
| Example Retrieval | [specs/features/example-retrieval.md](specs/features/example-retrieval.md) |
| LLM Generator | [specs/features/llm-generator.md](specs/features/llm-generator.md) |
| Validator | [specs/features/validator.md](specs/features/validator.md) |
| Executor | [specs/features/executor.md](specs/features/executor.md) |

## Project Status

See [memory/current-state.md](memory/current-state.md) for current progress.

## Architecture

```
Question → Entity Linking → Schema Retrieval → Example Retrieval → LLM → Validator → Executor → Results
```

## Tech Stack

- Python 3.11+
- OpenAI GPT-5.4-nano
- ChromaDB (vector store)
- SPARQLWrapper (DBLP endpoint)
- Pydantic (data models)

## License

Internal research project.
