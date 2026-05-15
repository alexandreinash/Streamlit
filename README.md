# 🎬 CineMindAI

**CineMindAI** is an AI-powered movie recommendation chatbot built with **Retrieval-Augmented Generation (RAG)**. It loads movie information from a local dataset, retrieves relevant entries with a vector database, and generates accurate answers using OpenAI.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red)
![LangChain](https://img.shields.io/badge/LangChain-0.3%2B-green)

---

## ✨ Features

- **RAG pipeline** — Retrieves relevant movie chunks before answering
- **Chat interface** — Modern Streamlit UI with `chat_input` and `chat_message`
- **Session memory** — Conversation history stored in `st.session_state`
- **ChromaDB** — Local vector store for semantic search
- **HuggingFace embeddings** — `all-MiniLM-L6-v2` sentence embeddings
- **OpenAI** — Natural language responses via `ChatOpenAI`
- **Sample questions** — Quick-start prompts in the sidebar
- **Streamlit Cloud ready** — Deploy with one click

---

## 🧠 How RAG Works in CineMindAI

1. **Load** — Movie data is read from `movies.txt`
2. **Split** — `RecursiveCharacterTextSplitter` breaks text into chunks
3. **Embed** — `HuggingFaceEmbeddings` converts chunks into vectors
4. **Store** — Vectors are saved in **ChromaDB**
5. **Retrieve** — User questions fetch the most relevant movie chunks
6. **Generate** — **OpenAI** (`ChatOpenAI`) answers using only retrieved context

This keeps responses **grounded in your dataset** instead of guessing from general knowledge alone.

### Accuracy features

- One **document per movie** (Title, Genre, Description) from `movies.txt`
- **Strict LLM prompt** — no invented titles or plot details
- **Temperature 0** — consistent, factual wording
- **MMR retrieval** — diverse, relevant movie chunks per question
- **Source titles** shown under each answer so you can verify the database was used

---

## 📁 Project Structure

```
CineMindAI/
├── app.py              # Streamlit application
├── assets/
│   └── hero_banner.png # Cinema hero image
├── movies.txt          # Movie dataset (title, genre, description)
├── requirements.txt    # Python dependencies
├── README.md           # Project documentation
├── .gitignore          # Git ignore rules
├── .env.example        # Environment variable template
└── chroma_db/          # Auto-created vector store (ignored by git)
```

---

## 🛠️ Installation

### 1. Clone or download the project

```bash
git clone https://github.com/YOUR_USERNAME/CineMindAI.git
cd CineMindAI
```

### 2. Create a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> First run downloads the HuggingFace embedding model (~90MB). This is normal.

### 4. Configure your API key

```bash
copy .env.example .env
```

On macOS/Linux:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-actual-key-here
```

Get a key at: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

---

## ▶️ How to Run

```bash
streamlit run app.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`).

---

## 📤 GitHub Setup

1. Create a new repository on GitHub: [alexandreinash/CineMindAI](https://github.com/alexandreinash/CineMindAI) (empty, no README)
2. Initialize git and push:

```bash
git init
git add .
git commit -m "Initial commit: CineMindAI RAG movie chatbot"
git branch -M main
git remote add origin https://github.com/alexandreinash/CineMindAI.git
git push -u origin main
```

**Important:** Never commit your `.env` file. It is listed in `.gitignore`.

---

## ☁️ Deploy to Streamlit Cloud

1. Push your project to GitHub (without `.env`)
2. Go to [https://share.streamlit.io](https://share.streamlit.io)
3. Click **New app**
4. Select your repository, branch (`main`), and main file path: `app.py`
5. Open **Advanced settings** → **Secrets** and add:

```toml
OPENAI_API_KEY = "sk-your-actual-key-here"
```

6. Click **Deploy**

Streamlit Cloud will install `requirements.txt` automatically. The first launch may take a few minutes while embeddings are built.

---

## 💬 Example Questions

- Recommend action movies
- Suggest sci-fi films
- Movies similar to Interstellar
- Best family movies
- Horror movie recommendations

---

## 📦 Tech Stack

| Component        | Technology                          |
|-----------------|-------------------------------------|
| UI              | Streamlit                           |
| Orchestration   | LangChain                           |
| Vector DB       | ChromaDB                            |
| Embeddings      | HuggingFace (`all-MiniLM-L6-v2`)    |
| LLM             | OpenAI (`gpt-4o-mini`)              |
| Text splitting  | RecursiveCharacterTextSplitter      |
| QA chain        | RetrievalQA                         |

---

## ⚠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| API key error | Ensure `.env` exists with a valid `OPENAI_API_KEY` |
| Slow first start | Embedding model and Chroma index build on first run |
| Module not found | Run `pip install -r requirements.txt` inside your venv |
| Streamlit Cloud fails | Add `OPENAI_API_KEY` in app Secrets, not `.env` |

---

## 📄 License

This project is open source and available for learning and portfolio use.

---

Made with 🍿 for movie lovers everywhere.
