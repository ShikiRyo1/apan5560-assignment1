# Assignment 1: Word Embeddings API

This project adds a spaCy word-vector endpoint to the course FastAPI application. It also keeps the existing bigram text generator.

Repository: https://github.com/ShikiRyo1/apan5560-assignment1

The repository is public, so a reviewer can view or clone it directly. The submitted source ZIP is self-contained: extract it, open a terminal in the directory containing `pyproject.toml`, and follow either run method below. A GitHub login is not required to run the extracted project.

## Requirements

- Python 3.12 and [uv](https://docs.astral.sh/uv/getting-started/installation/), or Docker with Linux containers.
- Internet access for the first dependency installation or image build. The English model download is about 382 MB; installation and container layers require additional space.
- Port 8000 available on the host.

The project pins spaCy 3.8.16 and `en_core_web_lg` 3.8.0. The official model wheel is declared in `pyproject.toml`; `uv.lock` locks the full dependency set. No API key or Hugging Face account is needed. After installation, vector lookups run locally without network requests.

## Run locally

Open a terminal in this project's directory:

```powershell
uv sync --frozen
uv run --frozen uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Wait for `Application startup complete`, then open:

- Interactive API documentation: http://127.0.0.1:8000/docs
- Readiness check: http://127.0.0.1:8000/health
- Example word: http://127.0.0.1:8000/embedding?word=apple

The model loads once per server process during application startup. The endpoint excludes unnecessary tagging, parsing, and entity-recognition components while retaining the tokenizer and pretrained static vectors.

## Run with Docker

From this project's directory:

```powershell
docker build -t assignment1-embedding-api .
docker run --rm --name assignment1-embedding-api -p 127.0.0.1:8000:8000 assignment1-embedding-api
```

Alternatively:

```powershell
docker compose up --build
```

The image includes Python, the application, locked dependencies, and the English vector model. The first build downloads the model. The server listens on `0.0.0.0:8000` inside the container so Docker can forward requests to it; the host mapping `127.0.0.1:8000:8000` exposes it only on the host's loopback interface. The image runs as a non-root user and includes a `/health` check. Allow up to 90 seconds for the initial model load.

Use `Ctrl+C` to stop the foreground server. For Compose, run `docker compose down` afterward to remove the stopped container and project network.

## API contract

| Method and path | Input | Output |
|---|---|---|
| `GET /embedding` | Required query parameter `word` | Word, normalized word, model, version, dimensions, and complete vector |
| `POST /generate` | JSON with `start_word` and `length` | `generated_text` sampled from the course bigram model |
| `GET /health` | None | Loaded model name, version, dimension, and status |
| `GET /docs` | None | Swagger UI for trying the endpoints |

### Word embedding

In Swagger UI, expand `GET /embedding`, select **Try it out**, enter `apple` in `word`, and select **Execute**. A successful response has HTTP status 200, `dimensions: 300`, and a `vector` array containing all 300 floating-point components.

The equivalent PowerShell request is:

```powershell
$result = Invoke-RestMethod 'http://127.0.0.1:8000/embedding?word=apple'
$result.dimensions
$result.vector.Count
$result.vector[0..4]
```

The first two output values should both be `300`. The final line displays only the first five components for convenience; the HTTP response contains the full vector.

The endpoint trims surrounding whitespace and converts the word to lowercase. It requires one alphabetic token; sentences, punctuation, numeric inputs, missing input, and inputs over 100 characters return HTTP 422. An alphabetic word absent from the model's vector table returns HTTP 404, rather than an invented vector or a misleading zero vector.

These are **static embeddings**: the same normalized word has the same vector in every request. This endpoint does not compute context-dependent Transformer embeddings, generate text, or train a new model. Vector coordinates are numerical features, not individually named semantic properties.

### Existing text generation

The original corpus is deliberately small. Try `the`, `cat`, `dog`, `reads`, or `writes` as a starting word. `length` is a maximum word count from 1 to 50; generation can stop earlier at the end-of-sentence token.

```powershell
$body = @{start_word='the'; length=5} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/generate' -ContentType 'application/json' -Body $body
```

Different calls can produce different valid sentences because generation samples from empirical bigram counts.

## Tests

```powershell
uv run --frozen pytest -q
```

Tests use the real installed model. They compare API vectors for three words with a separately loaded spaCy reference model, check the 300-dimensional response, verify normalization and model reuse, exercise invalid and unknown inputs, check the health and OpenAPI routes, and confirm valid bigram transitions and error handling. No vector responses are mocked.

Verified on September 25, 2026: all 18 tests passed on Python 3.12.13. Docker build and container startup also succeeded, with `/health` reporting a loaded 300-dimensional model and `/embedding?word=apple` returning HTTP 200. The test run emitted one Starlette notice about a future test-client dependency change; it did not affect the assertions or the running API.

## Project structure

```text
app/
  main.py          Application lifecycle and HTTP routes
  embeddings.py    Model loading, input rules, and vector lookup
  bigram_model.py  Existing course bigram algorithm
  schemas.py       Typed request and response schemas
tests/test_api.py  Tests using real spaCy vectors
pyproject.toml     Direct dependencies and project configuration
uv.lock           Exact dependency resolution
Dockerfile        Reproducible container build
compose.yaml      Local container startup and port mapping
```

## Troubleshooting

- **Model not found:** run `uv sync --frozen` in the project directory. Avoid launching an unrelated global Python interpreter.
- **Port already in use:** stop the other server, or use local port 8001. For Docker, change the mapping to `127.0.0.1:8001:8000` and visit port 8001.
- **Docker daemon unavailable:** start Docker Desktop and wait for the Linux engine to become ready before building.
- **First install is slow:** the official vector model is large. Keep the download running and ensure the configured cache and target drive have free space.
- **404 for a word:** try a common English word such as `apple`; this means that the requested word has no stored vector, not that the API route is missing.

## References

- [spaCy English models](https://spacy.io/models/en)
- [Official en_core_web_lg 3.8.0 release and wheel checksum](https://github.com/explosion/spacy-models/releases/tag/en_core_web_lg-3.8.0)
- [FastAPI query parameters](https://fastapi.tiangolo.com/tutorial/query-params/)
- [FastAPI lifespan events](https://fastapi.tiangolo.com/advanced/events/)
- [Using uv in Docker](https://docs.astral.sh/uv/guides/integration/docker/)

The bigram implementation is adapted from the local Week 2 word-sampling practical and the course setup example. The embedding endpoint is the Assignment 1 extension.
