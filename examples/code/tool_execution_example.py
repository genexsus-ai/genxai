"""Execute a built-in tool without an LLM."""

import asyncio

from genxai.tools.registry import ToolRegistry
from genxai.tools.builtin import *  # noqa: F403 - auto-register tools


async def main() -> None:
    calculator = ToolRegistry.get("calculator")
    if not calculator:
        raise RuntimeError("Calculator tool not found")

    result = await calculator.execute(expression="(15 * 8) + (42 / 6) - 10")
    print("Tool success:", result.success)
    print("Tool data:", result.data)


if __name__ == "__main__":
    asyncio.run(main())