import re
from pathlib import Path


def clean_text(text: str) -> str:
    """Remove excessive whitespace and normalize."""
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def is_valid_paragraph(text: str) -> bool:
    """Filter out short/empty/junk paragraphs."""
    text = text.strip()
    if len(text) < 20:
        return False
    # Skip paragraphs that are just numbers (page numbers, chapter numbers)
    if re.match(r'^\d+\.?$', text):
        return False
    return True


def parse_pdf(filepath: str) -> list[dict]:
    """Extract paragraphs from PDF, skipping images."""
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer, LTFigure, LTPage

    paragraphs = []
    page_num = 0

    for page_layout in extract_pages(filepath):
        page_num += 1
        page_texts = []

        for element in page_layout:
            # Skip image/figure elements
            if isinstance(element, LTFigure):
                continue
            if isinstance(element, LTTextContainer):
                text = element.get_text()
                text = clean_text(text)
                if text:
                    page_texts.append(text)

        # Merge short fragments into paragraphs
        current = ""
        for fragment in page_texts:
            if not current:
                current = fragment
            elif len(current) < 200 and not current.endswith('.'):
                current += " " + fragment
            else:
                if is_valid_paragraph(current):
                    paragraphs.append({
                        "chapter": f"Страница {page_num}",
                        "text": current
                    })
                current = fragment

        if current and is_valid_paragraph(current):
            paragraphs.append({
                "chapter": f"Страница {page_num}",
                "text": current
            })

    return paragraphs


def parse_epub(filepath: str) -> list[dict]:
    """Extract paragraphs from EPUB, skipping images."""
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup

    book = epub.read_epub(filepath, options={"ignore_ncx": True})
    paragraphs = []

    for item in book.get_items():
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue

        soup = BeautifulSoup(item.get_content(), "html.parser")

        # Remove image tags and their containers
        for tag in soup.find_all(['img', 'figure', 'svg', 'image']):
            tag.decompose()

        # Try to get chapter title from heading
        chapter_title = ""
        heading = soup.find(['h1', 'h2', 'h3'])
        if heading:
            chapter_title = clean_text(heading.get_text())

        # Extract paragraphs
        for p_tag in soup.find_all(['p', 'div']):
            # Skip divs that contain other block elements (structural divs)
            if p_tag.name == 'div' and p_tag.find(['p', 'div', 'section']):
                continue

            text = clean_text(p_tag.get_text())
            if is_valid_paragraph(text):
                paragraphs.append({
                    "chapter": chapter_title or "—",
                    "text": text
                })

    return paragraphs


def parse_book(filepath: str) -> list[dict]:
    """Parse a book file and return list of {chapter, text} dicts."""
    ext = Path(filepath).suffix.lower()
    if ext == ".pdf":
        return parse_pdf(filepath)
    elif ext == ".epub":
        return parse_epub(filepath)
    else:
        raise ValueError(f"Unsupported format: {ext}")
