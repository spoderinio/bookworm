from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import aiosqlite
from app.db import DB_PATH

router = APIRouter(prefix="/read")
templates = Jinja2Templates(directory="app/templates")


@router.get("/{book_id}", response_class=HTMLResponse)
async def reader_page(request: Request, book_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM books WHERE id=?", (book_id,)) as cur:
            book = await cur.fetchone()
        if not book:
            raise HTTPException(404, "Книгата не е намерена")

        async with db.execute(
            "SELECT paragraph_index FROM progress WHERE book_id=?", (book_id,)
        ) as cur:
            prog = await cur.fetchone()
        start_para = prog["paragraph_index"] if prog else 0

    return templates.TemplateResponse("reader.html", {
        "request": request,
        "book": dict(book),
        "start_para": start_para,
    })


@router.get("/{book_id}/paragraph/{idx}")
async def get_paragraph(book_id: int, idx: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT idx, chapter, text FROM paragraphs WHERE book_id=? AND idx=?",
            (book_id, idx)
        ) as cur:
            para = await cur.fetchone()
        if not para:
            raise HTTPException(404, "Параграф не е намерен")

        async with db.execute(
            "SELECT total_paragraphs FROM books WHERE id=?", (book_id,)
        ) as cur:
            book = await cur.fetchone()

    return JSONResponse({
        "idx": para["idx"],
        "chapter": para["chapter"],
        "text": para["text"],
        "total": book["total_paragraphs"],
        "is_last": para["idx"] >= book["total_paragraphs"] - 1,
    })


@router.post("/{book_id}/progress/{idx}")
async def save_progress(book_id: int, idx: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO progress (book_id, paragraph_index, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(book_id) DO UPDATE SET
                paragraph_index=excluded.paragraph_index,
                updated_at=CURRENT_TIMESTAMP
        """, (book_id, idx))
        await db.commit()
    return JSONResponse({"ok": True})
