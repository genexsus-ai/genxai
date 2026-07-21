"""Set / Edit Fields tool: build a shaped output object (n8n-style)."""

from typing import Any, Dict, Optional
import logging

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class SetFieldsTool(Tool):
    """Assemble an output object from named fields (n8n's Edit Fields / Set).

    ``fields`` is a name -> value mapping (values are usually ``{{ }}``
    expressions the Studio resolves before this runs). With ``base`` provided
    and ``keep_only_set`` false, the set fields are merged on top of ``base``
    (n8n's "include other input fields"); otherwise only the set fields are
    returned.
    """

    def __init__(self) -> None:
        metadata = ToolMetadata(
            name="data_set_fields",
            description="Build an output object from named fields (rename, reshape, add computed values)",
            category=ToolCategory.DATA,
            tags=["set", "edit-fields", "format", "reshape", "mapping"],
            version="1.0.0",
        )
        parameters = [
            ToolParameter(
                name="fields",
                type="object",
                description="Name -> value mapping for the output object",
                required=True,
            ),
            ToolParameter(
                name="base",
                type="object",
                description="Object to merge the set fields on top of (e.g. the input item)",
                required=False,
            ),
            ToolParameter(
                name="keep_only_set",
                type="boolean",
                description="Output only the set fields (true, default) or merge them onto base (false)",
                required=False,
            ),
        ]
        super().__init__(metadata, parameters)

    async def _execute(
        self,
        fields: Any,
        base: Any = None,
        keep_only_set: bool = True,
    ) -> Dict[str, Any]:
        if not isinstance(fields, dict):
            return {
                "success": False,
                "error": "fields must be an object (name -> value mapping)",
                "result": {},
            }

        result: Dict[str, Any] = {}
        if not keep_only_set and isinstance(base, dict):
            result.update(base)
        result.update(fields)

        logger.info("data_set_fields: produced %d fields", len(result))
        return {"success": True, "result": result, "field_count": len(result)}
