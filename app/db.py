import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "bookworm.db")

CREATE_BOOKS = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT DEFAULT '',
    filename TEXT NOT NULL UNIQUE,
    format TEXT NOT NULL,
    total_paragraphs INTEGER DEFAULT 0,
    cover_color TEXT DEFAULT '#4a7c59',
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_PROGRESS = """
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    paragraph_index INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(book_id)
);
"""

CREATE_PARAGRAPHS = """
CREATE TABLE IF NOT EXISTS paragraphs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    idx INTEGER NOT NULL,
    chapter TEXT DEFAULT '',
    text TEXT NOT NULL
);
"""

async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_BOOKS)
        await db.execute(CREATE_PROGRESS)
        await db.execute(CREATE_PARAGRAPHS)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_paragraphs_book ON paragraphs(book_id, idx)")
        await db.commit()

async def get_db():
    return aiosqlite.connect(DB_PATH)
