"""Configuration management for the Text-to-SPARQL system."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DBLP_SPARQL_ENDPOINT = os.getenv(
    "DBLP_SPARQL_ENDPOINT", "https://sparql.dblp.org/sparql"
)
DBLP_SEARCH_API = os.getenv("DBLP_SEARCH_API", "https://dblp.org/search/publ/api")
DBLP_AUTHOR_API = os.getenv("DBLP_AUTHOR_API", "https://dblp.org/search/author/api")
DBLP_VENUE_API = os.getenv("DBLP_VENUE_API", "https://dblp.org/search/venue/api")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.4-nano")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "500"))

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
EXAMPLES_PATH = BASE_DIR / os.getenv("EXAMPLES_PATH", "data/examples.json")
SCHEMA_PATH = BASE_DIR / os.getenv("SCHEMA_PATH", "data/schema.ttl")
ENTITY_CACHE_PATH = BASE_DIR / os.getenv("ENTITY_CACHE_PATH", "data/entity_cache.json")

DBLP_PREFIXES = """PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX schema: <https://schema.org/>"""

DBLP_KEY_CLASSES = []

DBLP_KEY_PREDICATES = []

KNOWN_PERSON_URIS = {
    "michael stonebraker": "https://dblp.org/pid/s/MichaelStonebraker",
    "donald knuth": "https://dblp.org/pid/k/DonaldEKnuth",
    "geoffrey hinton": "https://dblp.org/pid/10/3248",
    "yann lecun": "https://dblp.org/pid/l/YannLeCun",
    "christos faloutsos": "https://dblp.org/pid/f/CFaloutsos",
    "jiawei han": "https://dblp.org/pid/h/JiaweiHan",
    "jennifer widom": "https://dblp.org/pid/w/JenniferWidom",
    "hector garcia-molina": "https://dblp.org/pid/g/HGarciaMolina",
}

KNOWN_VENUE_URIS = {
    "sigmod": "https://dblp.org/streams/conf/sigmod",
    "vldb": "https://dblp.org/streams/conf/vldb",
    "sigir": "https://dblp.org/streams/conf/sigir",
    "kdd": "https://dblp.org/streams/conf/kdd",
    "icde": "https://dblp.org/streams/conf/icde",
    "icdt": "https://dblp.org/streams/conf/icdt",
    "edbt": "https://dblp.org/streams/conf/edbt",
    "pods": "https://dblp.org/streams/conf/pods",
    "cidr": "https://dblp.org/streams/conf/cidr",
    "tods": "https://dblp.org/streams/journals/tods",
    "tkde": "https://dblp.org/streams/journals/tkde",
    "debulk": "https://dblp.org/streams/journals/debu",
    "tos": "https://dblp.org/streams/journals/tos",
    "pvldb": "https://dblp.org/streams/journals/pvldb",
}
