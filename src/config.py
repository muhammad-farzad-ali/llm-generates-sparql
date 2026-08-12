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

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.4-nano")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "500"))

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
EXAMPLES_PATH = BASE_DIR / os.getenv("EXAMPLES_PATH", "data/examples.json")
SCHEMA_PATH = BASE_DIR / os.getenv("SCHEMA_PATH", "data/schema.ttl")

DBLP_PREFIXES = """PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX schema: <https://schema.org/>"""

DBLP_KEY_PREDICATES = [
    "authoredBy",
    "authorOf",
    "title",
    "yearOfPublication",
    "publishedInStream",
    "publishedInJournal",
    "publishedIn",
    "doi",
    "creatorName",
    "homepage",
    "coAuthorWith",
]

DBLP_KEY_CLASSES = [
    "Person",
    "Publication",
    "Article",
    "Inproceedings",
    "Book",
    "Conference",
    "Journal",
    "Stream",
]
