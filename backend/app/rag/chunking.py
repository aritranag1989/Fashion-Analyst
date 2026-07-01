"""The one place LlamaIndex is used in this codebase - purely for text splitting utilities, not
its agent/workflow abstractions (LangGraph owns orchestration; see docs/adr/ for the rationale).
"""

from llama_index.core.node_parser import SentenceSplitter

CHUNK_SIZE_TOKENS = 400
CHUNK_OVERLAP_TOKENS = 50

_splitter = SentenceSplitter(chunk_size=CHUNK_SIZE_TOKENS, chunk_overlap=CHUNK_OVERLAP_TOKENS)


def chunk_text(text: str) -> list[str]:
    if not text.strip():
        return []
    return _splitter.split_text(text)
