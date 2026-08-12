# Technology Stack

## Core

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Language | Python | 3.11+ | Main implementation language |
| LLM | OpenAI GPT-5.4-nano | gpt-5.4-nano | SPARQL generation |
| SPARQL Client | SPARQLWrapper | 2.0+ | Query DBLP endpoint |
| Vector Store | ChromaDB | 0.4+ | Example retrieval |
| Embeddings | sentence-transformers | 2.2+ | Semantic search |

## Supporting Libraries

| Library | Purpose |
|---------|---------|
| `rdflib` | Parse DBLP schema (Turtle/RDF) |
| `SPARQLParser` | Validate SPARQL syntax |
| `pydantic` | Data models and validation |
| `httpx` | HTTP client for DBLP Search API |
| `python-dotenv` | Environment variable management |
| `pytest` | Testing framework |
| `rich` | CLI formatting |

## External Services

| Service | URL | Purpose |
|---------|-----|---------|
| DBLP SPARQL Endpoint | https://sparql.dblp.org/sparql | Execute queries |
| DBLP Search API | https://dblp.org/search/publ/api | Entity linking |
| OpenAI API | https://api.openai.com | LLM inference |

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your OpenAI API key
```

## Environment Variables

```env
OPENAI_API_KEY=your_api_key_here
DBLP_SPARQL_ENDPOINT=https://sparql.dblp.org/sparql
DBLP_SEARCH_API=https://dblp.org/search/publ/api
LLM_MODEL=gpt-5.4-nano
LLM_TEMPERATURE=0.0
MAX_RETRIES=3
```

## requirements.txt

```
openai>=1.0.0
SPARQLWrapper>=2.0.0
rdflib>=6.0.0
chromadb>=0.4.0
sentence-transformers>=2.2.0
pydantic>=2.0.0
httpx>=0.24.0
python-dotenv>=1.0.0
pytest>=7.0.0
rich>=13.0.0
```
