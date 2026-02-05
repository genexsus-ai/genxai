"""Regex matcher tool for pattern matching and extraction."""

from typing import Any, Dict, List, Optional
import logging
import re

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class RegexMatcherTool(Tool):
    """Match, search, and extract patterns using regular expressions."""

    def __init__(self) -> None:
        """Initialize regex matcher tool."""
        metadata = ToolMetadata(
            name="regex_matcher",
            description="Match, search, and extract patterns using regular expressions",
            category=ToolCategory.COMPUTATION,
            tags=["regex", "pattern", "matching", "extraction", "search"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="text",
                type="string",
                description="Text to search in",
                required=True,
            ),
            ToolParameter(
                name="pattern",
                type="string",
                description="Regular expression pattern",
                required=True,
            ),
            ToolParameter(
                name="operation",
                type="string",
                description="Operation to perform",
                required=False,
                default="findall",
                enum=["match", "search", "findall", "finditer", "sub", "split"],
            ),
            ToolParameter(
                name="replacement",
                type="string",
                description="Replacement string (for sub operation)",
                required=False,
            ),
            ToolParameter(
                name="flags",
                type="string",
                description="Regex flags (comma-separated: IGNORECASE,MULTILINE,DOTALL)",
                required=False,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        text: str,
        pattern: str,
        operation: str = "findall",
        replacement: Optional[str] = None,
        flags: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute regex operation.

        Args:
            text: Text to search
            pattern: Regex pattern
            operation: Operation to perform
            replacement: Replacement string
            flags: Regex flags

        Returns:
            Dictionary containing operation results
        """
        result: Dict[str, Any] = {
            "operation": operation,
            "pattern": pattern,
            "success": False,
        }

        try:
            # Parse flags
            regex_flags = self._parse_flags(flags)

            # Compile pattern
            compiled_pattern = re.compile(pattern, regex_flags)

            if operation == "match":
                match = compiled_pattern.match(text)
                if match:
                    result.update({
                        "matched": True,
                        "match": match.group(0),
                        "groups": match.groups(),
                        "groupdict": match.groupdict(),
                        "span": match.span(),
                    })
                else:
                    result["matched"] = False

            elif operation == "search":
                match = compiled_pattern.search(text)
                if match:
                    result.update({
                        "found": True,
                        "match": match.group(0),
                        "groups": match.groups(),
                        "groupdict": match.groupdict(),
                        "span": match.span(),
                    })
                else:
                    result["found"] = False

            elif operation == "findall":
                matches = compiled_pattern.findall(text)
                result.update({
                    "matches": matches,
                    "count": len(matches),
                })

            elif operation == "finditer":
                matches = []
                for match in compiled_pattern.finditer(text):
                    matches.append({
                        "match": match.group(0),
                        "groups": match.groups(),
                        "groupdict": match.groupdict(),
                        "span": match.span(),
                    })
                result.update({
                    "matches": matches,
                    "count": len(matches),
                })

            elif operation == "sub":
                if replacement is None:
                    raise ValueError("replacement parameter required for sub operation")
                
                new_text = compiled_pattern.sub(replacement, text)
                result.update({
                    "original_text": text,
                    "new_text": new_text,
                    "replacements_made": text != new_text,
                })

            elif operation == "split":
                parts = compiled_pattern.split(text)
                result.update({
                    "parts": parts,
                    "count": len(parts),
                })

            result["success"] = True

        except re.error as e:
            result["error"] = f"Invalid regex pattern: {str(e)}"
        except Exception as e:
            result["error"] = str(e)

        logger.info(f"Regex {operation} completed: success={result['success']}")
        return result

    def _parse_flags(self, flags: Optional[str]) -> int:
        """Parse regex flags from string.

        Args:
            flags: Comma-separated flag names

        Returns:
            Combined regex flags
        """
        if not flags:
            return 0

        flag_map = {
            "IGNORECASE": re.IGNORECASE,
            "I": re.IGNORECASE,
            "MULTILINE": re.MULTILINE,
            "M": re.MULTILINE,
            "DOTALL": re.DOTALL,
            "S": re.DOTALL,
            "VERBOSE": re.VERBOSE,
            "X": re.VERBOSE,
            "ASCII": re.ASCII,
            "A": re.ASCII,
        }

        combined_flags = 0
        for flag_name in flags.upper().split(","):
            flag_name = flag_name.strip()
            if flag_name in flag_map:
                combined_flags |= flag_map[flag_name]

        return combined_flags
