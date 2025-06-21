from typing import List
from pydantic import BaseModel, Field
from llm7shi import config_from_schema, generate_content_retry

class LocationTemperature(BaseModel):
    location: str
    temperature: float = Field(description="Temperature in Celsius")

class LocationsAndTemperatures(BaseModel):
    locations_and_temperatures: List[LocationTemperature]

generate_content_retry(
    ["The temperature in Tokyo is 90 degrees Fahrenheit."],
    config=config_from_schema(LocationsAndTemperatures),
)
