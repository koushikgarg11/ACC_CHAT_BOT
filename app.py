"""
Entrypoint launcher for Analytics Career Connect AI Chatbot.
"""

import os
import sys
import uvicorn

sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 60)
    print("Starting Analytics Career Connect (ACC) AI Assistant")
    print("URL: http://localhost:8000")
    print("=" * 60)
    
    # Ensure knowledge base is indexed
    data_file = os.path.join(os.path.dirname(__file__), "app", "data", "knowledge_base.json")
    if not os.path.exists(data_file):
        print("Indexing knowledge base from PDFs and website...")
        from app.knowledge.indexer import build_knowledge_base
        build_knowledge_base()

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
