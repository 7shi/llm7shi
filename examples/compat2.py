from typing import List
from pydantic import BaseModel, Field
from llm7shi.compat import generate_with_schema
from llm7shi import create_json_descriptions_prompt

class LocationTemperature(BaseModel):
    reasoning: str
    location: str
    temperature: float = Field(description="Temperature in Celsius")

class LocationsAndTemperatures(BaseModel):
    locations_and_temperatures: List[LocationTemperature]

# Create enhanced prompt with field descriptions
json_descriptions = create_json_descriptions_prompt(LocationsAndTemperatures)

generate_with_schema(
    ["The temperature in Tokyo is 90 degrees Fahrenheit.", json_descriptions],
    schema=LocationsAndTemperatures,
    model="ollama:",
)
