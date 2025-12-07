from sqlite3 import DatabaseError, connect

DB_NAME = "training_data.db"


def get_db():
    conn = connect(DB_NAME, check_same_thread=False)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        yield conn
    finally:
        conn.close()


def create_table():
    """Run this once on startup."""
    try:
        with connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback_loops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code_hash TEXT,
                    function_name TEXT,
                    code_snippet TEXT,
                    ai_explanation TEXT,
                    upvotes INTEGER DEFAULT 0,
                    downvotes INTEGER DEFAULT 0,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(code_hash, ai_explanation)
                )
            """)
            conn.commit()
            print("✅ Database initialized successfully.")
    except DatabaseError as e:
        print(f"❌ Database Init Error: {e}")
