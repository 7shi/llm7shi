import sys
from typing import Optional, List, Any

from .response import Response

DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_RETRY_DELAY = 15


class StreamGenerator:
    """Unified base class for streaming LLM generation with retry and monitoring logic."""

    def __init__(
        self,
        *,
        model: Optional[str] = None,
        config: Optional[Any] = None,
        contents: Optional[List[Any]] = None,
        file = sys.stdout,
        max_length: Optional[int] = None,
        check_repetition: bool = True,
        message: str = "Retrying ({retry}/{max_retries})...",
    ):
        self.model = model
        self.config = config
        self.contents = contents
        self.file = file
        self.max_length = max_length
        self.check_repetition = check_repetition
        self.message = message

    def make_stream(self) -> Any:
        """Create and return the stream iterator. Must be implemented by subclasses."""
        raise NotImplementedError

    def process_chunk(self, chunk: Any, processor: Any) -> bool:
        """Process a single stream chunk. Return False to stop generation early. Must be implemented by subclasses."""
        raise NotImplementedError

    def handle_error(self, e: Exception) -> Optional[dict]:
        """Check if an exception is retryable. Return a dict {"status_code": int, "delay": Optional[int]} if retryable, or None if not."""
        raise NotImplementedError

    def finalize_stream(self, processor: Any) -> None:
        """Hook called after the stream is consumed successfully. Can be overridden by subclasses."""
        pass

    def generate(self) -> Response:
        """Run the streaming generation with retry loop and monitoring."""
        import sys
        from .terminal import wait_retry, error
        from .monitor import StreamProcessor

        last_exception = None
        for attempt in range(DEFAULT_MAX_ATTEMPTS, 0, -1):
            processor = StreamProcessor(
                file=self.file,
                max_length=self.max_length,
                check_repetition=self.check_repetition
            )
            chunks = []
            try:
                stream = self.make_stream()
                with processor:
                    for chunk in stream:
                        chunks.append(chunk)
                        if not self.process_chunk(chunk, processor):
                            if hasattr(stream, "close"):
                                stream.close()
                            elif hasattr(stream, "_client") and hasattr(stream._client, "close"):
                                stream._client.close()
                            break
                self.finalize_stream(processor)

                return Response(
                    model=self.model,
                    config=self.config,
                    contents=self.contents,
                    response=stream,
                    chunks=chunks,
                    thoughts=processor.thoughts,
                    text=processor.text,
                    repetition=processor.repetition_detected,
                    max_length=processor.max_length_exceeded,
                )

            except Exception as e:
                last_exception = e
                err_info = self.handle_error(e)
                if err_info is None:
                    raise
                
                status_code = err_info.get("status_code")
                delay = err_info.get("delay") or DEFAULT_RETRY_DELAY

                error(f"API Error ({status_code}): {e}", file=self.file)

                if attempt == 1:
                    continue

                retry = DEFAULT_MAX_ATTEMPTS - attempt + 1
                max_retries = DEFAULT_MAX_ATTEMPTS - 1
                message = self.message.format(retry=retry, max_retries=max_retries)
                wait_retry(delay, message=message, file=self.file)
                continue

        if last_exception:
            raise RuntimeError("Max retries exceeded.") from last_exception
        raise RuntimeError("Max retries exceeded.")
