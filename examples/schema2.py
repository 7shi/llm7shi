"""
Same structured-extraction task as schema1.py, but schema defined via Pydantic
instead of a JSON Schema file: type hints give IDE completion/type checking
and avoid hand-maintaining schema JSON, at the cost of an external
dependency. See also: schema1.py for the reasoning-first, item-level ordering
rationale (`reasoning` field placed first in LocationTemperature).
"""

from typing import List
from pydantic import BaseModel, Field
from llm7shi import config_from_schema, generate_content_retry

class LocationTemperature(BaseModel):
    reasoning: str  # first field, so the model reasons before filling in values (see schema1.md)
    location: str
    temperature: float = Field(description="Temperature in Celsius")

class LocationsAndTemperatures(BaseModel):
    locations_and_temperatures: List[LocationTemperature]

generate_content_retry(
    ["The temperature in Tokyo is 90 degrees Fahrenheit."],
    config=config_from_schema(LocationsAndTemperatures),
)
