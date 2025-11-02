# AI Trader Backend

Python backend for AI Trader system.

## Setup

```bash
pip install -r requirements.txt
```

## Running

```bash
python run.py
```

## Testing

```bash
# Run all tests
python -m tests.run_all

# Run specific test
python tests/test_02_discussion_rounds.py
```

## Project Structure

```
backend/
├── src/          # Source code
│   ├── agents/   # Agent implementations
│   ├── tools/    # Tool modules
│   ├── data/     # Data layer
│   ├── llm/      # LLM client
│   ├── core/     # Core services (Event Bus)
│   ├── api/      # FastAPI server
│   └── utils/    # Utilities
├── config/       # Configuration files
├── data/         # Data directory
├── tests/        # Test files
├── prompts/      # Prompt templates
├── scripts/     # Utility scripts
└── run.py        # Entry point
```
