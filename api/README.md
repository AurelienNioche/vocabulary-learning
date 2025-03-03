# Vocabulary Learning API

A FastAPI backend for the Japanese vocabulary learning application.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure Firebase (optional):
- Create a Firebase project
- Download service account key JSON
- Set environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

3. Run the server:
```bash
uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoints

#### Vocabulary Management

- `GET /vocabulary`: Get list of all vocabulary words
- `GET /vocabulary/{word}`: Get details for a specific word
- `POST /vocabulary`: Add a new word
- `PUT /vocabulary/{word}`: Update an existing word
- `DELETE /vocabulary/{word}`: Delete a word
- `GET /vocabulary/search/{query}`: Search vocabulary

#### Practice

- `GET /practice/words`: Get words for practice session
- `POST /practice/result`: Submit practice result
- `GET /practice/stats`: Get practice statistics
- `GET /practice/suggestions/{word}`: Get similar word suggestions

### Data Models

#### WordEntry

```json
{
  "word": "string",
  "translations": ["string"],
  "example_sentences": [["japanese", "french"]]
}
```

#### PracticeResult

```json
{
  "word": "string",
  "success": true
}
```

## Development

The API is built with:
- FastAPI for the web framework
- Pydantic for data validation
- Firebase Admin SDK for cloud storage (optional)
- Rich for console output

### Project Structure

```
api/
├── main.py              # FastAPI application
└── README.md           # This file

vocabulary_learning/
├── core/               # Core business logic
│   ├── progress_tracking.py
│   └── vocabulary.py
└── services/          # Service layer
    ├── practice_service.py
    ├── progress_service.py
    └── vocabulary_service.py
```

### Adding New Features

1. Add core logic in `vocabulary_learning/core/`
2. Create/update services in `vocabulary_learning/services/`
3. Add endpoints in `api/main.py`
4. Update documentation

## Testing

Run tests with:
```bash
pytest
```

Coverage reports will be generated in `test-results/` 