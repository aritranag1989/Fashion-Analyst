"""Flattens extracted PDF/HTML tables (product catalogs, price lists, spec sheets) into
natural-language sentences suitable for embedding into the product_catalog_chunks collection.
"""


def flatten_table_to_sentences(table: list[list[str | None]]) -> list[str]:
    if not table or not table[0]:
        return []

    header = [cell.strip() if cell else "" for cell in table[0]]
    sentences: list[str] = []

    for row in table[1:]:
        pairs = [
            f"{header[i]}: {cell.strip()}"
            for i, cell in enumerate(row)
            if i < len(header) and cell and cell.strip() and header[i]
        ]
        if pairs:
            sentences.append("; ".join(pairs))

    return sentences
