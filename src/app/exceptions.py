class VectorDBError(Exception):
    """Raised when the vector database is unavailable or returns an unexpected error."""


class LLMError(Exception):
    """Raised when the LLM service is unavailable or returns an unexpected response."""


class IngestError(Exception):
    """Raised when repo ingestion fails due to a non-recoverable error."""
