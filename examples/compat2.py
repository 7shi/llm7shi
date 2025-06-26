from typing import List
from pydantic import BaseModel, Field
from llm7shi.compat import generate_with_schema

class LocationTemperature(BaseModel):
    location: str
    temperature: float = Field(description="Temperature in Celsius")

class LocationsAndTemperatures(BaseModel):
    locations_and_temperatures: List[LocationTemperature]

generate_with_schema(
    ["The temperature in Tokyo is 90 degrees Fahrenheit."],
    schema=LocationsAndTemperatures,
    model="gemini-2.5-flash",
)
print("=" * 40)
generate_with_schema(
    ["The temperature in Tokyo is 90 degrees Fahrenheit."],
    schema=LocationsAndTemperatures,
    model="gpt-4.1-mini",
)
