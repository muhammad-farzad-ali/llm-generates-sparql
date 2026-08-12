"""Entity linker: maps natural language mentions to DBLP URIs."""

import json
import httpx
from pathlib import Path
from typing import List, Optional
from .models import Entity
from .config import (
    DBLP_SEARCH_API,
    DBLP_AUTHOR_API,
    DBLP_VENUE_API,
    KNOWN_PERSON_URIS,
    KNOWN_VENUE_URIS,
    ENTITY_CACHE_PATH,
)


class EntityLinker:
    """Links entity mentions to DBLP URIs via search API."""

    def __init__(self):
        self.client = httpx.Client(timeout=10.0)
        self.entity_cache = self._load_cache()

    def _load_cache(self) -> dict:
        """Load entity cache from file."""
        if ENTITY_CACHE_PATH.exists():
            try:
                with open(ENTITY_CACHE_PATH) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_cache(self):
        """Save entity cache to file."""
        try:
            ENTITY_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(ENTITY_CACHE_PATH, "w") as f:
                json.dump(self.entity_cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save entity cache: {e}")

    def link(self, mention: str, entity_hint: Optional[str] = None) -> Optional[Entity]:
        """Link a text mention to a DBLP entity."""
        mention_lower = mention.lower().strip()

        if mention_lower in self.entity_cache:
            cached = self.entity_cache[mention_lower]
            return Entity(
                mention=mention,
                uri=cached["uri"],
                label=cached.get("label", mention),
                entity_type=cached["type"],
                confidence=1.0,
            )

        if entity_hint == "Person" or mention_lower in KNOWN_PERSON_URIS:
            return self._link_person(mention)
        elif (
            entity_hint in ("Conference", "Journal", "Venue")
            or mention_lower in KNOWN_VENUE_URIS
        ):
            return self._link_venue(mention, entity_hint or "Venue")
        else:
            return self._link_from_publication_search(mention)

    def _link_person(self, mention: str) -> Optional[Entity]:
        """Link a person mention to DBLP person URI."""
        mention_lower = mention.lower().strip()

        if mention_lower in KNOWN_PERSON_URIS:
            uri = KNOWN_PERSON_URIS[mention_lower]
            self._cache_entity(mention, uri, "Person")
            return Entity(
                mention=mention,
                uri=uri,
                label=mention,
                entity_type="Person",
                confidence=1.0,
            )

        candidates = self._search_author(mention)
        if candidates:
            best = candidates[0]
            uri = best.get("author-url", "")
            name = best.get("author", mention)
            if uri:
                self._cache_entity(mention, uri, "Person")
                return Entity(
                    mention=mention,
                    uri=uri,
                    label=name,
                    entity_type="Person",
                    confidence=0.9,
                )

        pid = self._name_to_pid(mention)
        uri = f"https://dblp.org/pid/{pid}"
        return Entity(
            mention=mention,
            uri=uri,
            label=mention,
            entity_type="Person",
            confidence=0.4,
        )

    def _link_venue(self, mention: str, hint: str) -> Optional[Entity]:
        """Link a venue mention to DBLP venue URI."""
        mention_lower = mention.lower().strip()

        if mention_lower in KNOWN_VENUE_URIS:
            uri = KNOWN_VENUE_URIS[mention_lower]
            self._cache_entity(
                mention, uri, "Conference" if "/conf/" in uri else "Journal"
            )
            return Entity(
                mention=mention,
                uri=uri,
                label=mention,
                entity_type="Conference" if "/conf/" in uri else "Journal",
                confidence=1.0,
            )

        candidates = self._search_venue(mention)
        if candidates:
            best = candidates[0]
            uri = best.get("url", "")
            name = best.get("venue", mention)
            if uri:
                entity_type = "Conference" if "/conf/" in uri else "Journal"
                self._cache_entity(mention, uri, entity_type)
                return Entity(
                    mention=mention,
                    uri=uri,
                    label=name,
                    entity_type=entity_type,
                    confidence=0.9,
                )

        vid = mention_lower.replace(" ", "").replace("-", "")
        return Entity(
            mention=mention,
            uri=f"https://dblp.org/conf/{vid}",
            label=mention,
            entity_type=hint,
            confidence=0.4,
        )

    def _link_from_publication_search(self, mention: str) -> Optional[Entity]:
        """Try to find entity from publication search results."""
        candidates = self._search_publications(mention)
        if candidates:
            for c in candidates:
                info = c.get("info", {})
                authors = info.get("authors", {}).get("author", [])
                if isinstance(authors, dict):
                    authors = [authors]

                for author in authors:
                    if isinstance(author, dict):
                        author_name = author.get("text", "")
                        author_url = author.get("author-url", "")
                    else:
                        author_name = str(author)
                        author_url = ""

                    if mention.lower() in author_name.lower():
                        if author_url and "/pid/" in author_url:
                            self._cache_entity(mention, author_url, "Person")
                            return Entity(
                                mention=mention,
                                uri=author_url,
                                label=author_name,
                                entity_type="Person",
                                confidence=0.8,
                            )

        return None

    def _search_author(self, query: str) -> List[dict]:
        """Search DBLP for authors."""
        params = {"q": query, "format": "json", "h": 5}
        try:
            response = self.client.get(DBLP_AUTHOR_API, params=params)
            response.raise_for_status()
            data = response.json()
            hits = data.get("result", {}).get("hits", {}).get("hit", [])
            if isinstance(hits, dict):
                hits = [hits]
            return hits
        except Exception:
            return []

    def _search_venue(self, query: str) -> List[dict]:
        """Search DBLP for venues."""
        params = {"q": query, "format": "json", "h": 5}
        try:
            response = self.client.get(DBLP_VENUE_API, params=params)
            response.raise_for_status()
            data = response.json()
            hits = data.get("result", {}).get("hits", {}).get("hit", [])
            if isinstance(hits, dict):
                hits = [hits]
            return hits
        except Exception:
            return []

    def _search_publications(self, query: str) -> List[dict]:
        """Search DBLP for publications."""
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

    def _name_to_pid(self, name: str) -> str:
        """Convert a name to a DBLP pid format."""
        parts = name.strip().split()
        if len(parts) < 2:
            return name.lower().replace(" ", "")
        last = parts[-1]
        first_initial = parts[0][0]
        return f"{last[0].lower()}/{last}{first_initial}"

    def _cache_entity(self, mention: str, uri: str, entity_type: str):
        """Cache an entity mapping."""
        self.entity_cache[mention.lower().strip()] = {
            "uri": uri,
            "type": entity_type,
            "label": mention,
        }
        self._save_cache()

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

    def close(self):
        """Close the HTTP client."""
        self.client.close()
