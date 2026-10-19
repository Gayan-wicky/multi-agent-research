
import asyncio
import os

from dotenv import load_dotenv
from agents import Agent, Runner


async def main():
    # Load API keys from .env
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OpenAI API key not found.")
        print("Check your .env file location.")
        return

    print("OpenAI API key found.")
    print("Testing connection...")

    agent = Agent(
        name="Test Agent",
        instructions="Reply with exactly: OpenAI connection successful.",
        model="gpt-5.4-mini",
    )

    result = await Runner.run(
        agent,
        "Test connection",
    )

    print("\nResponse:")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
