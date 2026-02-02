# API Contract

## Base URL
```
http://localhost:8000/api
```

## Endpoints

### Repository Management

#### Upload GitHub Repository
```http
POST /repo/github
Content-Type: application/json

{
  "url": "https://github.com/owner/repo",
  "branch": "main"  // optional, defaults to "main"
}
```

**Response**:
```json
{
  "repo_id": "a1b2c3d4",
  "name": "repo",
  "url": "https://github.com/owner/repo",
  "files_count": 42,
  "languages": ["Python", "JavaScript"]
}
```

#### Get Repository Files
```http
GET /repo/files/{repo_id}
```

**Response**:
```json
{
  "repo_id": "a1b2c3d4",
  "files": [
    {
      "name": "src",
      "type": "directory",
      "path": "src",
      "children": [
        {
          "name": "main.py",
          "type": "file",
          "path": "src/main.py"
        }
      ]
    }
  ]
}
```

---

### Review Management

#### Start Review
```http
POST /review/
Content-Type: application/json

{
  "repo_id": "a1b2c3d4",
  "files": ["src/main.py"],  // optional, review all if omitted
  "agents": ["code", "security"]  // optional, run all if omitted
}
```

**Response**:
```json
{
  "review_id": "r1e2v3i4",
  "status": "started"
}
```

#### Get Review Status
```http
GET /review/status/{review_id}
```

**Response**:
```json
{
  "review_id": "r1e2v3i4",
  "status": "processing",  // pending | processing | completed | failed
  "progress": 45,          // 0-100
  "error": null            // error message if failed
}
```

#### Get Review Results
```http
GET /review/{review_id}
```

**Response**:
```json
{
  "review_id": "r1e2v3i4",
  "repo_id": "a1b2c3d4",
  "status": "completed",
  "total_findings": 12,
  "severity_counts": {
    "critical": 1,
    "high": 3,
    "medium": 5,
    "low": 2,
    "info": 1
  },
  "findings": [
    {
      "id": "f1i2n3d4",
      "severity": "high",
      "category": "security",
      "title": "SQL Injection Vulnerability",
      "description": "User input is directly concatenated into SQL query...",
      "file_path": "src/db.py",
      "start_line": 42,
      "end_line": 45,
      "suggestion": "Use parameterized queries instead...",
      "code_snippet": "query = f\"SELECT * FROM users WHERE id = {user_id}\""
    }
  ]
}
```

---

### Health Check

```http
GET /health
```

**Response**:
```json
{
  "status": "healthy"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Status Codes**:
- `400`: Bad Request (invalid input)
- `404`: Not Found (review/repo not found)
- `500`: Internal Server Error

---

## WebSocket (Future)

Real-time review updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/review/{review_id}')

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  // { type: 'progress', progress: 45 }
  // { type: 'finding', finding: {...} }
  // { type: 'complete', results: {...} }
}
```

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| POST /repo/github | 10/minute |
| POST /review/ | 5/minute |
| GET /* | 100/minute |
