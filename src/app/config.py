from dataclasses import dataclass, field

from environs import env

env.read_env()


@dataclass
class Config:
    CHROME_PATH: str = field(default_factory=lambda: env('CHROME_PATH'))
    USER_DATA_DIR: str = field(default_factory=lambda: env('USER_DATA_DIR'))
    BASE_URL: str = field(default_factory=lambda: env('BASE_URL'))
    API_KEY: str = field(default_factory=lambda: env('API_KEY'))
    MODEL_NAME: str = field(default_factory=lambda: env('MODEL_NAME'))


config = Config()
