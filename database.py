from sqlite3 import DatabaseError, connect

# Check same thread = False allows FastAPI (async) to share this connection
conn = connect("training_data.db", check_same_thread=False)


def get_db():
    try:
        yield conn
    finally:
        pass


def create_table():
    try:
        cursor = conn.cursor()
        # We add 'code_hash' and 'upvotes/downvotes'
        # We create a UNIQUE constraint so we can perform UPSERTS later
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
    except DatabaseError as e:
        print(f"DB Init Error: {e}")
    else:
        conn.commit()
        print("✅ Feedback table initialized with Deduplication constraints")
