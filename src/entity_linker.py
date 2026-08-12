"""Entity linker: maps natural language mentions to DBLP URIs."""

import re
import httpx
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
                return self._fallback_link(mention, entity_hint)

            return self._select_best(candidates, mention, entity_hint)
        except Exception as e:
            print(f"Entity linking failed for '{mention}': {e}")
            return self._fallback_link(mention, entity_hint)

    def _fallback_link(
        self, mention: str, entity_hint: Optional[str]
    ) -> Optional[Entity]:
        """Create a fallback entity with constructed URI."""
        if entity_hint == "Person":
            pid = self._name_to_pid(mention)
            return Entity(
                mention=mention,
                uri=f"https://dblp.org/pid/{pid}",
                label=mention,
                entity_type="Person",
                confidence=0.5,
            )
        elif entity_hint in ("Conference", "Journal", "Venue"):
            vid = mention.lower().replace(" ", "").replace("-", "")
            return Entity(
                mention=mention,
                uri=f"https://dblp.org/conf/{vid}",
                label=mention,
                entity_type=entity_hint,
                confidence=0.5,
            )
        return None

    def _name_to_pid(self, name: str) -> str:
        """Convert a name to a DBLP pid format."""
        parts = name.strip().split()
        if len(parts) < 2:
            return name.lower().replace(" ", "")
        last = parts[-1]
        first_initial = parts[0][0]
        return f"{last[0].lower()}/{last}{first_initial}"

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
        params = {"q": query, "format": "json", "h": 10}
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

        mention_lower = mention.lower().strip()

        person_candidates = []
        venue_candidates = []
        pub_candidates = []

        for c in candidates:
            info = c.get("info", {})
            url = info.get("url", "")
            authors = info.get("authors", {}).get("author", [])
            if isinstance(authors, dict):
                authors = [authors]

            if "/pid/" in url:
                person_candidates.append((c, info, url, authors))
            elif "/conf/" in url or "/journals/" in url:
                venue_candidates.append((c, info, url, authors))
            else:
                pub_candidates.append((c, info, url, authors))

        if hint == "Person" and person_candidates:
            return self._score_person(person_candidates, mention)
        elif hint in ("Conference", "Journal", "Venue") and venue_candidates:
            return self._score_venue(venue_candidates, mention, hint)
        elif person_candidates:
            return self._score_person(person_candidates, mention)
        elif venue_candidates:
            return self._score_venue(venue_candidates, mention, hint or "Venue")

        if pub_candidates:
            return self._score_publication(pub_candidates, mention)

        return None

    def _score_person(self, candidates: List[tuple], mention: str) -> Optional[Entity]:
        """Score and select best person candidate."""
        mention_lower = mention.lower()
        best_score = -1
        best_entity = None

        for c, info, url, authors in candidates:
            score = 0.0
            author_names = [
                a.get("text", str(a)) if isinstance(a, dict) else str(a)
                for a in authors
            ]

            for name in author_names:
                if mention_lower in name.lower() or name.lower() in mention_lower:
                    score += 1.0
                    break

            if score > best_score:
                best_score = score
                pid = url.split("/pid/")[-1] if "/pid/" in url else ""
                label = author_names[0] if author_names else mention
                best_entity = Entity(
                    mention=mention,
                    uri=f"https://dblp.org/pid/{pid}",
                    label=label,
                    entity_type="Person",
                    confidence=min(0.7 + score * 0.3, 1.0),
                )

        return best_entity

    def _score_venue(
        self, candidates: List[tuple], mention: str, hint: str
    ) -> Optional[Entity]:
        """Score and select best venue candidate."""
        mention_lower = mention.lower()
        best_score = -1
        best_entity = None

        for c, info, url, authors in candidates:
            score = 0.0
            title = info.get("title", "").lower()

            if mention_lower in title:
                score += 1.0
            elif mention_lower.replace(" ", "") in url.lower():
                score += 0.8

            if score > best_score:
                best_score = score
                if "/conf/" in url:
                    venue_id = url.split("/conf/")[-1].rstrip("/")
                    entity_type = "Conference"
                elif "/journals/" in url:
                    venue_id = url.split("/journals/")[-1].rstrip("/")
                    entity_type = "Journal"
                else:
                    venue_id = mention.lower().replace(" ", "")
                    entity_type = hint

                best_entity = Entity(
                    mention=mention,
                    uri=f"https://dblp.org/{'conf' if entity_type == 'Conference' else 'journals'}/{venue_id}",
                    label=info.get("title", mention),
                    entity_type=entity_type,
                    confidence=min(0.7 + score * 0.3, 1.0),
                )

        return best_entity

    def _score_publication(
        self, candidates: List[tuple], mention: str
    ) -> Optional[Entity]:
        """Score and select best publication candidate."""
        mention_lower = mention.lower()
        best_score = -1
        best_entity = None

        for c, info, url, authors in candidates:
            score = 0.0
            title = info.get("title", "").lower()

            if mention_lower in title:
                score += 1.0

            if score > best_score:
                best_score = score
                best_entity = Entity(
                    mention=mention,
                    uri=url,
                    label=info.get("title", mention),
                    entity_type="Publication",
                    confidence=min(0.5 + score * 0.5, 1.0),
                )

        return best_entity

    def close(self):
        """Close the HTTP client."""
        self.client.close()
