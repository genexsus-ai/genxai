"""Hash generator tool for creating cryptographic hashes."""

from typing import Any, Dict
import logging
import hashlib
import hmac
import base64

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class HashGeneratorTool(Tool):
    """Generate cryptographic hashes and HMACs."""

    def __init__(self) -> None:
        """Initialize hash generator tool."""
        metadata = ToolMetadata(
            name="hash_generator",
            description="Generate cryptographic hashes (MD5, SHA1, SHA256, SHA512) and HMACs",
            category=ToolCategory.COMPUTATION,
            tags=["hash", "crypto", "md5", "sha", "hmac", "checksum"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="data",
                type="string",
                description="Data to hash",
                required=True,
            ),
            ToolParameter(
                name="algorithm",
                type="string",
                description="Hash algorithm",
                required=True,
                enum=["md5", "sha1", "sha256", "sha512", "sha3_256", "sha3_512", "blake2b", "blake2s"],
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="Input data encoding",
                required=False,
                default="utf-8",
                enum=["utf-8", "ascii", "latin-1"],
            ),
            ToolParameter(
                name="output_format",
                type="string",
                description="Output format",
                required=False,
                default="hex",
                enum=["hex", "base64"],
            ),
            ToolParameter(
                name="hmac_key",
                type="string",
                description="HMAC key (if provided, generates HMAC instead of hash)",
                required=False,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        data: str,
        algorithm: str,
        encoding: str = "utf-8",
        output_format: str = "hex",
        hmac_key: str = None,
    ) -> Dict[str, Any]:
        """Execute hash generation.

        Args:
            data: Data to hash
            algorithm: Hash algorithm
            encoding: Input encoding
            output_format: Output format
            hmac_key: HMAC key (optional)

        Returns:
            Dictionary containing hash results
        """
        result: Dict[str, Any] = {
            "algorithm": algorithm,
            "output_format": output_format,
            "success": False,
        }

        try:
            # Encode data
            data_bytes = data.encode(encoding)

            # Generate hash or HMAC
            if hmac_key:
                # Generate HMAC
                key_bytes = hmac_key.encode(encoding)
                hash_obj = hmac.new(key_bytes, data_bytes, algorithm)
                result["type"] = "hmac"
            else:
                # Generate regular hash
                hash_obj = hashlib.new(algorithm, data_bytes)
                result["type"] = "hash"

            # Format output
            if output_format == "hex":
                hash_value = hash_obj.hexdigest()
            elif output_format == "base64":
                hash_value = base64.b64encode(hash_obj.digest()).decode("ascii")
            else:
                hash_value = hash_obj.hexdigest()

            result.update({
                "hash": hash_value,
                "length": len(hash_value),
                "input_length": len(data),
                "success": True,
            })

        except ValueError as e:
            result["error"] = f"Invalid algorithm: {str(e)}"
        except Exception as e:
            result["error"] = str(e)

        logger.info(f"Hash generation ({algorithm}) completed: success={result['success']}")
        return result
