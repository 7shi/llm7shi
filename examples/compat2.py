from typing import List
from pydantic import BaseModel, Field
from llm7shi.compat import generate_with_schema

class LocationTemperature(BaseModel):
    location: str
    temperature: float = Field(description="Temperature in Celsius")

class LocationsAndTemperatures(BaseModel):
    locations_and_temperatures: List[LocationTemperature]

models = [
    "google:gemini-2.5-flash",
    "openai:gpt-4o-mini",
    "ollama:qwen3:4b"
]

for i, model in enumerate(models):
    if i:
        print("", "=" * 60, "", sep="\n")
    generate_with_schema(
        ["The temperature in Tokyo is 90 degrees Fahrenheit."],
        schema=LocationsAndTemperatures,
        model=model,
    )
