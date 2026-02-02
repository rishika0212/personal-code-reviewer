# Coder - AI Code Review System

An intelligent code review system powered by multiple AI agents that analyze your code for bugs, security issues, and performance optimizations.

## Features

- 🔍 **Multi-Agent Review**: Specialized agents for different aspects of code quality
- 🐛 **Bug Detection**: Identifies potential bugs and code smells
- 🔐 **Security Analysis**: Finds security vulnerabilities
- ⚡ **Performance Optimization**: Suggests performance improvements
- 📊 **Visual Dashboard**: Interactive UI to explore review results

## Architecture

- **Backend**: FastAPI + ChromaDB + Ollama (Llama 3)
- **Frontend**: React + Vite + shadcn/ui + Tailwind CSS

## Quick Start

```bash
docker-compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

See `docs/architecture.md` for detailed documentation.
