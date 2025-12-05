import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from schemas import CodeSenseiAnalysis

# Load environment variables
load_dotenv()


class CodeSenseiAgent:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file")

        # Initialize Gemini
        # We use a low temperature for strict factual analysis
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",  # Or "gemini-1.5-flash" / "gemini-2.0-flash-exp"
            temperature=0.0,
            google_api_key=api_key,
            max_retries=2,
        )

        # Bind your Pydantic V2 schema directly to the model
        self.structured_llm = self.llm.with_structured_output(CodeSenseiAnalysis)

    def analyze_function(self, code_block: str, function_name: str) -> dict | None:
        """
        Sends a single function block to Gemini for analysis.

        Returns a dictionary matching the CodeSenseiAnalysis schema.
        """
        system_prompt = (
            "You are a Senior Systems Architect and Code Sensei. "
            "Your goal is to explain code to junior developers and catch 'Knowledge Debt'.\n\n"
            "CRITICAL RULES:\n"
            "1. If the input is empty, a random word (like 'string'), or not valid code, return 'N/A' for complexity and a quality score of 0.\n"
            "2. Do NOT hallucinate functionality that does not exist.\n"
            "3. Analyze the logic strictly.\n"
            "4. Identify Big O complexity issues.\n"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "Analyze this function named '{name}':\n\n{code}"),
            ],
        )

        # Chain: Prompt -> Gemini -> Pydantic Validation
        chain = prompt | self.structured_llm

        try:
            # Invoke the chain
            result = chain.invoke({"name": function_name, "code": code_block})
            return result.model_dump()

        except Exception as e:  # noqa: BLE001
            print(f"Error analyzing function {function_name}: {e}")
            return None


# --- TEST BLOCK ---
if __name__ == "__main__":
    # Test with bad code to see if it catches the issues
    agent = CodeSenseiAgent()

    bad_code = """
    def find_duplicate(nums):
        # This is O(n^2) - Bad Logic!
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] == nums[j]:
                    return nums[i]
        return -1
    """

    print("Sending code to Gemini...")
    analysis = agent.analyze_function(bad_code, "find_duplicate")

    import json

    # Use default=str to handle any non-serializable types if necessary
    print(json.dumps(analysis, indent=2, default=str))
