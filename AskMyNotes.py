import os
import warnings
import requests
import streamlit as st
from dotenv import load_dotenv
from docx import Document
from pypdf import PdfReader
from streamlit_lottie import st_lottie

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings
)
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

warnings.filterwarnings("ignore")

# =========================
# Load .env and get API key
# =========================
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    st.error("❌ GOOGLE_API_KEY not found. Please add it to your .env file.")
    st.stop()

# =========================
# Helper for Lottie Animations
# =========================
def load_lottie_url(url: str):
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

# =========================
# Custom Styling (CSS)
# =========================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: #ffffff;
    font-family: 'Segoe UI', sans-serif;
}

.center-box {
    max-width: 850px;
    margin: auto;
}

.chat-bubble {
    padding: 14px;
    margin: 10px 0;
    border-radius: 14px;
    max-width: 85%;
    font-size: 15px;
    line-height: 1.5;
}

.user-bubble {
    background: linear-gradient(135deg, #4CAF50, #2e7d32);
    color: white;
    margin-left: auto;
    text-align: right;
}

.bot-bubble {
    background-color: #1f2933;
    color: #f1f5f9;
    margin-right: auto;
    border: 1px solid #334155;
}
</style>
""", unsafe_allow_html=True)

# =========================
# Header
# =========================
st.markdown("## 📘 AskMyNotes")
st.caption("Upload your notes and ask questions instantly using AI")

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
1. Upload your notes  
2. Ask a question  
3. Get answers strictly from your content  
""")

st.markdown("---")

# =========================
# Upload Section (HOME PAGE)
# =========================
st.markdown("### 📂 Upload your notes")
file = st.file_uploader(
    "Supported formats: PDF, DOCX, TXT",
    type=["pdf", "docx", "txt"]
)

# =========================
# Main Logic
# =========================
if file is not None:
    with st.status("📄 Processing your file...", expanded=True) as status:
        try:
            status.update(label="Reading file...")
            text = ""

            if file.type == "application/pdf":
                pdf = PdfReader(file)
                for page in pdf.pages:
                    text += page.extract_text() or ""

            elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = Document(file)
                for para in doc.paragraphs:
                    text += para.text + "\n"

            elif file.type == "text/plain":
                text = file.read().decode("utf-8")

            if not text.strip():
                status.update(label="No text found ❌", state="error")
                st.stop()

            status.update(label="Splitting text into chunks...")
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=300,
                chunk_overlap=50
            )
            chunks = splitter.split_text(text)

            status.update(label="Creating embeddings...")
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=GOOGLE_API_KEY
            )
            vector_store = FAISS.from_texts(chunks, embeddings)

            status.update(label="File processed successfully ✅", state="complete")

        except Exception as e:
            status.update(label="Error while processing file ❌", state="error")
            st.error(e)
            st.stop()

    # =========================
    # Question Section
    # =========================
    st.markdown("### 💬 Ask a question about your notes")
    user_query = st.text_input(
        "Type your question and press Enter",
        placeholder="e.g. Explain this topic in simple words"
    )

    if user_query:
        with st.status("🤔 Generating answer...", expanded=True) as q_status:
            try:
                q_status.update(label="Searching relevant content...")
                matching_chunks = vector_store.similarity_search(
                    user_query, k=3
                )

                q_status.update(label="Generating answer...")
                llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    temperature=0.3,
                    max_tokens=1000,
                    google_api_key=GOOGLE_API_KEY
                )

                prompt = ChatPromptTemplate.from_template("""
Answer the question using ONLY the context below.

<context>
{context}
</context>

Question: {input}
""")

                chain = prompt | llm | StrOutputParser()

                output = chain.invoke({
                    "context": matching_chunks,
                    "input": user_query
                })

                q_status.update(label="Answer ready ✅", state="complete")

                st.markdown(
                    f'<div class="chat-bubble user-bubble">{user_query}</div>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    f'<div class="chat-bubble bot-bubble">{output}</div>',
                    unsafe_allow_html=True
                )

            except Exception as e:
                q_status.update(label="Error generating answer ❌", state="error")
                st.error(e)
