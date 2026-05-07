import os
import shutil
import random
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import aiosqlite
from app.db import DB_PATH
from app import parser

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

BOOKS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "books")
COVER_COLORS = [
    "#4a7c59", "#7c4a6a", "#4a5f7c", "#7c6a4a",
    "#6a4a7c", "#4a7c7c", "#7c4a4a", "#5f7c4a",
]


@router.get("/", response_class=HTMLResponse)
async def library_home(request: Request):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT b.*, 
                   COALESCE(p.paragraph_index, 0) as current_para,
                   ROUND(COALESCE(p.paragraph_index, 0) * 100.0 / NULLIF(b.total_paragraphs, 0)) as progress_pct
            FROM books b
            LEFT JOIN progress p ON p.book_id = b.id
            ORDER BY COALESCE(p.updated_at, b.added_at) DESC
        """) as cur:
            books = [dict(r) for r in await cur.fetchall()]
    return templates.TemplateResponse("library.html", {"request": request, "books": books})


@router.post("/upload")
async def upload_book(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(""),
    author: str = Form(""),
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".pdf", ".epub"):
        raise HTTPException(400, "Само PDF и EPUB файлове са поддържани")

    os.makedirs(BOOKS_DIR, exist_ok=True)
    safe_name = file.filename.replace(" ", "_")
    dest = os.path.join(BOOKS_DIR, safe_name)

    # Save uploaded file
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Parse paragraphs
    try:
        paragraphs = parser.parse_book(dest)
    except Exception as e:
        os.remove(dest)
        raise HTTPException(500, f"Грешка при парсване: {e}")

    if not paragraphs:
        os.remove(dest)
        raise HTTPException(400, "Не беше намерен текст в книгата")

    book_title = title.strip() or os.path.splitext(file.filename)[0].replace("_", " ")
    color = random.choice(COVER_COLORS)

    async with aiosqlite.connect(DB_PATH) as db:
        try:
            cur = await db.execute(
                "INSERT INTO books (title, author, filename, format, total_paragraphs, cover_color) VALUES (?,?,?,?,?,?)",
                (book_title, author.strip(), safe_name, ext.lstrip("."), len(paragraphs), color)
            )
            book_id = cur.lastrowid

            await db.executemany(
                "INSERT INTO paragraphs (book_id, idx, chapter, text) VALUES (?,?,?,?)",
                [(book_id, i, p["chapter"], p["text"]) for i, p in enumerate(paragraphs)]
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            os.remove(dest)
            raise HTTPException(500, f"Грешка при запис: {e}")

    return RedirectResponse("/", status_code=303)


@router.post("/delete/{book_id}")
async def delete_book(book_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT filename FROM books WHERE id=?", (book_id,)) as cur:
            row = await cur.fetchone()
        if not row:
            raise HTTPException(404, "Книгата не е намерена")

        filepath = os.path.join(BOOKS_DIR, row["filename"])
        if os.path.exists(filepath):
            os.remove(filepath)

        await db.execute("DELETE FROM books WHERE id=?", (book_id,))
        await db.commit()

    return RedirectResponse("/", status_code=303)
