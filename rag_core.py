"""
CineMindAI — RAG backend (loaded only after user clicks Launch).
"""

import contextlib
import logging
import os
import re
import sys
from pathlib import Path
from typing import List

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
# ChromaDB / OpenTelemetry vs protobuf 4+ on Streamlit Cloud
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

import chromadb
from langchain_classic.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from huggingface_hub.utils import disable_progress_bars

    disable_progress_bars()
except Exception:
    pass

logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

BASE_DIR = Path(__file__).resolve().parent
MOVIES_FILE = BASE_DIR / "movies.txt"

QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are CineMindAI, a confident movie guide who gives clear picks.

Use ONLY facts from the Context below. Never invent titles, plots, cast, or ratings.

How to write:
- Medium length: about 3–5 sentences. Not a single line, not an essay.
- Sound natural and helpful, like a friend who knows film — not robotic or legalistic.

Comparisons and "which should I watch":
- You MUST choose exactly ONE film as the winner. Name it clearly in the first sentence (e.g. "Tonight I'd pick Interstellar.").
- Briefly say why it wins over the other option using facts from the Context — do NOT say "both are good" or "it depends on your mood" unless the user only asked for facts, not a recommendation.
- Do not give equal paragraphs for each film when the user wants a decision; one short contrast line for the loser is enough.

Other requests:
- If the user asks to compare but only one film is in the Context, say which title is missing and recommend the one you have (or ask them to pick two films from the library).
- If asked for similar films, name up to 3 titles from the Context with one line each on why.
- Avoid repeating "the Context" or "the database" more than once.

Context:
{context}

Question: {question}

Reply:""",
)


@contextlib.contextmanager
def quiet_stdio():
    with open(os.devnull, "w", encoding="utf-8") as devnull:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = devnull, devnull
        try:
            yield
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr


class HuggingFaceMiniLMEmbeddings(Embeddings):
    def __init__(self) -> None:
        with quiet_stdio():
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2",
                device="cpu",
            )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        with quiet_stdio():
            vectors = self._model.encode(
                texts, normalize_embeddings=True, show_progress_bar=False
            )
        return vectors.tolist()

    def embed_query(self, text: str) -> List[float]:
        with quiet_stdio():
            vector = self._model.encode(
                text, normalize_embeddings=True, show_progress_bar=False
            )
        return vector.tolist()


def load_movie_documents() -> List[Document]:
    raw_text = MOVIES_FILE.read_text(encoding="utf-8")
    blocks = [b.strip() for b in raw_text.split("\n---\n") if b.strip()]
    documents: List[Document] = []
    for block in blocks:
        title_match = re.search(r"^Title:\s*(.+)$", block, re.MULTILINE)
        genre_match = re.search(r"^Genre:\s*(.+)$", block, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "Unknown"
        genre = genre_match.group(1).strip() if genre_match else "Unknown"
        documents.append(
            Document(page_content=block, metadata={"title": title, "genre": genre})
        )
    return documents


def build_rag_chain(api_key: str):
    movie_docs = load_movie_documents()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800, chunk_overlap=0, separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_documents(movie_docs)

    with quiet_stdio():
        embeddings = HuggingFaceMiniLMEmbeddings()
        client = chromadb.EphemeralClient()
        vectorstore = Chroma(
            client=client,
            collection_name="cinemind_movies",
            embedding_function=embeddings,
        )
        vectorstore.add_documents(chunks)

    n = max(len(chunks), 1)
    k = min(10, n)
    fetch_k = min(24, n)
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": k, "fetch_k": max(k, fetch_k)},
    )
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=520,
        openai_api_key=api_key,
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": QA_PROMPT},
    )
