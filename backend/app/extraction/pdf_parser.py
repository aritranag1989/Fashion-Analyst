from io import BytesIO

import pdfplumber
from pydantic import BaseModel


class ExtractedPdf(BaseModel):
    text: str
    tables: list[list[list[str | None]]]
    page_count: int


def extract_pdf(pdf_bytes: bytes) -> ExtractedPdf:
    text_parts: list[str] = []
    tables: list[list[list[str | None]]] = []

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
            for table in page.extract_tables():
                tables.append(table)
        page_count = len(pdf.pages)

    return ExtractedPdf(text="\n".join(text_parts), tables=tables, page_count=page_count)
