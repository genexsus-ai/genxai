"""Demonstrate routed LLM provider with fallback models."""

from genxai.llm.factory import LLMProviderFactory


def main() -> None:
    provider = LLMProviderFactory.create_routed_provider(
        primary_model="gpt-4",
        fallback_models=["gpt-3.5-turbo", "claude-3-haiku"],
        temperature=0.5,
    )

    print("Primary model:", provider.primary.model)
    print("Fallbacks:", [fallback.model for fallback in provider.fallbacks])


if __name__ == "__main__":
    main()