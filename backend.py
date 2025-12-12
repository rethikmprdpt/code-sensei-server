import hashlib
import re
from contextlib import asynccontextmanager
from sqlite3 import Connection
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ai_agent import run_agent
from chat_agent import CodeSenseiChat
from database import create_table, get_db
from parser_engine import TreeSitterParser, get_parser
from schemas import ChatRequest, CodeRequest, FeedbackRequest


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    # Startup: Create DB Tables
    create_table()
    yield
    # Shutdown: Clean up if necessary


def get_chat_agent():
    return CodeSenseiChat()


app = FastAPI(title="Code Sensei API", lifespan=lifespan)


origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze")
async def analyze_code(
    request: CodeRequest,
    parser: Annotated[TreeSitterParser, Depends(get_parser)],
):
    """Analyzes code with Language Mismatch Detection."""
    raw_code = request.code
    if not raw_code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    results = []

    # Step A: Parse Code with Safety Check
    try:
        functions = parser.extract_functions(raw_code, lang_name=request.language)

    # Catch the Language Mismatch specifically
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    except Exception as e:
        # Unexpected parser crashes
        raise HTTPException(status_code=500, detail=f"Parser Error: {e!s}") from e

    if not functions:
        functions = [
            {
                "name": "Main Script",
                "code": raw_code,
                "start_line": 1,
                "end_line": len(raw_code.splitlines()),
            },
        ]

    # Step B: Analyze each block
    for func in functions:
        print(f"🤖 Analyzing function: {func['name']} ({request.language})...")

        try:
            analysis = run_agent(func["code"], request.language, func["name"])

            full_report = {
                "meta": {
                    "function_name": func["name"],
                    "start_line": func["start_line"],
                    "end_line": func["end_line"],
                    "code": func["code"],
                },
                "analysis": analysis,
            }
            results.append(full_report)

        except Exception as e:  # noqa: BLE001
            print(f"⚠️ AI Analysis failed for {func['name']}: {e}")
            results.append({"meta": func, "error": {"message": str(e)}})

    return {"results": results}


@app.get("/")
def health_check():
    return {
        "status": "active",
        "parser": "tree-sitter-polyglot",
        "agent": "langgraph-multi-expert",
        "version": "v1.0.0",
    }


@app.post("/feedback")
async def collect_feedback(
    feedback: FeedbackRequest,
    conn: Annotated[Connection, Depends(get_db)],
):
    cursor = conn.cursor()
    normalized_code = re.sub(r"\s+", "", feedback.code)
    code_hash = hashlib.sha256(normalized_code.encode("utf-8")).hexdigest()
    vote_col = "upvotes" if feedback.rating > 0 else "downvotes"

    try:
        query = f"""
            INSERT INTO feedback_loops
            (code_hash, function_name, code_snippet, ai_explanation, {vote_col})
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(code_hash, ai_explanation)
            DO UPDATE SET
                {vote_col} = {vote_col} + 1,
                last_updated = CURRENT_TIMESTAMP
        """  # noqa: S608
        cursor.execute(
            query,
            (code_hash, feedback.function_name, feedback.code, feedback.explanation),
        )
        conn.commit()
    except Exception as e:
        print(f"DB Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save feedback") from e
    else:
        return {"status": "success", "message": "Signal aggregated successfully"}


@app.post("/chat")
async def chat_with_sensei(
    request: ChatRequest, chat_agent: Annotated[CodeSenseiChat, Depends(get_chat_agent)]
):
    try:
        response_text = chat_agent.chat(
            user_message=request.message,
            code_context=request.code_context,
            language=request.language,
            history=request.history,
        )
        return {"response": response_text}
    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
