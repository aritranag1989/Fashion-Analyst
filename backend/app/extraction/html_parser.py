from bs4 import BeautifulSoup
from pydantic import BaseModel


class ExtractedHtml(BaseModel):
    title: str | None
    language: str | None
    text: str
    pdf_links: list[str]
    image_urls: list[str]


def extract_html(html: str, base_url: str) -> ExtractedHtml:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else None
    html_tag = soup.find("html")
    language = html_tag.get("lang") if html_tag else None

    text = " ".join(soup.get_text(separator=" ").split())

    pdf_links = [
        a["href"]
        for a in soup.find_all("a", href=True)
        if a["href"].lower().endswith(".pdf")
    ]
    image_urls = [img["src"] for img in soup.find_all("img", src=True)]

    return ExtractedHtml(
        title=title, language=language, text=text, pdf_links=pdf_links, image_urls=image_urls
    )
