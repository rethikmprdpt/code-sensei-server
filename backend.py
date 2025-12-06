import hashlib
import re
from sqlite3 import Connection
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ai_agent import CodeSenseiAgent
from database import create_table, get_db

# Import our custom engines
from parser_engine import TreeSitterParser
from schemas import CodeRequest, FeedbackRequest

app = FastAPI(title="Code Sensei API")

# --- 1. CORS CONFIGURATION ---
# Allow the React frontend to talk to this backend
origins = [
    "http://localhost:5173",  # Vite default
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    parser = TreeSitterParser()
    agent = CodeSenseiAgent()
    create_table()
    print("✅ Engines initialized successfully.")
except Exception as e:  # noqa: BLE001
    print(f"❌ Failed to initialize engines: {e}")
    # We don't exit here so the server still runs, but it will error on request


@app.post("/analyze")
async def analyze_code(request: CodeRequest):
    """
    Instructions.

    1. Parse the code into functions (CST).
    2. Send each function to Gemini (AI).
    3. Return a list of reports.
    """
    raw_code = request.code
    if not raw_code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    results = []

    # Step A: Parse Code
    try:
        functions = parser.extract_functions(raw_code, lang_name=request.language)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Parser Error: {e!s}")  # noqa: B904

    # Fallback: If no functions found (e.g., just a script), treat whole file as one block
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
        print(f"🤖 Analyzing function: {func['name']}...")

        try:
            analysis = agent.analyze_function(func["code"], func["name"])

            # Merge the AI result with the Location data (Line numbers)
            # This is CRITICAL for the frontend to know where to draw squiggles
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
            # We continue processing other functions even if one fails
            results.append({"meta": func, "error": {"message": str(e)}})

    return {"results": results}


@app.get("/")
def health_check():
    return {
        "status": "active",
        "parser": "tree-sitter-python",
        "agent": "gemini-2.5-pro",
    }


@app.post("/feedback")
async def collect_feedback(
    feedback: FeedbackRequest,
    conn: Annotated[Connection, Depends(get_db)],
):
    """
    Implements 'Signal Aggregation'.

    If data exists, we boost its signal (weights) instead of creating duplicates.
    """
    cursor = conn.cursor()

    # 1. Normalization (The "Canonical" Step)
    # Simple strategy: Remove all whitespace to ignore formatting differences
    # In a real compiler role, you'd use Tree-sitter to strip comments too.
    normalized_code = re.sub(r"\s+", "", feedback.code)

    # 2. Structural Hashing
    code_hash = hashlib.sha256(normalized_code.encode("utf-8")).hexdigest()

    # 3. Determine Vote Direction
    vote_col = "upvotes" if feedback.rating > 0 else "downvotes"

    try:
        # 4. The UPSERT (Insert or Update)
        # SQLite syntax: ON CONFLICT(columns) DO UPDATE SET ...
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
