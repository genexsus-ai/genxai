"""List built-in tools and show how to fetch one from ToolRegistry."""

from genxai.tools.registry import ToolRegistry
from genxai.tools.builtin import *  # noqa: F403 - triggers auto-registration


def main() -> None:
    stats = ToolRegistry.get_stats()
    print("Total tools:", stats["total_tools"])
    print("Categories:", stats["categories"])

    calculator = ToolRegistry.get("calculator")
    if calculator:
        print("Calculator schema:", calculator.get_schema())


if __name__ == "__main__":
    main()