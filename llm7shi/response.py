# Response dataclass for LLM API interactions
from dataclasses import dataclass, field
from typing import List, Optional, Any


@dataclass
class Response:
    """Response object containing the results from LLM API calls.
    
    Attributes:
        model: The model used for generation
        config: The configuration object used (provider-specific)
        contents: The input contents sent to the API
        response: The raw API response object
        chunks: List of all streaming chunks received
        thoughts: The thinking process text (if include_thoughts=True)
        text: The final generated text
        repetition: Whether repetitive patterns were detected during generation
        max_length: Set to the length limit if generation was truncated (None for normal completion)
        data: Parsed JSON content of text (dict/list, or a Pydantic instance when a
            Pydantic schema was used), set when a schema is passed to Client.__call__
    """
    model: Optional[str] = None
    config: Optional[Any] = None  # provider-specific objects stay Any; only common fields are standardized
    contents: Optional[List[Any]] = None
    response: Optional[Any] = None
    chunks: List[Any] = field(default_factory=list)
    thoughts: str = ""
    text: str = ""
    repetition: bool = False  # distinguishes early termination (repetition loop) from normal completion
    max_length: Optional[int] = None  # set only when truncated by max_length; None means natural completion
    data: Optional[Any] = None

    def __str__(self) -> str:
        """Return the text content when converting to string."""
        return self.text  # print(response) shows text directly, no need for response.text
    
    def __repr__(self) -> str:
        """Return a concise representation showing contents and text."""
        if self.contents is None:
            contents_repr = "None"
        else:
            contents_repr = str(self.contents[0])
            if len(contents_repr) > 10:
                contents_repr = contents_repr[:10] + "..."
        
        text_repr = self.text
        if len(text_repr) > 10:
            text_repr = text_repr[:10] + "..."
        
        return f"Response(contents={contents_repr!r}, text={text_repr!r})"
