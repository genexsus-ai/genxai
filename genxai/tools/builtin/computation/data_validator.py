"""Data validator tool for validating data against schemas and rules."""

from typing import Any, Dict, List, Optional
import logging
import re

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class DataValidatorTool(Tool):
    """Validate data against schemas, patterns, and custom rules."""

    def __init__(self) -> None:
        """Initialize data validator tool."""
        metadata = ToolMetadata(
            name="data_validator",
            description="Validate data types, formats, ranges, and patterns",
            category=ToolCategory.COMPUTATION,
            tags=["validation", "schema", "data", "rules", "constraints"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="data",
                type="string",
                description="Data to validate",
                required=True,
            ),
            ToolParameter(
                name="validation_type",
                type="string",
                description="Type of validation to perform",
                required=True,
                enum=[
                    "email",
                    "url",
                    "phone",
                    "ip",
                    "date",
                    "number",
                    "json",
                    "custom_regex",
                ],
            ),
            ToolParameter(
                name="custom_pattern",
                type="string",
                description="Custom regex pattern (for custom_regex type)",
                required=False,
            ),
            ToolParameter(
                name="min_value",
                type="number",
                description="Minimum value (for number validation)",
                required=False,
            ),
            ToolParameter(
                name="max_value",
                type="number",
                description="Maximum value (for number validation)",
                required=False,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        data: str,
        validation_type: str,
        custom_pattern: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Execute data validation.

        Args:
            data: Data to validate
            validation_type: Type of validation
            custom_pattern: Custom regex pattern
            min_value: Minimum value
            max_value: Maximum value

        Returns:
            Dictionary containing validation results
        """
        result: Dict[str, Any] = {
            "validation_type": validation_type,
            "data": data,
            "valid": False,
        }

        try:
            if validation_type == "email":
                result.update(self._validate_email(data))
            
            elif validation_type == "url":
                result.update(self._validate_url(data))
            
            elif validation_type == "phone":
                result.update(self._validate_phone(data))
            
            elif validation_type == "ip":
                result.update(self._validate_ip(data))
            
            elif validation_type == "date":
                result.update(self._validate_date(data))
            
            elif validation_type == "number":
                result.update(self._validate_number(data, min_value, max_value))
            
            elif validation_type == "custom_regex":
                if not custom_pattern:
                    raise ValueError("custom_pattern required for custom_regex validation")
                result.update(self._validate_custom_regex(data, custom_pattern))

            elif validation_type == "json":
                result.update(self._validate_json(data))

        except Exception as e:
            result["error"] = str(e)

        logger.info(
            f"Data validation ({validation_type}) completed: valid={result.get('valid', False)}"
        )
        return result

    def _validate_json(self, data: str) -> Dict[str, Any]:
        """Validate JSON."""
        import json

        try:
            parsed = json.loads(data)
            return {
                "valid": True,
                "format": "json",
                "parsed_type": type(parsed).__name__,
            }
        except Exception as e:
            return {
                "valid": False,
                "format": "json",
                "error": f"Invalid JSON: {e}",
            }

    def _validate_email(self, data: str) -> Dict[str, Any]:
        """Validate email address."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        match = re.match(pattern, data)
        return {
            "valid": bool(match),
            "format": "email",
        }

    def _validate_url(self, data: str) -> Dict[str, Any]:
        """Validate URL."""
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        match = re.match(pattern, data, re.IGNORECASE)
        return {
            "valid": bool(match),
            "format": "url",
        }

    def _validate_phone(self, data: str) -> Dict[str, Any]:
        """Validate phone number."""
        # Remove common separators
        cleaned = re.sub(r'[\s\-\(\)\.]', '', data)
        # Check if it's all digits and reasonable length
        valid = cleaned.isdigit() and 10 <= len(cleaned) <= 15
        return {
            "valid": valid,
            "format": "phone",
            "cleaned": cleaned if valid else None,
        }

    def _validate_ip(self, data: str) -> Dict[str, Any]:
        """Validate IP address (IPv4)."""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, data):
            return {"valid": False, "format": "ipv4"}
        
        # Check each octet is 0-255
        octets = data.split('.')
        valid = all(0 <= int(octet) <= 255 for octet in octets)
        
        return {
            "valid": valid,
            "format": "ipv4",
            "octets": octets if valid else None,
        }

    def _validate_date(self, data: str) -> Dict[str, Any]:
        """Validate date format."""
        # Common date patterns
        patterns = [
            (r'^\d{4}-\d{2}-\d{2}$', 'YYYY-MM-DD'),
            (r'^\d{2}/\d{2}/\d{4}$', 'MM/DD/YYYY'),
            (r'^\d{2}-\d{2}-\d{4}$', 'DD-MM-YYYY'),
        ]
        
        for pattern, format_name in patterns:
            if re.match(pattern, data):
                return {
                    "valid": True,
                    "format": format_name,
                }
        
        return {
            "valid": False,
            "format": "unknown",
        }

    def _validate_number(
        self, data: str, min_value: Optional[float], max_value: Optional[float]
    ) -> Dict[str, Any]:
        """Validate number and range."""
        try:
            number = float(data)
            
            # Check range
            in_range = True
            if min_value is not None and number < min_value:
                in_range = False
            if max_value is not None and number > max_value:
                in_range = False
            
            return {
                "valid": in_range,
                "format": "number",
                "value": number,
                "in_range": in_range,
                "is_integer": number.is_integer(),
            }
        except ValueError:
            return {
                "valid": False,
                "format": "number",
                "error": "Not a valid number",
            }

    def _validate_custom_regex(self, data: str, pattern: str) -> Dict[str, Any]:
        """Validate against custom regex pattern."""
        try:
            match = re.match(pattern, data)
            return {
                "valid": bool(match),
                "format": "custom_regex",
                "pattern": pattern,
                "matched": match.group(0) if match else None,
            }
        except re.error as e:
            return {
                "valid": False,
                "format": "custom_regex",
                "error": f"Invalid regex pattern: {str(e)}",
            }
