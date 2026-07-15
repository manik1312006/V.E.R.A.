"""Knowledge Manager tool for V.E.R.A. — stores and retrieves research and context."""

import os
import re
from pathlib import Path
from utils.logger import get_logger

logger = get_logger("vera.tools.knowledge")


class KnowledgeManager:
    """Manages the V.E.R.A. Knowledge Base."""

    def __init__(self, base_dir: str = "D:/V.E.R.A/Knowledge"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, action: str, parameters: str) -> str:
        """Execute a knowledge management action.

        Args:
            action: The action to perform.
            parameters: Action parameters.

        Returns:
            Result message string.
        """
        handler = {
            "save_knowledge": self.save_knowledge,
            "search_knowledge": self.search_knowledge,
            "read_knowledge": self.read_knowledge,
            "list_topics": self.list_topics,
        }.get(action)

        if not handler:
            return f"Unknown action: {action}. Available: {list(self._actions().keys())}"

        return handler(parameters)

    def _actions(self) -> dict:
        return {
            "save_knowledge": "Save information to the knowledge base (params: topic:content)",
            "search_knowledge": "Search the knowledge base for a query (params: query)",
            "read_knowledge": "Read a specific knowledge file (params: filename)",
            "list_topics": "List all researched topics in the knowledge base (params: none)",
        }

    def _slugify(self, text: str) -> str:
        """Convert a topic string into a safe filename."""
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', '_', text)
        return text.strip('_')

    def save_knowledge(self, params: str) -> str:
        """Save text content to a Markdown file in a topic subfolder."""
        try:
            parts = params.split(":", 1)
            if len(parts) < 2:
                return "Error: format must be 'topic:content'"
            
            topic = parts[0].strip()
            content = parts[1].strip()
            
            # Save into a dedicated topic subfolder
            topic_dir = self.base_dir / topic.strip().title()
            topic_dir.mkdir(parents=True, exist_ok=True)
            
            filename = self._slugify(topic) + ".md"
            file_path = topic_dir / filename
            
            # If it already exists, append to it, otherwise create new
            mode = "a" if file_path.exists() else "w"
            with open(file_path, mode, encoding="utf-8") as f:
                if mode == "a":
                    f.write("\n\n---\n\n")
                f.write(f"# {topic}\n\n{content}\n")
                
            return f"Successfully saved knowledge about '{topic}' to {topic_dir.name}/{filename}"
        except Exception as e:
            return f"Failed to save knowledge: {e}"

    def search_knowledge(self, query: str) -> str:
        """Search all Markdown files (including subfolders) for the given query."""
        query = query.strip().lower()
        if not query:
            return "Error: query cannot be empty."

        try:
            results = []
            # Recursively search all .md files in all subdirectories
            for file_path in self.base_dir.rglob("*.md"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    relative = file_path.relative_to(self.base_dir)
                    if query in content.lower() or query in file_path.stem.lower():
                        idx = content.lower().find(query)
                        if idx != -1:
                            start = max(0, idx - 100)
                            end = min(len(content), idx + 200)
                            snippet = content[start:end].replace('\n', ' ')
                            results.append(f"- [{relative}]\n  Snippet: ...{snippet}...")
                        else:
                            results.append(f"- [{relative}] (filename match)")
                except Exception as e:
                    logger.error(f"Error reading knowledge file {file_path}: {e}")

            if not results:
                return f"No knowledge found matching '{query}'."

            summary = f"Found {len(results)} matching file(s):\n" + "\n".join(results[:15])
            if len(results) > 15:
                summary += f"\n  ...and {len(results) - 15} more files."
            return summary
        except Exception as e:
            return f"Search failed: {e}"

    def list_topics(self, params: str = "") -> str:
        """List all topics (subfolders) in the Knowledge base."""
        try:
            if not self.base_dir.exists():
                return "The knowledge base is currently empty."
            
            topics = []
            for item in self.base_dir.iterdir():
                if item.is_dir():
                    count = len(list(item.glob("*.md")))
                    topics.append(f"- {item.name} ({count} files)")
            
            if not topics:
                return "The knowledge base is currently empty."
                
            return "Current Knowledge Base Topics:\n" + "\n".join(sorted(topics))
        except Exception as e:
            return f"Failed to list topics: {e}"

    def read_knowledge(self, topic: str) -> str:
        """Read the full contents of a knowledge file."""
        topic = topic.strip()
        filename = self._slugify(topic) + ".md"
        file_path = self.base_dir / filename
        
        if not file_path.exists():
            return f"Error: No knowledge found for topic '{topic}' (Expected file: {filename})."
            
        try:
            content = file_path.read_text(encoding="utf-8")
            from utils.helpers import truncate_text
            # Truncate to avoid context window explosion, but allow large chunks
            return truncate_text(content, max_length=15000)
        except Exception as e:
            return f"Failed to read knowledge file: {e}"
