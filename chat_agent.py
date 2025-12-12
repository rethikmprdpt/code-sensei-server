import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


class CodeSenseiChat:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found")

        # Use Flash for Chat (Faster, lower latency)
        # Or stick to Pro if you want deep reasoning
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.4,  # Slightly creative for conversation
            google_api_key=api_key,
        )

    def chat(self, user_message: str, code_context: str, language: str, history: list):
        """
        Conversational turn.
        """
        # 1. Convert Pydantic history to LangChain format
        lc_history = []
        for msg in history:
            if msg.role == "user":
                lc_history.append(HumanMessage(content=msg.content))
            else:
                lc_history.append(AIMessage(content=msg.content))

        # 2. System Prompt (Context Injection)
        system_prompt = (
            f"You are a Senior {language} Expert. "
            "The user is asking about the code block below.\n"
            "GUIDELINES:\n"
            "1. Be extremely concise. No fluff. No 'That's a great question'.\n"
            "2. If the user asks for a fix, provide JUST the code snippet and a 1-sentence explanation.\n"
            "3. Use Markdown formatting (``` code blocks) for all code.\n"
            "4. Assume the user is a developer; do not over-explain basic concepts.\n\n"
            f"### CONTEXT CODE ###\n{code_context}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )

        chain = prompt | self.llm

        # 3. Invoke
        response = chain.invoke({"history": lc_history, "input": user_message})

        return response.content
