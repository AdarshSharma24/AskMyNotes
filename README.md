# 📘 AskMyNotes

**AskMyNotes** is a Streamlit-based AI application that lets you upload your personal notes (PDF, DOCX, or TXT) and ask questions about them.  
The answers are generated **strictly from the uploaded content**, using semantic search and Google Gemini models.

---

## ✨ Features

- 📂 Upload notes in **PDF, DOCX, or TXT** format  
- 🔍 Semantic search using **FAISS vector database**  
- 🤖 AI-powered answers using **Google Gemini**  
- 🔒 Answers are based **only on your notes**  
- ⏳ Clear on-page loading and processing indicators  
- 🖥️ Optimized for laptop/desktop usage  

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit  
- **LLM**: Google Gemini (via LangChain)  
- **Embeddings**: Google Generative AI embeddings  
- **Vector Store**: FAISS  
- **Language**: Python 3  

---

## 📁 Project Structure

```bash
AskMyNotes/
├── AskMyNotes.py # Main Streamlit application
├── requirements.txt # Project dependencies
├── .env # API keys (not committed)
├── .gitignore
└── README.md
```

---

## 🚀 Setup & Usage (on any PC)

Follow these steps **in order**.

---

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/AdarshSharma24/AskMyNotes.git
cd AskMyNotes
```

### 2️⃣ Create a Virtual Environment (Recommended)
#### Windows
```bash
python -m venv .venv   #creating the enviroment
.venv\Scripts\activate   #activating the enviroment
```
#### Linux / macOS
```bash
python3 -m venv .venv   #creating the enviroment
source .venv/bin/activate   #activating the enviroment
```
#### If you are using VS Code you can also do this for activating your enviroment:
```ruby
Ctrl+Shift+P > Python Interpreter > select the one which you have created in your working directory i.e. AskMyNotes
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Set Up Environment Variables
Create a file named .env in the project root:
```ruby
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

### 5️⃣ Run the Application
```bash
python -m streamlit run AskMyNotes.py
```

### If you want to exit the virtual enviroment
just write ``deactivate`` in the terminal where virtual enviroment is active.

Virtual enviroment only affects python, it has nothing to do with git commands.

