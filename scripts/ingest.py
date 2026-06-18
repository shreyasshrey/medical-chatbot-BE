import argparse
import time
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.services.vector_store import get_vector_db

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)

def iter_pdf_paths(inputs: list[str]) -> list[Path]:
    if not inputs:
        inputs = ["data/pdfs"]

    pdfs: list[Path] = []
    for raw in inputs:
        p = Path(raw)
        if p.is_dir():
            pdfs.extend(sorted(p.glob("*.pdf")))
        else:
            pdfs.append(p)

    seen: set[Path] = set()
    unique: list[Path] = []
    for p in pdfs:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(rp)

    return unique


def ingest_pdfs(inputs: list[str] | None = None) -> dict:
    pdf_paths = iter_pdf_paths(inputs or [])
    if not pdf_paths:
        raise ValueError("No PDFs found. Put PDFs in data/pdfs or pass paths explicitly.")

    print(f"Ingestion started. pdfs={len(pdf_paths)}", flush=True)

    all_docs = []
    for pdf_path in pdf_paths:
        print(f"Loading PDF: {pdf_path.name}", flush=True)
        loader = PyPDFLoader(str(pdf_path))
        all_docs.extend(loader.load())

    print(f"PDF loading complete. documents={len(all_docs)}", flush=True)
    print("Splitting into chunks...", flush=True)

    t_chunk_start = time.perf_counter()
    chunks = splitter.split_documents(all_docs)
    t_chunk_s = time.perf_counter() - t_chunk_start

    print(f"Chunking complete. chunks={len(chunks)} time_s={t_chunk_s:.3f}", flush=True)
    print("Adding chunks to vector store...", flush=True)

    vector_db = get_vector_db(create=True)
    t_store_start = time.perf_counter()
    vector_db.add_documents(chunks)
    try:
        vector_db.persist()
    except AttributeError:
        pass
    t_store_s = time.perf_counter() - t_store_start

    print(f"Vector store write complete. time_s={t_store_s:.3f}", flush=True)

    print("Ingestion finished.", flush=True)

    return {
        "pdfs": len(pdf_paths),
        "documents": len(all_docs),
        "chunks": len(chunks),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "inputs",
        nargs="*",
        help="PDF file(s) or folder(s) containing PDFs. Default: data/pdfs",
    )
    args = parser.parse_args()

    try:
        result = ingest_pdfs(args.inputs)
    except ValueError as e:
        raise SystemExit(str(e))

    print(
        "Ingestion complete. "
        f"PDFs={result['pdfs']} documents={result['documents']} chunks={result['chunks']}"
    )


if __name__ == "__main__":
    main()
