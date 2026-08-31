import json
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
        # kept inside history (not a separate field) so to_xml/load_xml round-trip it too
        if self.history and self.history[0].get('role') == 'system':
            self.history[0]['content'] = system_prompt
        else:
            self.history.insert(0, {'role': 'system', 'content': system_prompt})

    def should_retry(
        self,
        resp: Response,
        schema: Union[Dict[str, Any], Type[BaseModel], None] = None,
    ) -> Optional[str]:
        """Decide whether a response should be regenerated.

        Override in a subclass to customize quality checks.

        Args:
            resp: The response to evaluate
            schema: The schema passed to __call__. When given, resp.text is validated
                as JSON against it instead of the plain-text quality checks (Pydantic
                models are validated in full; dict JSON schemas are only checked for
                parseability)

        Returns:
            A reason string if the response should be retried, or None if it is acceptable.
        """
        # overridable so callers can swap in custom quality gates without duplicating the retry loop
        if schema is not None:
            # schema validity supersedes the text heuristics below (e.g. structured JSON can look "repetitive")
            try:
                if isinstance(schema, type) and issubclass(schema, BaseModel):
                    resp.data = schema.model_validate_json(resp.text)
                else:
                    resp.data = json.loads(resp.text)  # no schema-validation lib is a dependency, so parse-only
            except Exception as e:
                return f"invalid JSON ({e})"
            return None

        if resp.repetition:
            return "repetition"
        if resp.max_length is not None:
            return f"max_length ({self.max_length} chars) exceeded"
        if not resp.text.strip():
            return "empty reply"
        return None

    def __call__(
        self,
        # only turn-specific args here; session-wide config lives on self from __init__
        prompt: Union[str, List[str]],
        schema: Union[Dict[str, Any], Type[BaseModel], None] = None,
    ) -> Response:
        """Call LLM with quality retry and automatically add query/response to history.

        Args:
            prompt: A single user prompt string (`client("question")`), or a list
                of strings, each added as its own user-role message in the same
                turn, in list order (`client(["Essay:\\n" + essay, question])`).
                Splitting into multiple messages -- rather than one concatenated
                string -- matters for providers/models that treat message
                boundaries as structure (e.g. so a later message reads as "the
                question about the text above" rather than part of the text).
            schema: JSON schema for structured output, Pydantic model, or None for plain text

        Returns:
            The final checkable Response object
        """
        prompts = [prompt] if isinstance(prompt, str) else prompt
        prompt_messages = [{'role': 'user', 'content': p} for p in prompts]
        messages = self.history.copy() + prompt_messages

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

            reason = self.should_retry(resp, schema)
            if reason is None:
                break

            # Print warnings
            error(
                f"Client: attempt {attempt}/{self.retries} hit {reason}; regenerating",
                file=self.file
            )

        # Add to history
        self.history += prompt_messages
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
