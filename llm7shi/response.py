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
    """
    model: Optional[str] = None
    config: Optional[Any] = None
    contents: Optional[List[Any]] = None
    response: Optional[Any] = None
    chunks: List[Any] = field(default_factory=list)
    thoughts: str = ""
    text: str = ""
    repetition: bool = False
    max_length: Optional[int] = None
    
    def __str__(self) -> str:
        """Return the text content when converting to string."""
        return self.text
    
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
