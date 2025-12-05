from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ai_agent import CodeSenseiAgent

# Import our custom engines
from parser_engine import TreeSitterParser

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

# --- 2. INITIALIZATION ---
# Initialize expensive objects once on startup
try:
    parser = TreeSitterParser()
    agent = CodeSenseiAgent()
    print("✅ Engines initialized successfully.")
except Exception as e:  # noqa: BLE001
    print(f"❌ Failed to initialize engines: {e}")
    # We don't exit here so the server still runs, but it will error on request


# --- 3. DATA MODELS ---
class CodeRequest(BaseModel):
    code: str


# --- 4. THE ENDPOINT ---
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
        functions = parser.extract_functions(raw_code)
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
                },
                "analysis": analysis,
            }
            results.append(full_report)

        except Exception as e:  # noqa: BLE001
            print(f"⚠️ AI Analysis failed for {func['name']}: {e}")
            # We continue processing other functions even if one fails
            results.append({"meta": func, "error": {"message": str(e)}})

    return {"results": results}


# --- 5. HEALTH CHECK ---
@app.get("/")
def health_check():
    return {
        "status": "active",
        "parser": "tree-sitter-python",
        "agent": "gemini-2.5-pro",
    }
