# Demo Guide

1. Start the backend and frontend.
2. Open `http://localhost:5173`.
3. Go to Files and upload a Markdown, TXT, PDF, or Word document.
4. Return to Chat and ask a question about the uploaded content.
5. Toggle Agent Mode and enter: `帮我分析这个漏洞报告`.
6. Go to Reports to download the generated Markdown report.

The backend can run without an API key. In that mode, it returns a local fallback answer that includes the retrieved context summary. Configure `LLM_API_KEY` for full model responses.

