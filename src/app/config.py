from dataclasses import dataclass, field

from environs import env

env.read_env()


@dataclass
class Config:
    BASE_URL: str = field(default_factory=lambda: env('BASE_URL'))
    API_KEY: str = field(default_factory=lambda: env('API_KEY'))
    MODEL_NAME: str = field(default_factory=lambda: env('MODEL_NAME'))


config = Config()
