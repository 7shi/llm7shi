"""
Tests for Client, the stateful/callable chat execution wrapper.

Covers history tracking, config propagation, system-prompt mutation, and XML
persistence — checked for reliability and symmetry (e.g. copy() must deep-copy
history so mutating the copy never leaks into the original).
"""

import io
import pytest
from unittest.mock import MagicMock, patch, ANY
from pydantic import BaseModel, Field
from llm7shi.client import Client
from llm7shi.response import Response
from llm7shi.usage import Usage

def test_client_init_and_copy():
    # Pass various parameters to test init & copy
    client = Client(
        model="google:gemini-2.5-flash",
        include_thoughts=True,
        temperature=0.7,
        thinking_budget=1024,
        show_params=True,
        check_repetition=False
    )
    client.set_system_prompt("Initial System")
    client.history.append({"role": "user", "content": "hello"})
    
    copied = client.copy()
    assert copied.model == client.model
    assert copied.include_thoughts == client.include_thoughts
    assert copied.temperature == client.temperature
    assert copied.thinking_budget == client.thinking_budget
    assert copied.show_params == client.show_params
    assert copied.check_repetition == client.check_repetition
    assert copied.history == client.history
    
    # Verify deep copy of history list
    copied.history.append({"role": "assistant", "content": "hi"})
    assert len(client.history) == 2
    assert len(copied.history) == 3

def test_client_set_system_prompt():
    client = Client(model="dummy")

    # Must insert/replace at index 0 without disturbing later turns, or history order corrupts
    # 1. Insert new system prompt into empty history
    client.set_system_prompt("System V1")
    assert len(client.history) == 1
    assert client.history[0] == {"role": "system", "content": "System V1"}
    
    # 2. Replace existing system prompt
    client.set_system_prompt("System V2")
    assert len(client.history) == 1
    assert client.history[0] == {"role": "system", "content": "System V2"}
    
    # 3. Add regular turns, then replace system prompt
    client.history.append({"role": "user", "content": "Hi"})
    client.set_system_prompt("System V3")
    assert len(client.history) == 2
    assert client.history[0] == {"role": "system", "content": "System V3"}
    assert client.history[1] == {"role": "user", "content": "Hi"}

@patch("llm7shi.client.generate_with_schema")
def test_client_call_success_and_history(mock_generate):
    mock_resp = Response(
        text="Hello back!",
        thoughts="Thinking process",
        repetition=False,
        max_length=None
    )
    mock_generate.return_value = mock_resp
    
    client = Client(model="dummy-model", include_thoughts=True)
    client.set_system_prompt("System instructions")
    resp = client(prompt="Hi")
    
    assert resp == mock_resp
    # History should contain system prompt, user prompt, and assistant response
    expected_history = [
        {"role": "system", "content": "System instructions"},
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello back!"}
    ]
    assert client.history == expected_history
    
    # Next call (history already exists, so system prompt shouldn't be duplicated)
    mock_generate.return_value = Response(text="Fine, thanks", repetition=False, max_length=None)
    client(prompt="How are you?")
    
    expected_history.extend([
        {"role": "user", "content": "How are you?"},
        {"role": "assistant", "content": "Fine, thanks"}
    ])
    assert client.history == expected_history

@patch("llm7shi.client.generate_with_schema")
def test_client_call_keep_history_false(mock_generate):
    mock_generate.return_value = Response(text="Answer", repetition=False, max_length=None)

    client = Client(model="dummy-model", keep_history=False)
    client.set_system_prompt("System instructions")
    client(prompt="First")
    client(prompt="Second")

    # Turns are not recorded, so the system prompt is all that remains
    assert client.history == [{"role": "system", "content": "System instructions"}]
    # ...and each call still carries it, without the earlier turn
    assert mock_generate.call_args[0][0] == [
        {"role": "system", "content": "System instructions"},
        {"role": "user", "content": "Second"}
    ]
    assert client.copy().keep_history is False

class _Answer(BaseModel):
    reasoning: str = Field(description="Why this answer was chosen")
    answer: str = Field(description="The final answer")

@patch("llm7shi.client.generate_with_schema")
def test_client_call_add_json_descriptions(mock_generate):
    mock_generate.return_value = Response(
        text='{"reasoning": "because", "answer": "42"}', repetition=False, max_length=None
    )

    client = Client(model="dummy-model", add_json_descriptions=True)
    client(prompt="Question", schema=_Answer)

    # Descriptions are appended as their own trailing user message, for providers
    # (e.g. Ollama) that use the schema only to constrain decoding and never show
    # its `description` fields to the model
    sent = mock_generate.call_args[0][0]
    assert sent[0] == {"role": "user", "content": "Question"}
    assert len(sent) == 2
    assert sent[1]["role"] == "user"
    assert "Why this answer was chosen" in sent[1]["content"]
    assert "The final answer" in sent[1]["content"]
    # ...and history records what was actually sent
    assert client.history[:2] == sent

    assert client.copy().add_json_descriptions is True

@patch("llm7shi.client.generate_with_schema")
def test_client_call_add_json_descriptions_default_off(mock_generate):
    mock_generate.return_value = Response(
        text='{"reasoning": "because", "answer": "42"}', repetition=False, max_length=None
    )

    # Default must not alter the prompt actually sent (backward compatibility)
    client = Client(model="dummy-model")
    client(prompt="Question", schema=_Answer)
    assert mock_generate.call_args[0][0] == [{"role": "user", "content": "Question"}]

@patch("llm7shi.client.generate_with_schema")
def test_client_call_add_json_descriptions_without_schema(mock_generate):
    mock_generate.return_value = Response(text="Answer", repetition=False, max_length=None)

    # Nothing to describe without a schema
    client = Client(model="dummy-model", add_json_descriptions=True)
    client(prompt="Question")
    assert mock_generate.call_args[0][0] == [{"role": "user", "content": "Question"}]

@patch("llm7shi.client.generate_with_schema")
def test_client_call_parameter_propagation(mock_generate):
    mock_generate.return_value = Response(text="Success", repetition=False, max_length=None)
    
    client = Client(
        model="test-model",
        include_thoughts=False,
        temperature=0.9,
        thinking_budget=256,
        show_params=True,
        check_repetition=False,
        max_length=10000
    )
    
    # Call directly
    client(prompt="Test")

    # Confirms Client instance settings propagate down to generate_with_schema
    # Verify overrides were passed to generate_with_schema
    mock_generate.assert_called_once_with(
        [{"role": "user", "content": "Test"}],
        schema=None,
        model="test-model",
        temperature=0.9,
        include_thoughts=False,
        thinking_budget=256,
        show_params=True,
        max_length=10000,
        check_repetition=False,
        file=ANY
    )

@patch("llm7shi.client.generate_with_schema")
def test_client_call_quality_retry(mock_generate):
    # Confirms history is only appended with the final successful response, not failed retries.
    # First attempt: repetition. Second attempt: empty text. Third attempt: success.
    mock_generate.side_effect = [
        Response(text="repeat repeat", repetition=True, max_length=None),
        Response(text="   ", repetition=False, max_length=None),
        Response(text="Success response", repetition=False, max_length=None)
    ]
    
    client = Client(model="dummy-model", include_thoughts=False, retries=3)
    with patch("llm7shi.client.error") as mock_error:
        resp = client(prompt="Start")
        assert resp.text == "Success response"
        assert mock_generate.call_count == 3
        # Should have called error warning 2 times
        assert mock_error.call_count == 2

@patch("llm7shi.client.generate_with_schema")
def test_client_usages_include_retries(mock_generate):
    # Retried attempts consumed tokens too, so they must count toward the total
    # even though the caller only ever sees the final Response
    mock_generate.side_effect = [
        Response(text="   ", repetition=False, max_length=None, usage=Usage(raw={"input_tokens": 10, "output_tokens": 1})),
        Response(text="OK", repetition=False, max_length=None, usage=Usage(raw={"input_tokens": 10, "output_tokens": 5})),
        Response(text="No usage", repetition=False, max_length=None),
    ]
    client = Client(model="dummy-model", retries=3)
    with patch("llm7shi.client.error"):
        client(prompt="First")
    client(prompt="Second")  # a response without usage adds nothing

    assert len(client.usages) == 2
    assert sum(client.usages).to_dict() == {"input_tokens": 20, "output_tokens": 6, "total_tokens": 26}

@patch("llm7shi.client.generate_with_schema")
def test_client_show_usage(mock_generate):
    usage = Usage(raw={"input_tokens": 3, "output_tokens": 2})
    mock_generate.return_value = Response(text="OK", repetition=False, max_length=None, usage=usage)
    out = io.StringIO()
    Client(model="dummy-model", file=out)(prompt="Hi")
    assert out.getvalue() == ""  # off by default
    Client(model="dummy-model", file=out, show_usage=True)(prompt="Hi")
    assert out.getvalue() == f"\n{usage}\n"
    assert Client(show_usage=True).copy().show_usage is True

def test_client_copy_starts_with_empty_usages():
    client = Client(model="dummy-model")
    client.usages.append(Usage(raw={"input_tokens": 1}))
    assert client.copy().usages == []

def test_client_xml_serialization_roundtrip():
    client = Client(model="dummy", include_thoughts=False)
    client.history = [
        {"role": "system", "content": "Sys prompt"},
        {"role": "user", "content": "Hello! ]]>"},
        {"role": "assistant", "content": "Hi! ]]>"}
    ]
    
    xml_str = client.to_xml()
    assert "]] >" in xml_str
    
    new_client = Client(model="dummy", include_thoughts=False)
    new_client.load_xml(xml_str)
    
    expected = [
        {"role": "system", "content": "Sys prompt\n"},
        {"role": "user", "content": "Hello! ]]>\n"},
        {"role": "assistant", "content": "Hi! ]]>\n"}
    ]
    assert new_client.history == expected
