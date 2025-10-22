"""Tests for gpt-oss template filter."""

import pytest
from unittest.mock import patch, MagicMock
from llm7shi.monitor import GptOssTemplateFilter
from llm7shi.openai import generate_content


def test_basic_channel_switching():
    """Test basic channel switching between analysis and final."""
    filter = GptOssTemplateFilter()

    # Analysis channel
    output = filter.feed('<|channel|>')
    assert output == ''

    output = filter.feed('analysis')
    assert output == ''

    output = filter.feed('<|message|>')
    assert output == ''

    output = filter.feed('This is analysis.')
    assert output == ''
    assert filter.thoughts == 'This is analysis.'

    # Switch to final channel
    output = filter.feed('<|channel|>')
    assert output == ''

    output = filter.feed('final')
    assert output == ''

    output = filter.feed('<|message|>')
    assert output == ''

    output = filter.feed('This is final.')
    assert output == 'This is final.'
    assert filter.text == 'This is final.'


def test_multiple_chunks():
    """Test processing content split into multiple chunks."""
    filter = GptOssTemplateFilter()

    chunks = [
        '<|channel|>',
        'analysis',
        '<|message|>',
        'The',
        ' user',
        ' wants',
        ' greeting',
        '<|channel|>',
        'final',
        '<|message|>',
        'Hello',
        '!',
    ]

    output_parts = []
    for chunk in chunks:
        output = filter.feed(chunk)
        if output:
            output_parts.append(output)

    assert filter.thoughts == 'The user wants greeting'
    assert filter.text == 'Hello!'
    assert ''.join(output_parts) == 'Hello!'


def test_start_token_with_role():
    """Test <|start|> token followed by role name."""
    filter = GptOssTemplateFilter()

    output = filter.feed('<|start|>')
    assert output == ''

    output = filter.feed('assistant')
    assert output == ''

    output = filter.feed('<|channel|>')
    assert output == ''

    output = filter.feed('final')
    assert output == ''

    output = filter.feed('<|message|>')
    assert output == ''

    output = filter.feed('Hello')
    assert output == 'Hello'
    assert filter.text == 'Hello'


def test_no_channel_defaults_to_text():
    """Test that content without channel goes to text."""
    filter = GptOssTemplateFilter()

    output = filter.feed('Direct text')
    assert output == 'Direct text'
    assert filter.text == 'Direct text'
    assert filter.thoughts == ''


def test_control_token_across_chunks():
    """Test control token split across multiple chunks."""
    filter = GptOssTemplateFilter()

    # Split <|channel|> token
    output = filter.feed('<|chan')
    assert output == ''

    output = filter.feed('nel|>')
    assert output == ''

    output = filter.feed('analysis')
    assert output == ''

    output = filter.feed('text')
    assert output == ''
    assert filter.thoughts == 'text'


def test_flush():
    """Test flushing remaining buffer."""
    filter = GptOssTemplateFilter()

    # Set to final channel
    filter.feed('<|channel|>')
    filter.feed('final')
    filter.feed('<|message|>')

    # Add content but keep some in buffer
    filter.feed('Hello <|')

    # Flush should output remaining content
    remaining = filter.flush()
    assert remaining == '<|'
    assert filter.text == 'Hello <|'


def test_complex_scenario():
    """Test complex real-world scenario."""
    filter = GptOssTemplateFilter()

    # Simulate real gpt-oss output
    chunks = [
        '<|channel|>',
        'analysis',
        '<|message|>',
        'User asks for greeting. ',
        'Should respond politely.',
        '<|start|>',
        'assistant',
        '<|channel|>',
        'final',
        '<|message|>',
        'Hello! ',
        'How can I help you?',
    ]

    final_output = []
    for chunk in chunks:
        output = filter.feed(chunk)
        if output:
            final_output.append(output)

    assert filter.thoughts == 'User asks for greeting. Should respond politely.'
    assert filter.text == 'Hello! How can I help you?'
    assert ''.join(final_output) == 'Hello! How can I help you?'


def test_end_token():
    """Test <|end|> token is properly filtered."""
    filter = GptOssTemplateFilter()

    filter.feed('<|channel|>')
    filter.feed('final')
    filter.feed('<|message|>')
    filter.feed('Hello')

    output = filter.feed('<|end|>')
    assert output == ''
    assert filter.text == 'Hello'


def test_multiple_roles():
    """Test different role names (user, system, assistant)."""
    filter = GptOssTemplateFilter()

    # Test 'user' role
    filter.feed('<|start|>')
    filter.feed('user')
    filter.feed('<|channel|>')
    filter.feed('final')
    filter.feed('Hi')

    assert filter.text == 'Hi'

    # Test 'system' role
    filter2 = GptOssTemplateFilter()
    filter2.feed('<|start|>')
    filter2.feed('system')
    filter2.feed('<|message|>')
    filter2.feed('Test')

    assert filter2.text == 'Test'


def test_partial_role_name():
    """Test partial role name in buffer."""
    filter = GptOssTemplateFilter()

    filter.feed('<|start|>')
    filter.feed('ass')  # Partial 'assistant'
    filter.feed('istant')
    filter.feed('<|channel|>')
    filter.feed('final')
    filter.feed('text')

    assert filter.text == 'text'


def test_empty_chunks():
    """Test handling of empty chunks."""
    filter = GptOssTemplateFilter()

    output = filter.feed('')
    assert output == ''

    filter.feed('<|channel|>')
    filter.feed('final')

    output = filter.feed('')
    assert output == ''

    filter.feed('text')
    assert filter.text == 'text'


def test_long_content():
    """Test with longer content in each channel."""
    filter = GptOssTemplateFilter()

    analysis_text = "This is a detailed analysis. " * 10
    final_text = "This is the final response. " * 10

    filter.feed('<|channel|>')
    filter.feed('analysis')
    filter.feed('<|message|>')
    filter.feed(analysis_text)

    filter.feed('<|channel|>')
    filter.feed('final')
    filter.feed('<|message|>')
    output = filter.feed(final_text)

    assert filter.thoughts == analysis_text
    assert filter.text == final_text
    assert output == final_text


class TestFilterActivation:
    """Test filter activation based on model name."""

    @patch('llm7shi.openai.OpenAI')
    def test_filter_activates_for_llama_cpp_gpt_oss(self, mock_openai_class):
        """Test that filter activates for model name 'llama.cpp/gpt-oss'."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Simulate gpt-oss template output
        mock_chunks = [
            self._create_chunk('<|channel|>'),
            self._create_chunk('analysis'),
            self._create_chunk('<|message|>'),
            self._create_chunk('Thinking...'),
            self._create_chunk('<|channel|>'),
            self._create_chunk('final'),
            self._create_chunk('<|message|>'),
            self._create_chunk('Hello!'),
        ]
        mock_client.chat.completions.create.return_value = iter(mock_chunks)

        # Call with llama.cpp/gpt-oss model
        result = generate_content(
            messages=[{"role": "user", "content": "Test"}],
            model="llama.cpp/gpt-oss",
            file=None
        )

        # Filter should activate: control tokens removed, thoughts separated
        assert result.thoughts == 'Thinking...'
        assert result.text == 'Hello!'
        assert '<|channel|>' not in result.text
        assert '<|message|>' not in result.text

    @patch('llm7shi.openai.OpenAI')
    def test_filter_does_not_activate_for_other_models(self, mock_openai_class):
        """Test that filter does NOT activate for other model names."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Simulate gpt-oss template output (same as above)
        mock_chunks = [
            self._create_chunk('<|channel|>'),
            self._create_chunk('analysis'),
            self._create_chunk('<|message|>'),
            self._create_chunk('Thinking...'),
            self._create_chunk('<|channel|>'),
            self._create_chunk('final'),
            self._create_chunk('<|message|>'),
            self._create_chunk('Hello!'),
        ]
        mock_client.chat.completions.create.return_value = iter(mock_chunks)

        # Call with different model name
        result = generate_content(
            messages=[{"role": "user", "content": "Test"}],
            model="gpt-oss:120b",
            file=None
        )

        # Filter should NOT activate: control tokens remain in text
        assert result.thoughts == ''
        assert '<|channel|>' in result.text
        assert '<|message|>' in result.text
        assert 'Thinking...' in result.text
        assert 'Hello!' in result.text

    @patch('llm7shi.openai.OpenAI')
    def test_filter_does_not_activate_for_standard_models(self, mock_openai_class):
        """Test that filter does NOT activate for standard OpenAI models."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Normal OpenAI response without control tokens
        mock_chunks = [
            self._create_chunk('Hello,'),
            self._create_chunk(' world!'),
        ]
        mock_client.chat.completions.create.return_value = iter(mock_chunks)

        # Call with standard model name
        result = generate_content(
            messages=[{"role": "user", "content": "Test"}],
            model="gpt-4",
            file=None
        )

        # No filter: normal text passthrough
        assert result.thoughts == ''
        assert result.text == 'Hello, world!'

    def _create_chunk(self, content):
        """Helper to create a mock chunk."""
        chunk = MagicMock()
        chunk.choices = [MagicMock()]
        chunk.choices[0].delta = MagicMock()
        chunk.choices[0].delta.content = content
        return chunk
