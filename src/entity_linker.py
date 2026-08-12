"""Entity linker: maps natural language mentions to DBLP URIs."""

import httpx
import re
from typing import List, Optional
from .models import Entity
from .config import DBLP_SEARCH_API


class EntityLinker:
    """Links entity mentions to DBLP URIs via search API."""

    def __init__(self):
        self.client = httpx.Client(timeout=10.0)

    def link(self, mention: str, entity_hint: Optional[str] = None) -> Optional[Entity]:
        """Link a text mention to a DBLP entity."""
        try:
            candidates = self._search_dblp(mention)
            if not candidates:
                return None

            best = self._select_best(candidates, mention, entity_hint)
            return best
        except Exception as e:
            print(f"Entity linking failed for '{mention}': {e}")
            return None

    def link_batch(self, mentions: List[dict]) -> List[Entity]:
        """Link multiple mentions to DBLP entities."""
        results = []
        for item in mentions:
            mention = item.get("text") or item.get("mention", "")
            hint = item.get("type")
            entity = self.link(mention, hint)
            if entity:
                results.append(entity)
        return results

    def _search_dblp(self, query: str) -> List[dict]:
        """Search DBLP for entities matching query."""
        params = {"q": query, "format": "json", "h": 5}
        try:
            response = self.client.get(DBLP_SEARCH_API, params=params)
            response.raise_for_status()
            data = response.json()
            hits = data.get("result", {}).get("hits", {}).get("hit", [])
            if isinstance(hits, dict):
                hits = [hits]
            return hits
        except Exception:
            return []

    def _select_best(
        self, candidates: List[dict], mention: str, hint: Optional[str]
    ) -> Optional[Entity]:
        """Select the best matching candidate."""
        if not candidates:
            return None

        scored = []
        for c in candidates:
            info = c.get("info", {})
            title = info.get("title", "")
            url = info.get("url", "")
            authors = info.get("authors", {}).get("author", [])
            if isinstance(authors, dict):
                authors = [authors]

            score = 0.0
            mention_lower = mention.lower()
            title_lower = title.lower()

            if mention_lower in title_lower:
                score += 0.5

            author_names = [
                a.get("text", a) if isinstance(a, dict) else str(a) for a in authors
            ]
            for name in author_names:
                if mention_lower in name.lower():
                    score += 0.5
                    break

            if hint == "Person" and authors:
                score += 0.2
            elif hint == "Venue" and not authors:
                score += 0.2

            scored.append((score, c, title, url))

        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best, title, url = scored[0]

        entity_type = "Publication"
        if hint:
            entity_type = hint
        elif url and "conf/" in url:
            entity_type = "Conference"
        elif url and "journals/" in url:
            entity_type = "Journal"

        return Entity(
            mention=mention,
            uri=url,
            label=title,
            entity_type=entity_type,
            confidence=min(best_score + 0.5, 1.0),
        )

    def close(self):
        """Close the HTTP client."""
        self.client.close()
