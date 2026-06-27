import sys
from typing import List, Dict, Optional, Any, Union, Type
from xml.dom.minidom import parseString
from pydantic import BaseModel

from .response import Response
from .compat import generate_with_schema
from .xml import messages_to_xml, xml_to_str, xml_to_messages
from .terminal import error

DEFAULT_LLM_RETRIES = 3

class Client:
    def __init__(
        self,
        model: str = "",
        include_thoughts: bool = True,
        temperature: Optional[float] = None,
        thinking_budget: Optional[int] = None,
        file = sys.stdout,
        show_params: bool = True,
        max_length: Optional[int] = None,
        check_repetition: bool = True,
        # Extended arguments
        retries: int = DEFAULT_LLM_RETRIES,
    ):
        self.model = model
        self.include_thoughts = include_thoughts
        self.temperature = temperature
        self.thinking_budget = thinking_budget
        self.file = file
        self.show_params = show_params
        self.max_length = max_length
        self.check_repetition = check_repetition
        self.retries = retries
        self.history: List[Dict[str, str]] = []

    def copy(self) -> 'Client':
        """Create a copy of the Client with the same config and history."""
        new_client = Client(
            model=self.model,
            include_thoughts=self.include_thoughts,
            temperature=self.temperature,
            thinking_budget=self.thinking_budget,
            file=self.file,
            show_params=self.show_params,
            max_length=self.max_length,
            check_repetition=self.check_repetition,
            retries=self.retries
        )
        new_client.history = self.history.copy()
        return new_client

    def set_system_prompt(self, system_prompt: str) -> None:
        """Set or update the system prompt at the beginning of the history.

        If the history starts with a system prompt, it is replaced.
        Otherwise, a new system prompt is inserted at the beginning.
        """
        if self.history and self.history[0].get('role') == 'system':
            self.history[0]['content'] = system_prompt
        else:
            self.history.insert(0, {'role': 'system', 'content': system_prompt})

    def __call__(
        self,
        prompt: str,
        schema: Union[Dict[str, Any], Type[BaseModel], None] = None,
    ) -> Response:
        """Call LLM with quality retry and automatically add query/response to history.

        Args:
            prompt: User prompt text
            schema: JSON schema for structured output, Pydantic model, or None for plain text

        Returns:
            The final checkable Response object
        """
        messages = self.history.copy()
        messages.append({'role': 'user', 'content': prompt})

        # Quality retry loop
        for attempt in range(1, self.retries + 1):
            resp = generate_with_schema(
                messages,
                schema=schema,
                model=self.model,
                temperature=self.temperature,
                include_thoughts=self.include_thoughts,
                thinking_budget=self.thinking_budget,
                show_params=self.show_params,
                max_length=self.max_length,
                check_repetition=self.check_repetition,
                file=self.file
            )

            # Quality checks
            if not resp.repetition and resp.max_length is None and resp.text.strip():
                break

            if resp.repetition:
                reason = "repetition"
            elif resp.max_length is not None:
                reason = f"max_length ({self.max_length} chars) exceeded"
            else:
                reason = "empty reply"

            # Print warnings
            error(
                f"Client: attempt {attempt}/{self.retries} hit {reason}; regenerating",
                file=self.file
            )
        
        # Add to history
        self.history.append({'role': 'user', 'content': prompt})
        self.history.append({'role': 'assistant', 'content': resp.text.strip()})

        return resp

    def to_xml(self) -> str:
        """Serialize current history to a flat XML string."""
        doc = messages_to_xml(self.history)
        return xml_to_str(doc)

    def load_xml(self, xml_string: str) -> None:
        """Load history from a flat XML string."""
        doc = parseString(xml_string)
        self.history = xml_to_messages(doc)
