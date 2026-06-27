import re
from xml.dom.minidom import Document

def escape_cdata_content(s: str) -> str:
    """Escape CDATA end tags (]]>) to prevent XML parsing issues.
    
    Inserts a space before the final '>' of any ']]>' sequence.
    """
    if not isinstance(s, str):
        s = str(s)
    return re.sub(r"\]\](\s*)\>", lambda m: f"]]{m.group(1)} >", s)

def unescape_cdata_content(s: str) -> str:
    """Restore escaped CDATA end tags by removing the inserted space."""
    if not isinstance(s, str):
        s = str(s)
    return re.sub(r"\]\](\s*)\s\>", lambda m: f"]]{m.group(1)}>", s)

def messages_to_xml(messages, response: str = None) -> Document:
    """Convert messages (list of dicts, or a single prompt string) and an optional
    assistant response to a minidom Document object.
    """
    doc = Document()
    messages_el = doc.createElement("messages")
    doc.appendChild(messages_el)

    def prepare_text(s: str) -> str:
        if not isinstance(s, str):
            s = str(s)
        # rstrip to prevent duplicate newlines, then wrap with \n for readability
        return f"\n{escape_cdata_content(s.rstrip())}\n"

    # Append input messages
    if isinstance(messages, list):
        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                msg_el = doc.createElement("message")
                msg_el.setAttribute("role", role)
                cdata = doc.createCDATASection(prepare_text(content))
                msg_el.appendChild(cdata)
                messages_el.appendChild(msg_el)
    elif isinstance(messages, str):
        msg_el = doc.createElement("message")
        msg_el.setAttribute("role", "user")
        cdata = doc.createCDATASection(prepare_text(messages))
        msg_el.appendChild(cdata)
        messages_el.appendChild(msg_el)

    # Append assistant response if provided
    if response is not None:
        msg_el = doc.createElement("message")
        msg_el.setAttribute("role", "assistant")
        cdata = doc.createCDATASection(prepare_text(response))
        msg_el.appendChild(cdata)
        messages_el.appendChild(msg_el)

    return doc

def xml_to_str(doc: Document) -> str:
    """Serialize a minidom Document to a flat XML string (no indentation, newline-separated)."""
    return doc.toprettyxml(indent="", encoding="utf-8").decode("utf-8")

def xml_to_messages(doc: Document) -> list:
    """Convert a minidom Document back to LLM interaction messages, unescaping CDATA tags.

    Args:
        doc: minidom Document representing the messages

    Returns:
        List of message dictionaries with 'role' and 'content'
    """
    history = []
    for message in doc.getElementsByTagName("message"):
        role = message.getAttribute("role")
        content = ""
        for child in message.childNodes:
            if child.nodeType == child.CDATA_SECTION_NODE:
                content = child.data
                content = content.removeprefix("\n")
                content = unescape_cdata_content(content)
                break
        history.append({"role": role, "content": content})
    return history
