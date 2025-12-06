import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from schemas import CodeSenseiAnalysis
from shared_state import AgentState

load_dotenv()


def analyze_with_persona(
    state: AgentState,
    lang_label: str,
    specific_instructions: str,
):
    """Shared logic to call Gemini with a specific persona."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_API_KEY not found."}

    # Initialize Gemini
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        temperature=0,
        google_api_key=api_key,
    )

    # Bind Schema
    structured_llm = llm.with_structured_output(CodeSenseiAnalysis)

    # Construct the Persona-based System Prompt
    system_prompt = (
        f"You are a Senior {lang_label} Engineer and Code Sensei. "
        "Explain code to junior devs and catch 'Knowledge Debt'.\n"
        f"SPECIFIC FOCUS: {specific_instructions}\n\n"
        "CRITICAL RULES:\n"
        "1. Identify Big O complexity issues.\n"
        "2. Suggest specific fixes matching the language idioms.\n"
        "3. Be kind but firm."
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "Analyze this {lang} function named '{name}':\n\n{code}"),
        ],
    )

    chain = prompt | structured_llm

    try:
        result = chain.invoke(
            {"lang": lang_label, "name": state["function_name"], "code": state["code"]},
        )
        # Return the Pydantic model dumped as a dict
        return {"analysis": result.model_dump()}  # type: ignore  # noqa: PGH003
    except Exception as e:  # noqa: BLE001
        return {"error": f"LLM Generation Failed: {e!s}"}
