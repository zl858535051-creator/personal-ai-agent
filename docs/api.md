# API Reference

Base URL: `http://localhost:8000/api/v1`

## Files

- `POST /files/upload`: multipart upload field `file`.
- `GET /files`: list uploaded documents.
- `DELETE /files/{file_id}`: delete document, chunks, and vectors.

## Chat

- `POST /chat`

```json
{
  "message": "请总结我的知识库",
  "session_id": null,
  "use_knowledge_base": true
}
```

- `GET /chat/sessions`: list sessions.
- `GET /chat/sessions/{session_id}`: fetch one session.

## Knowledge

- `POST /knowledge/query`

```json
{
  "query": "漏洞影响范围",
  "top_k": 5
}
```

## Agent

- `POST /agent/run`

```json
{
  "task": "帮我分析这个漏洞报告",
  "generate_report": true
}
```

## Reports

- `POST /reports`: create Markdown or PDF report.
- `GET /reports`: list reports.
- `GET /reports/{report_id}/download`: download report file.

