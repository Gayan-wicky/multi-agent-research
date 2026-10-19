# 🔎 Multi-Agent Research Assistant

A Python-based AI research assistant that searches the web, extracts relevant webpage content, analyzes evidence using multiple AI-agent stages, reviews findings, and generates downloadable Markdown and PDF reports.

The application uses **Ollama** for local language-model inference, **Olostep** for web search and webpage extraction, **Streamlit** for the browser interface, and **ReportLab** for PDF generation.

## ✨ Features

- 🌐 Web search using the Olostep API
- 📄 Automatic webpage content extraction
- 🧩 Text chunking to process long webpages
- 🎯 Selection of relevant text sections
- 🤖 Research analyst agent
- ⚖️ Judge/reviewer agent for checking findings against evidence
- 🔍 Automatic quotation text checks
- 🖥️ Local LLM inference using Ollama
- 🌍 Browser-based interface using Streamlit
- 📝 Markdown report generation
- 📕 PDF report generation
- ⬇️ Download buttons for research reports

> **Important:** AI-generated results can contain errors. Quotation matching does not prove a claim is true. Always verify important claims against the original sources.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Ollama | Runs the language model locally |
| Qwen 2.5 3B | Default local language model |
| Olostep API | Web search and webpage extraction |
| Streamlit | Browser-based user interface |
| HTTPX | HTTP requests to APIs |
| python-dotenv | Loads environment variables |
| ReportLab | Generates PDF reports |

## 🏗️ Project Architecture

1. The user enters a research question.
2. Olostep searches for relevant webpages.
3. The application extracts webpage content.
4. The text is split into overlapping chunks.
5. Relevant chunks are selected for the research question.
6. The analyst agent prepares findings using the selected evidence.
7. The judge agent reviews the findings and identifies limitations.
8. A quotation checker looks for quoted text in the selected evidence.
9. The application generates Markdown and PDF reports.
10. The user reads and downloads the reports through the browser.

## 📁 Project Structure

```text
multi-agent-research/
│
├── app.py                 # Streamlit web interface
├── main.py                # Research workflow and AI agents
├── pdf_report.py          # PDF report generation
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation
├── .env                   # Private configuration; never upload
├── .env.example           # Safe environment template
├── .gitignore             # Git ignore rules
│
├── research_report.md     # Generated Markdown report
├── research_report.pdf    # Generated PDF report
└── .venv/                 # Python virtual environment
```

Generated reports and `.venv/` do not normally need to be uploaded to GitHub.

## 💻 Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer recommended
- Git for GitHub uploads
- Ollama installed
- A compatible Ollama model
- An Olostep API key
- Internet access for web search and webpage extraction

**Note:** The language model runs locally, but web search and webpage extraction require an internet connection and access to Olostep. Check the provider's current pricing, quotas, and free-tier availability.

## 🚀 Installation and Setup

### Step 1: Install Python

Download Python:

https://www.python.org/downloads/

Check the installation in PowerShell:

```powershell
python --version
python -m pip --version
```

### Step 2: Install Ollama

Download Ollama:

https://ollama.com/download

Pull the default model:

```powershell
ollama pull qwen2.5:3b
```

Check the installed model:

```powershell
ollama list
```

Test the model:

```powershell
ollama run qwen2.5:3b
```

Type a question to test it. Enter `/bye` to exit the interactive session.

Ollama's default local API address is:

```text
http://localhost:11434
```

Keep Ollama running while using the application.

### Step 3: Clone the GitHub repository

After uploading this project to GitHub, clone it using your repository URL:

```powershell
git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
```

Enter the project directory:

```powershell
cd YOUR-REPOSITORY
```

Replace the example repository URL and folder name with your actual details.

If you are setting up the project you already have on your computer, open that folder instead of cloning it again.

### Step 4: Create a virtual environment

From the project folder, run:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Your terminal should show `(.venv)` at the beginning of the prompt.

If PowerShell blocks activation, run this command in the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again.

### Step 5: Install Python dependencies

Create a file named `requirements.txt` containing:

```text
streamlit
httpx
python-dotenv
reportlab
```

Install the dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Step 6: Configure the Olostep API key

Create a file named `.env` in the project root:

```dotenv
OLOSTEP_API_KEY=your_actual_olostep_api_key
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_BASE_URL=http://localhost:11434
```

Get your API key through your Olostep account:

https://olostep.com/

Replace `your_actual_olostep_api_key` with your own key.

**Never upload `.env` or share your real API key publicly.**

For the GitHub repository, create a separate `.env.example` file containing only placeholders:

```dotenv
OLOSTEP_API_KEY=your_olostep_api_key_here
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_BASE_URL=http://localhost:11434
```

### Step 7: Verify the required files

Ensure that the project contains:

- `main.py`
- `app.py`
- `pdf_report.py`
- `requirements.txt`
- `.env`

The application imports `manager_agent()` and `save_report()` from `main.py`, and `create_pdf_report()` from `pdf_report.py`.

## ▶️ Running the Application

Activate the virtual environment and navigate to the project directory.

Start the application:

```powershell
python -m streamlit run app.py
```

On the first launch, Streamlit may ask for an email address. Press **Enter** to skip it.

Open the application in your browser:

http://localhost:8501

### Using the application

1. Enter your research question.
2. Click **Start Research**.
3. Wait for the research workflow to finish.
4. Read the generated report in your browser.
5. Download the Markdown or PDF report.

The current interface displays a spinner while the workflow runs. It does not yet display separate live progress for each agent.

To stop the application, press `Ctrl + C` in PowerShell.

## ⚙️ Configuration

The current implementation uses these default settings in `main.py`:

| Setting | Default | Description |
|---|---|---|
| `OLLAMA_MODEL` | `qwen2.5:3b` | Local language model |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API URL |
| `MAX_SEARCH_RESULTS` | `3` | Maximum search results processed |
| `CHUNK_SIZE` | `3000` | Approximate characters per chunk |
| `CHUNK_OVERLAP` | `300` | Overlap between chunks |
| `TOP_CHUNKS_PER_SOURCE` | `2` | Relevant chunks selected per source |
| `REPORT_FILE` | `research_report.md` | Markdown report filename |

These values describe the version developed for this project. Check `main.py` if you have changed the configuration.

## 📄 Generated Reports

The application generates:

- **`research_report.md`** — Markdown report that can be read or edited in a text editor.
- **`research_report.pdf`** — PDF version suitable for sharing or printing.

The PDF generator supports common Markdown formatting. Complex tables or advanced formatting may not render perfectly.

## 🐛 Troubleshooting

### Module not found

Activate the virtual environment and reinstall dependencies:

```powershell
python -m pip install -r requirements.txt
```

### Olostep authentication error

- Check that `.env` exists in the project root.
- Verify the variable name `OLOSTEP_API_KEY`.
- Confirm the API key is valid.
- Check your account's API limits and access.

Never post your API key in a public GitHub issue.

### Ollama connection error

Check the installed model:

```powershell
ollama list
```

Confirm that Ollama is running and that `.env` contains:

```dotenv
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
```

### Streamlit port already in use

Run the app on another port:

```powershell
python -m streamlit run app.py --server.port 8502
```

Then open:

http://localhost:8502

### Webpage extraction fails

Some websites block automated scraping, require JavaScript, or return access-denied pages. Try another source. Successful extraction does not necessarily mean that the correct article content was retrieved.

### PDF generation fails

Install ReportLab:

```powershell
python -m pip install reportlab
```

Check that `pdf_report.py` exists and inspect the terminal error.

## 🔐 GitHub Security

Create a `.gitignore` file containing:

```gitignore
# Secrets
.env
.env.*
!.env.example

# Virtual environments
.venv/
venv/
env/

# Python cache
__pycache__/
*.py[cod]

# IDE and operating system files
.vscode/
.idea/
.DS_Store
Thumbs.db

# Generated reports
research_report.md
research_report.pdf

# Logs
*.log
```

Before uploading, run:

```powershell
git status
```

Check that `.env` and `.venv/` are not listed for upload.

If you previously uploaded an API key, revoke or rotate it. Removing the file in a later commit does not erase the secret from the repository's history.

## 📤 Upload the Project to GitHub

Create an empty repository on GitHub:

https://github.com/new

Then run the following commands in the project directory:

```powershell
git init
git add .
git status
git commit -m "Add multi-agent research assistant"
git branch -M main
```

Connect your own repository:

```powershell
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Replace the example URL with your actual GitHub repository URL.

For later updates:

```powershell
git add .
git status
git commit -m "Update research assistant"
git push
```

## ⚠️ Current Limitations

- AI-generated results may be incomplete or incorrect.
- Webpage extraction can fail or return access-denied content.
- Chunk selection uses lightweight keyword matching and can miss relevant context.
- Quotation matching does not prove that a claim is true.
- Detailed live agent progress is not currently displayed in the UI.
- Web search and scraping require Olostep access and internet connectivity.
- Results depend on the local model, extracted content, and selected sources.

## 📜 License

No license has been selected for this project yet. Add a license file if you want to define
