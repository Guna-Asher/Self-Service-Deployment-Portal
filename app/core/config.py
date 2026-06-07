from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Deployment Portal"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/deployment_portal"

    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 1800

    DOCKER_SOCKET: str = "unix:///var/run/docker.sock"
    DEFAULT_PORT_BINDING: str = "80:8080"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()