import json
import os
from pathlib import Path
from datetime import datetime

class PatternCatalog:
    """Persistent local storage for verified sovereign coding patterns."""

    def __init__(self, catalog_path: str = ".asd/patterns/catalog.json"):
        self.catalog_path = Path(catalog_path)
        self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_catalog_exists()

    def _ensure_catalog_exists(self):
        if not self.catalog_path.exists():
            with open(self.catalog_path, "w", encoding="utf-8") as f:
                json.dump({"patterns": []}, f, indent=4)

    def add_pattern(self, name: str, description: str, tags: list, content: str):
        """Adds a new pattern to the catalog."""
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        new_pattern = {
            "id": f"pat_{int(datetime.now().timestamp())}",
            "name": name,
            "description": description,
            "tags": tags,
            "content": content,
            "discovered_at": datetime.now().isoformat()
        }

        catalog["patterns"].append(new_pattern)

        with open(self.catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=4)
        
        return new_pattern["id"]

    def search_patterns(self, query: str) -> list:
        """Simple keyword-based search in the catalog."""
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)
        
        query_lower = query.lower()
        results = []
        for pat in catalog.get("patterns", []):
            if query_lower in pat["name"].lower() or \
               query_lower in pat["description"].lower() or \
               any(query_lower in tag.lower() for tag in pat["tags"]):
                results.append(pat)
        
        return results

    def get_all_summaries(self) -> str:
        """Returns a string summary of all patterns for LLM context."""
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)
        
        if not catalog["patterns"]:
            return "No patterns currently in catalog."
            
        summaries = []
        for pat in catalog["patterns"]:
            summaries.append(f"- {pat['name']} ({pat['id']}): {pat['description']} [Tags: {', '.join(pat['tags'])}]")
        
        return "\n".join(summaries)

if __name__ == "__main__":
    cat = PatternCatalog(catalog_path="tests/patterns/catalog.json")
    cat.add_pattern(
        "Hierarchical Planning", 
        "Splits a complex task into a master plan and sub-tasks for agents.", 
        ["orchestration", "planning", "efficiency"],
        "Details of hierarchical planning..."
    )
    print("Catalog Summary:")
    print(cat.get_all_summaries())
    print("\nSearch for 'planning':")
    print(cat.search_patterns("planning"))
