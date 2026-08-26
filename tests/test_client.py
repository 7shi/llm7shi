"""
Tests for Client, the stateful/callable chat execution wrapper.

Covers history tracking, config propagation, system-prompt mutation, and XML
persistence — checked for reliability and symmetry (e.g. copy() must deep-copy
history so mutating the copy never leaks into the original).
"""

import pytest
from unittest.mock import MagicMock, patch, ANY
from llm7shi.client import Client
from llm7shi.response import Response

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
