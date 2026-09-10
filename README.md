# ACC Chat Bot

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/RAG-Enabled-8A2BE2?style=for-the-badge" alt="RAG Enabled" />
  <img src="https://img.shields.io/badge/AI-Assistant-0EA5E9?style=for-the-badge" alt="AI Assistant" />
</p>

Analytics Career Connect (ACC) AI Assistant is a smart, document-aware chatbot and career guidance platform built for ACC programs, internships, job tracks, and knowledge portals. It combines FastAPI, a retrieval-augmented generation (RAG) pipeline, and structured program data to answer questions with citations and official ACC context.

## Why this project matters

ACC helps students and professionals transition into analytics and business roles with training, internship opportunities, and placement guidance. This bot turns official ACC documents and public website information into a searchable, conversational experience that can:

- answer student internship questions instantly
- explain program tracks and eligibility
- surface scam-alert policies and fee transparency
- recommend relevant career tracks based on skill level
- help users explore documents and course material

## Features

- AI chat assistant trained on official ACC content
- Document-aware retrieval using indexed PDF and website snippets
- Program and internship directory with filters by batch and track
- Career match recommendation engine
- Multi-provider LLM support with graceful local fallback
- Frontend interface with modern dark UI
- Health check and test coverage

## Tech stack

- Python 3.11+
- FastAPI
- pypdf (PDF indexing & processing)
- RAG-based custom retrieval engine
- HTML/JS frontend with Tailwind CSS
- pytest for automated validation

## Project structure

```text
ACC_CHAT_BOT/
├── app/
│   ├── api/
│   ├── data/
│   ├── knowledge/
│   ├── services/
│   ├── static/
│   └── main.py
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── test_app.py
├── app.py
├── website_data.json
├── *.pdf
└── ...
```

## Quick start

1. Clone the repository
   ```bash
   git clone https://github.com/koushikgarg11/ACC_CHAT_BOT.git
   cd ACC_CHAT_BOT
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv .venv
   .venv\Scripts\activate    # Windows PowerShell
   # or
   source .venv/bin/activate # macOS/Linux
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables
   ```bash
   copy .env.example .env
   ```
   Then add your API keys if you want to use cloud providers.

5. Run the FastAPI app
   ```bash
   python app.py
   ```
   The service will start on:
   - http://127.0.0.1:8000/

6. Run the Streamlit app for deployment-friendly UI
   ```bash
   streamlit run streamlit_app.py
   ```
   The app will launch locally on:
   - http://localhost:8501

7. Run tests
   ```bash
   python -m pytest test_app.py -q
   ```

## Streamlit deployment

This project now supports a Streamlit version for simple hosting and quick deployment on platforms like Streamlit Cloud, Render, or Railway.

### Deploy to Streamlit Cloud

1. Push this repo to GitHub.
2. Open Streamlit Cloud.
3. Create a new app and select this repository.
4. Set the main file to `streamlit_app.py`.
5. Add your environment variables if needed.

### Local streamlit run

```bash
streamlit run streamlit_app.py
```

This Streamlit interface reuses the same ACC knowledge base and AI logic, but presents it in a simpler, deploy-friendly dashboard format.

## Environment variables

Create a `.env` file based on `.env.example`:

```env
GEMINI_API_KEY=
OPENAI_API_KEY=
GROQ_API_KEY=
DEFAULT_LLM_PROVIDER=local
```

If no keys are provided, the app automatically uses the built-in ACC knowledge synthesizer.

## Available APIs

- `GET /health` — service health status
- `GET /api/programs` — list ACC programs
- `POST /api/career-match` — skill-to-track recommendations
- `POST /api/chat` — conversational chat with document-aware answers
- `GET /api/documents` — indexed document and page metadata
- `GET /api/documents/pdf/{name}` — serve a specific PDF
- `GET /api/config/status` — LLM backend availability

## Demo highlights

- Student internship guide for 2027–2029 batches
- Free vs paid program clarity and scam policy messaging
- AI-powered answers for job readiness and DataYug options
- Program matching for graduates and transitioning professionals

## Notes

This project is designed for ACC-related knowledge retrieval and program discovery. It is intended to support the official mission of helping students build job-ready analytics skills.

## Contributing

Contributions are welcome. To improve the project:

1. fork the repository
2. create a feature branch
3. make your changes
4. add or update tests if needed
5. open a pull request

## License

This repository is currently shared for educational and project demonstration purposes.
