import os
import warnings
import hashlib
from io import BytesIO
from typing import Any
import requests
import streamlit as st
from dotenv import load_dotenv
from docx import Document
from pypdf import PdfReader
from streamlit.errors import StreamlitSecretNotFoundError
from streamlit_lottie import st_lottie

from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

warnings.filterwarnings("ignore")

MAX_FILE_SIZE = 20 * 1024 * 1024

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
try:
    GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", GOOGLE_API_KEY)
except StreamlitSecretNotFoundError:
    pass

def load_lottie_url(url: str):
    try:
        response = requests.get(url, timeout=5)
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

def _extract_pdf(file_bytes: bytes, filename: str) -> list[dict[str, Any]]:
    reader = PdfReader(BytesIO(file_bytes))
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({
                "text": text,
                "source": filename,
                "page": page_number,
            })
    return pages

def _extract_docx(file_bytes: bytes, filename: str) -> list[dict[str, Any]]:
    document = Document(BytesIO(file_bytes))
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs]
    text = "\n".join(paragraph for paragraph in paragraphs if paragraph)
    return [{"text": text, "source": filename, "page": None}] if text else []

def _extract_txt(file_bytes: bytes, filename: str) -> list[dict[str, Any]]:
    text = file_bytes.decode("utf-8", errors="replace")
    return [{"text": text, "source": filename, "page": None}] if text.strip() else []

@st.cache_data(show_spinner=False)
def extract_documents(file_payloads: tuple[tuple[str, str, bytes], ...]):
    """Extract and chunk uploaded files; cached data avoids repeat work on reruns."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: list[dict[str, Any]] = []

    for filename, mime_type, file_bytes in file_payloads:
        if len(file_bytes) > MAX_FILE_SIZE:
            raise ValueError(f"{filename} is larger than the 20 MB limit.")

        if mime_type == "application/pdf" or filename.lower().endswith(".pdf"):
            sections = _extract_pdf(file_bytes, filename)
        elif mime_type == (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ) or filename.lower().endswith(".docx"):
            sections = _extract_docx(file_bytes, filename)
        elif mime_type == "text/plain" or filename.lower().endswith(".txt"):
            sections = _extract_txt(file_bytes, filename)
        else:
            raise ValueError(f"Unsupported file type: {filename}")
        for section in sections:
            documents = splitter.create_documents(
                [section["text"]],
                metadatas=[{
                    "source": section["source"],
                    "page": section["page"],
                }],
            )
            chunks.extend(
                {
                    "text": document.page_content,
                    "metadata": document.metadata,
                }
                for document in documents
            )

    if not chunks:
        raise ValueError("No readable text was found in the uploaded files.")

    return tuple(chunk["text"] for chunk in chunks), tuple(
        chunk["metadata"] for chunk in chunks
    )

@st.cache_resource(show_spinner=False)
def build_vector_store(
    chunk_texts: tuple[str, ...],
    chunk_metadata: tuple[dict[str, Any], ...],
    api_key: str | None,
):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        api_key=api_key,
    )
    return FAISS.from_texts(
    list(chunk_texts),
    embeddings,
    metadatas=list(chunk_metadata),
    )

def format_source(metadata: dict[str, Any]) -> str:
    page = metadata.get("page")
    return f"{metadata['source']}" + (f", page {page}" if page else "")

def answer_question(vector_store, user_query: str, api_key: str | None):
    matching_chunks = vector_store.similarity_search(user_query, k=5)
    context_parts = []
    for index, document in enumerate(matching_chunks, start=1):
        context_parts.append(
            f"[Source {index}: {format_source(document.metadata)}]\n"
            f"{document.page_content}"
        )
    context = "\n\n".join(context_parts)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You answer questions using only the supplied note excerpts.
If the excerpts do not contain enough evidence, say exactly that you could not find
the answer in the uploaded notes. Do not use outside knowledge or invent details.
Keep the answer clear and concise. Add citations like [filename, page N] after
claims when a page is available; for non-PDF files cite [filename].""",
    ),
    ("human", "Note excerpts:\n{context}\n\nQuestion: {input}"),
    ])
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
    temperature=0.3,
    max_tokens=1000,
    api_key=api_key,
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"context": context, "input": user_query}), matching_chunks

st.markdown("""
<style>
...
""", unsafe_allow_html=True)
st.markdown("## AskMyNotes")
st.caption("Upload your notes and ask questions grounded in their content")

col1, col2 = st.columns([1, 4], gap="small")
with col1:
    lottie = load_lottie_url(
        "https://assets10.lottiefiles.com/packages/lf20_jcikwtux.json"
    )
    if lottie:
        st_lottie(lottie, height=110)
with col2:
    st.markdown("""
**How it works**
1. Upload one or more notes
2. Ask questions about them
3. Review answers with source references
""")

st.markdown("---")
st.markdown("### Upload your notes")
uploaded_files = st.file_uploader(
    "Supported formats: PDF, DOCX, TXT",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True,
)

if uploaded_files:
    file_payloads = tuple(
        (uploaded_file.name, uploaded_file.type, uploaded_file.getvalue())
        for uploaded_file in uploaded_files
    )
    document_key = tuple(
        (name, hashlib.sha256(file_bytes).hexdigest())
        for name, _, file_bytes in file_payloads
    )

    if st.session_state.get("document_key") != document_key:
        st.session_state.document_key = document_key
        st.session_state.messages = []

    with st.status("Processing your files...", expanded=True) as status:
        try:
            status.update(label="Reading and splitting files...")
            chunk_texts, chunk_metadata = extract_documents(file_payloads)
            status.update(label="Creating or loading the semantic index...")
            vector_store = build_vector_store(
                chunk_texts, chunk_metadata, GOOGLE_API_KEY
            )
            status.update(
                label=f"Processed {len(uploaded_files)} file(s) successfully",
                state="complete",
            )
        except Exception as error:
            status.update(label="Error while processing files", state="error")
            st.error(str(error))
            st.stop()

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()

    for message in st.session_state.get("messages", []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                with st.expander("Sources"):
                    for source in message["sources"]:
                        st.write(source)

    user_query = st.chat_input("Ask a question about your notes")
    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Searching your notes and generating an answer..."):
                try:
                    output, matching_chunks = answer_question(
                        vector_store, user_query, GOOGLE_API_KEY
                    )
                    sources = list(dict.fromkeys(
                        format_source(document.metadata)
                        for document in matching_chunks
                    ))
                    st.markdown(output)
                    with st.expander("Sources"):
                        for source in sources:
                            st.write(source)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": output,
                        "sources": sources,
                    })
                except Exception as error:
                    st.error(str(error))
