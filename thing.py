from pydantic import BaseModel


def add(one, two):
    return one - two


class WeatherParams(BaseModel):
    city: str


def weather(params: WeatherParams):
    return f"The weather in {params.city} is sunny with a high of 2°C."


def load_file(file_path: str):
    with open(file_path) as f:
        return f.read()
