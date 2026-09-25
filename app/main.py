"""FastAPI routes for the existing generator and the new word-vector endpoint."""

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request

from app.bigram_model import BigramModel
from app.embeddings import (
    MODEL_NAME,
    InvalidWordError,
    UnknownWordError,
    WordEmbeddingService,
)
from app.schemas import (
    EmbeddingResponse,
    HealthResponse,
    TextGenerationRequest,
    TextGenerationResponse,
)

CORPUS = [
    "The cat reads books",
    "The dog reads notes",
    "The cat writes notes",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.embeddings = WordEmbeddingService()
    app.state.bigram = BigramModel(CORPUS)
    yield
    del app.state.embeddings
    del app.state.bigram


app = FastAPI(
    title="Assignment 1: Word Embeddings API",
    description="spaCy static word vectors and the course bigram generator.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", tags=["Status"])
def read_root():
    return {"message": "Assignment 1 API is running", "documentation": "/docs"}


@app.get("/health", response_model=HealthResponse, tags=["Status"])
def health(request: Request):
    service = request.app.state.embeddings
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "model_version": service.model_version,
        "dimensions": service.dimensions,
    }


@app.get(
    "/embedding",
    response_model=EmbeddingResponse,
    tags=["Word embeddings"],
    responses={
        404: {"description": "No pretrained vector exists for the word."},
        422: {"description": "A single alphabetic word is required."},
    },
)
def get_embedding(
    request: Request,
    word: Annotated[
        str,
        Query(min_length=1, max_length=100, description="One English word, for example apple"),
    ],
):
    """Return all 300 components of the lowercase word's static embedding."""
    try:
        return request.app.state.embeddings.embed(word)
    except InvalidWordError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except UnknownWordError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/generate", response_model=TextGenerationResponse, tags=["Text generation"])
def generate_text(request: Request, body: TextGenerationRequest):
    """Sample up to length words from the small course bigram model."""
    try:
        generated = request.app.state.bigram.generate_text(body.start_word, body.length)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"generated_text": generated}
