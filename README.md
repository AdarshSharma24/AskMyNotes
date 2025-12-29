# 🤖 GenAIChatBot ~ RizzBot

A document-aware, hallucination-resistant chatbot built with OpenAI + LangChain + RAG + Embeddings.
This chatbot answers your queries from uploaded PDF notes, and if the answer isn’t present in your notes, it falls back to Wikipedia with a disclaimer.


✨ Features

📄 Upload PDF notes and ask questions directly.

🔍 Uses Retrieval-Augmented Generation (RAG) to fetch answers from your notes.

🌍 Falls back to Wikipedia search if the answer is not in the provided documents.

💬 Beautiful Streamlit UI with custom chat bubbles and Lottie animations.

🧠 Reduces hallucination problem of LLMs by making sources transparent.



🛠️ Tech Stack

Language Model: GPT-3.5 Turbo (OpenAI)

Frameworks & Libraries:

LangChain – Document retrieval & chains

FAISS – Vector similarity search

PyPDF2 – Extract text from PDFs

python-docx – Extract text from DOCX files

Streamlit – Interactive UI

dotenv – API key management



🚀 How It Works

Upload your notes (PDF, DOCX, or TXT).

Notes are split into chunks using RecursiveCharacterTextSplitter.

Chunks are converted into embeddings using OpenAIEmbeddings.

User queries are matched with the most relevant chunks using FAISS similarity search.

The chatbot generates a response using ChatOpenAI with a custom prompt.

If the relevant context is not found, the bot fetches a short summary from Wikipedia.

Stylized chat bubbles display the user query and bot response in a beautiful Streamlit UI.





