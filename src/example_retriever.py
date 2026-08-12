"""Example retriever: fetches relevant few-shot examples."""

import json
from pathlib import Path
from typing import List, Optional
from .models import Example
from .config import EXAMPLES_PATH


class ExampleRetriever:
    """Retrieves relevant examples for few-shot prompting."""

    def __init__(self, examples_path: Optional[Path] = None):
        self.examples_path = examples_path or EXAMPLES_PATH
        self.examples: List[Example] = []
        self._load_examples()

    def _load_examples(self):
        """Load examples from JSON file."""
        if not self.examples_path.exists():
            print(f"Warning: Examples file not found at {self.examples_path}")
            self._create_default_examples()
            return

        try:
            with open(self.examples_path) as f:
                data = json.load(f)
            self.examples = [Example(**ex) for ex in data]
        except Exception as e:
            print(f"Error loading examples: {e}")
            self._create_default_examples()

    def _create_default_examples(self):
        """Create default few-shot examples with correct DBLP URIs."""
        self.examples = [
            Example(
                id=1,
                question="Which papers did Michael Stonebraker author?",
                sparql="SELECT ?pub ?title WHERE { ?pub dblp:authoredBy <https://dblp.org/pid/s/MichaelStonebraker> . ?pub dblp:title ?title . }",
                query_type="author_publications",
            ),
            Example(
                id=2,
                question="How many publications does Geoffrey Hinton have?",
                sparql="SELECT (COUNT(?pub) AS ?count) WHERE { ?pub dblp:authoredBy <https://dblp.org/pid/h/GeoffreyHinton> . }",
                query_type="count_publications",
            ),
            Example(
                id=3,
                question="What papers were published at SIGMOD 2023?",
                sparql='SELECT ?pub ?title WHERE { ?pub dblp:publishedInStream <https://dblp.org/streams/conf/sigmod> . ?pub dblp:title ?title . ?pub dblp:yearOfPublication "2023" . }',
                query_type="venue_publications",
            ),
            Example(
                id=4,
                question="Which papers did Donald Knuth author?",
                sparql="SELECT ?pub ?title WHERE { ?pub dblp:authoredBy <https://dblp.org/pid/k/DEKnuth> . ?pub dblp:title ?title . }",
                query_type="author_publications",
            ),
            Example(
                id=5,
                question="Who are the co-authors of Yann LeCun?",
                sparql="SELECT DISTINCT ?coauthor ?name WHERE { ?pub dblp:authoredBy <https://dblp.org/pid/l/LeCunYann> . ?pub dblp:authoredBy ?coauthor . ?coauthor dblp:creatorName ?name . FILTER(?coauthor != <https://dblp.org/pid/l/LeCunYann>) }",
                query_type="co_authors",
            ),
            Example(
                id=6,
                question="List all journals in DBLP",
                sparql="SELECT ?journal ?title WHERE { ?journal a dblp:Journal . ?journal dblp:streamTitle ?title . }",
                query_type="list_venues",
            ),
            Example(
                id=7,
                question="Find all papers about machine learning published in 2024",
                sparql='SELECT ?pub ?title WHERE { ?pub dblp:title ?title . ?pub dblp:yearOfPublication "2024" . FILTER(CONTAINS(LCASE(?title), "machine learning")) }',
                query_type="keyword_search",
            ),
            Example(
                id=8,
                question="What is the DOI of the paper titled 'Attention Is All You Need'?",
                sparql='SELECT ?doi WHERE { ?pub dblp:title "Attention Is All You Need" . ?pub dblp:doi ?doi . }',
                query_type="doi_lookup",
            ),
            Example(
                id=9,
                question="Which papers were published at VLDB 2023?",
                sparql='SELECT ?pub ?title WHERE { ?pub dblp:publishedInStream <https://dblp.org/streams/conf/vldb> . ?pub dblp:title ?title . ?pub dblp:yearOfPublication "2023" . }',
                query_type="venue_publications",
            ),
            Example(
                id=10,
                question="Find papers by author Christos Faloutsos",
                sparql="SELECT ?pub ?title WHERE { ?pub dblp:authoredBy <https://dblp.org/pid/f/ChristosFaloutsos> . ?pub dblp:title ?title . }",
                query_type="author_publications",
            ),
            Example(
                id=11,
                question="List top 5 publications of venue SIGIR",
                sparql="SELECT ?pub ?title ?year WHERE { ?pub dblp:publishedInStream <https://dblp.org/streams/conf/sigir> . ?pub dblp:title ?title . ?pub dblp:yearOfPublication ?year . } ORDER BY DESC(?year) LIMIT 5",
                query_type="venue_top_publications",
            ),
            Example(
                id=12,
                question="How many papers were published at SIGMOD in 2023?",
                sparql='SELECT (COUNT(?pub) AS ?count) WHERE { ?pub dblp:publishedInStream <https://dblp.org/streams/conf/sigmod> . ?pub dblp:yearOfPublication "2023" . }',
                query_type="venue_count",
            ),
        ]
        self._save_examples()

    def _save_examples(self):
        """Save examples to JSON file."""
        self.examples_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.examples_path, "w") as f:
            json.dump([ex.model_dump() for ex in self.examples], f, indent=2)

    def retrieve(self, question: str, k: int = 3) -> List[Example]:
        """Retrieve k most relevant examples for a question."""
        question_lower = question.lower()
        scored = []

        for ex in self.examples:
            score = 0.0
            ex_lower = ex.question.lower()

            question_words = set(question_lower.split())
            ex_words = set(ex_lower.split())
            overlap = len(question_words & ex_words)
            score = overlap / max(len(question_words), 1)

            if "how many" in question_lower and "count" in ex.query_type:
                score += 0.5
            elif "co-author" in question_lower and "co_author" in ex.query_type:
                score += 0.5
            elif "published at" in question_lower and "venue" in ex.query_type:
                score += 0.5
            elif "papers" in question_lower and "author" in ex.query_type:
                score += 0.3
            elif "list" in question_lower and "list" in ex.query_type:
                score += 0.4
            elif "top" in question_lower and "top" in ex.query_type:
                score += 0.4

            scored.append((score, ex))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [ex for _, ex in scored[:k]]

    def format_for_prompt(self, examples: List[Example]) -> str:
        """Format examples for LLM prompt."""
        if not examples:
            return ""

        lines = ["EXAMPLES:", ""]
        for i, ex in enumerate(examples, 1):
            lines.append(f"Example {i}:")
            lines.append(f"Question: {ex.question}")
            lines.append(f"SPARQL:\n{ex.sparql}")
            lines.append("")

        return "\n".join(lines)
