from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app import db
from app.routers import library, reader, tts

app = FastAPI(title="Bookworm")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/book-files", StaticFiles(directory="data/books"), name="book-files")

app.include_router(library.router)
app.include_router(reader.router)
app.include_router(tts.router)

@app.on_event("startup")
async def startup():
    await db.init_db()
