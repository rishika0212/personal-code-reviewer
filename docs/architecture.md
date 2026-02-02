# Coder Architecture

## Overview

Coder is a multi-agent AI code review system that analyzes repositories for bugs, security vulnerabilities, and performance issues.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│                    RepoUploader → Review Page                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ REST API
┌───────────────────────────▼─────────────────────────────────────┐
│                     FastAPI Backend                             │
├─────────────────────────────────────────────────────────────────┤
│  API Routes ──► Review Manager ──► Agents (Code/Security/Perf)  │
│       │              │                       │                  │
│       ▼              ▼                       ▼                  │
│  GitHub Loader    ChromaDB              Ollama (Llama 3)        │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### Frontend (React + Vite)
- **RepoUploader**: Upload GitHub repository URLs
- **FileTree**: Navigate repository structure
- **CodeViewer**: Display code with syntax highlighting
- **AgentComments**: Show review findings
- **SeverityBadge**: Visual severity indicators

### Backend (FastAPI)
- **API Layer**: REST endpoints for review operations
- **Loaders**: Clone and load GitHub repositories
- **Indexing**: Chunk code files and generate embeddings
- **Vector Store**: ChromaDB for semantic search
- **Agents**: Specialized AI reviewers
- **Orchestrator**: Coordinate multi-agent review

### AI Agents
1. **Code Analyzer**: Bugs, code smells, maintainability
2. **Security Agent**: OWASP vulnerabilities, security issues
3. **Optimization Agent**: Performance bottlenecks

## Data Flow

1. User submits GitHub URL
2. Backend clones repository
3. Code is chunked and indexed in ChromaDB
4. Review manager dispatches chunks to agents
5. Each agent analyzes code with Llama 3
6. Results are aggregated and returned
7. Frontend displays findings with code context

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| Backend | Python 3.11, FastAPI, Pydantic |
| Vector Store | ChromaDB |
| LLM | Ollama (Llama 3) |
| Containerization | Docker, Docker Compose |
