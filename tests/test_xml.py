from xml.dom.minidom import parseString
from llm7shi.xml import messages_to_xml, xml_to_str, xml_to_messages

def test_history_serialization_roundtrip():
    # Custom CDATA escape/unescape must not lose or corrupt a literal "]]>" in content
    history = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello! Let's write some code: ]]>"},
        {"role": "assistant", "content": "Sure, we can use CDATA blocks like this: ]]> or maybe ]]>."}
    ]
    
    doc = messages_to_xml(history)
    xml_str = xml_to_str(doc)
    
    # Check that it serialized and escaped CDATA inside the text,
    # but the overall CDATA blocks still terminate correctly.
    assert "]] >" in xml_str
    
    # Parse and restore symmetrically using Document boundaries
    parsed_doc = parseString(xml_str)
    restored = xml_to_messages(parsed_doc)
    
    # Suffix newline is kept.
    expected = [
        {"role": "system", "content": "You are a helpful assistant.\n"},
        {"role": "user", "content": "Hello! Let's write some code: ]]>\n"},
        {"role": "assistant", "content": "Sure, we can use CDATA blocks like this: ]]> or maybe ]]>.\n"}
    ]
    assert restored == expected

def test_messages_to_xml_with_response():
    # Strict line-by-line check: stray indentation or newline drift degrades raw log
    # readability and can break downstream parsers
    messages = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "User prompt"}
    ]
    response = "Assistant response"
    
    doc = messages_to_xml(messages, response=response)
    xml_str = xml_to_str(doc)
    
    # Expect formatting to match flat style (no indent, but with newlines)
    expected_lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<messages>',
        '<message role="system"><![CDATA[',
        'System prompt',
        ']]></message>',
        '<message role="user"><![CDATA[',
        'User prompt',
        ']]></message>',
        '<message role="assistant"><![CDATA[',
        'Assistant response',
        ']]></message>',
        '</messages>',
        ''
    ]
    assert xml_str.split('\n') == expected_lines

def test_messages_to_xml_str_input():
    prompt = "Simple user prompt"
    doc = messages_to_xml(prompt)
    xml_str = xml_to_str(doc)
    
    expected_lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<messages>',
        '<message role="user"><![CDATA[',
        'Simple user prompt',
        ']]></message>',
        '</messages>',
        ''
    ]
    assert xml_str.split('\n') == expected_lines

def test_empty_content_handling():
    history = [
        {"role": "user", "content": ""},
        {"role": "assistant", "content": "   "}
    ]
    doc = messages_to_xml(history)
    xml_str = xml_to_str(doc)
    
    parsed_doc = parseString(xml_str)
    restored = xml_to_messages(parsed_doc)
    
    expected = [
        {"role": "user", "content": "\n"},
        {"role": "assistant", "content": "\n"}
    ]
    assert restored == expected
