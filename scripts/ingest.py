import argparse
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.services.vector_store import vector_db

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "inputs",
        nargs="*",
        help="PDF file(s) or folder(s) containing PDFs. Default: data/pdfs",
    )
    args = parser.parse_args()

    pdf_paths = iter_pdf_paths(args.inputs)
    if not pdf_paths:
        raise SystemExit("No PDFs found. Put PDFs in data/pdfs or pass paths explicitly.")

    all_docs = []
    for pdf_path in pdf_paths:
        loader = PyPDFLoader(str(pdf_path))
        all_docs.extend(loader.load())

    chunks = splitter.split_documents(all_docs)
    vector_db.add_documents(chunks)
    vector_db.persist()

    print(f"Ingestion complete. PDFs={len(pdf_paths)} chunks={len(chunks)}")


if __name__ == "__main__":
    main()
