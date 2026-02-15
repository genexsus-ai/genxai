"""Tool registry for managing available tools."""

from typing import Any, Dict, List, Optional
import logging

from genxai.tools.base import Tool, ToolCategory

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for all tools."""

    SCHEMA_VERSION = "1.0"
    _instance: Optional["ToolRegistry"] = None
    _tools: Dict[str, Tool] = {}

    def __new__(cls) -> "ToolRegistry":
        """Singleton pattern for tool registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, tool: Tool) -> None:
        """Register a new tool.

        Args:
            tool: Tool to register
        """
        name = tool.metadata.name
        existing = cls._tools.get(name)
        if existing is not None:
            # Avoid noisy warnings when the same tool class is registered multiple
            # times due to import side-effects (common in CLIs).
            if type(existing) is type(tool):
                logger.debug(
                    "Tool %s already registered (%s); skipping duplicate registration",
                    name,
                    type(tool).__name__,
                )
                return
            logger.warning(
                "Tool %s already registered (%s -> %s), overwriting",
                name,
                type(existing).__name__,
                type(tool).__name__,
            )

        cls._tools[name] = tool
        logger.info("Registered tool: %s", name)

    @classmethod
    def unregister(cls, name: str) -> None:
        """Unregister a tool.

        Args:
            name: Tool name to unregister
        """
        if name in cls._tools:
            del cls._tools[name]
            logger.info(f"Unregistered tool: {name}")
        else:
            logger.warning(f"Tool {name} not found in registry")

    @classmethod
    def get(cls, name: str) -> Optional[Tool]:
        """Get tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return cls._tools.get(name)

    @classmethod
    def list_all(cls) -> List[Tool]:
        """List all registered tools.

        Returns:
            List of all tools
        """
        return list(cls._tools.values())

    @classmethod
    def search(
        cls, query: str, category: Optional[ToolCategory] = None
    ) -> List[Tool]:
        """Search tools by query and category.

        Args:
            query: Search query (searches name, description, tags)
            category: Optional category filter

        Returns:
            List of matching tools
        """
        results = []
        query_lower = query.lower()

        for tool in cls._tools.values():
            # Filter by category
            if category and tool.metadata.category != category:
                continue

            # Search in name, description, and tags
            if (
                query_lower in tool.metadata.name.lower()
                or query_lower in tool.metadata.description.lower()
                or any(query_lower in tag.lower() for tag in tool.metadata.tags)
            ):
                results.append(tool)

        logger.debug(f"Found {len(results)} tools matching '{query}'")
        return results

    @classmethod
    def list_categories(cls) -> List[ToolCategory]:
        """List all tool categories in use.

        Returns:
            List of categories
        """
        return list(set(tool.metadata.category for tool in cls._tools.values()))

    @classmethod
    def get_by_category(cls, category: ToolCategory) -> List[Tool]:
        """Get all tools in a category.

        Args:
            category: Tool category

        Returns:
            List of tools in category
        """
        return [
            tool for tool in cls._tools.values() if tool.metadata.category == category
        ]

    @classmethod
    def get_by_tag(cls, tag: str) -> List[Tool]:
        """Get all tools with a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            List of tools with tag
        """
        return [
            tool
            for tool in cls._tools.values()
            if tag.lower() in [t.lower() for t in tool.metadata.tags]
        ]

    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools."""
        cls._tools.clear()
        logger.info("Cleared all tools from registry")

    @classmethod
    def export_schema_bundle(cls, category: Optional[ToolCategory] = None) -> Dict[str, Any]:
        """Export a consolidated schema bundle for all registered tools.

        Returns:
            Dictionary containing tool schemas and metadata.
        """
        tools = [
            tool.get_schema()
            for tool in cls._tools.values()
            if not category or tool.metadata.category == category
        ]
        categories = {}
        for tool in cls._tools.values():
            if category and tool.metadata.category != category:
                continue
            category = tool.metadata.category.value
            categories[category] = categories.get(category, 0) + 1

        return {
            "schema_version": cls.SCHEMA_VERSION,
            "tool_count": len(tools),
            "categories": categories,
            "tools": tools,
        }

    @classmethod
    def export_schema_bundle_to_file(
        cls,
        path: str,
        category: Optional[ToolCategory] = None,
    ) -> str:
        """Export tool schemas to a JSON file.

        Args:
            path: Output file path

        Returns:
            Absolute path to the exported file
        """
        from pathlib import Path

        output_path = Path(path)
        bundle = cls.export_schema_bundle(category=category)
        if output_path.suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml
            except ImportError as exc:
                raise ImportError(
                    "PyYAML is required for YAML output. Install with: pip install PyYAML"
                ) from exc
            output_path.write_text(yaml.safe_dump(bundle, sort_keys=False))
        else:
            import json

            output_path.write_text(json.dumps(bundle, indent=2))
        return str(output_path.resolve())

    @classmethod
    def get_stats(cls) -> Dict[str, any]:
        """Get registry statistics.

        Returns:
            Statistics dictionary
        """
        category_counts = {}
        for tool in cls._tools.values():
            category = tool.metadata.category.value
            category_counts[category] = category_counts.get(category, 0) + 1

        return {
            "total_tools": len(cls._tools),
            "categories": category_counts,
            "tool_names": list(cls._tools.keys()),
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"ToolRegistry(tools={len(self._tools)})"
