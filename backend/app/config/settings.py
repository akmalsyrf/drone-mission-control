"""Application settings — simulation vs production profiles."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr, TypeAdapter
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.domain.value_objects import AdapterType


def _postgres_dsn(value: str) -> PostgresDsn:
    return TypeAdapter(PostgresDsn).validate_python(value)


def _redis_dsn(value: str) -> RedisDsn:
    return TypeAdapter(RedisDsn).validate_python(value)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "DroneMissionControl"
    app_env: Literal["simulation", "development", "staging", "production", "test"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    log_json: bool = False

    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://localhost",
        ]
    )

    database_url: Annotated[
        PostgresDsn,
        Field(
            default_factory=lambda: _postgres_dsn(
                "postgresql+asyncpg://dmc:dmc@localhost:5432/drone_mission_control"
            )
        ),
    ]
    redis_url: Annotated[
        RedisDsn,
        Field(default_factory=lambda: _redis_dsn("redis://localhost:6379/0")),
    ]

    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_topic_prefix: str = "dmc/telemetry"
    mqtt_enabled: bool = True

    jwt_secret: SecretStr = Field(default=SecretStr("change-me-in-production"))
    jwt_algorithm: str = "HS256"

    # Simulation (PX4 SITL + Gazebo) vs hardware endpoints
    drone_default_adapter: AdapterType = AdapterType.SIMULATED
    mavsdk_sim_address: str = "udpin://0.0.0.0:14540"
    mavsdk_hw_address: str = "serial:///dev/ttyUSB0:921600"
    telemetry_publish_hz: float = 5.0

    redis_telemetry_channel: str = "dmc:telemetry"
    redis_telemetry_ttl_seconds: int = 30

    @property
    def is_simulation(self) -> bool:
        return self.app_env in {"simulation", "development", "test"}

    @property
    def default_connection_uri(self) -> str:
        if self.drone_default_adapter == AdapterType.PX4 and not self.is_simulation:
            return self.mavsdk_hw_address
        if self.drone_default_adapter == AdapterType.SIMULATED:
            return "simulated://local"
        return self.mavsdk_sim_address


@lru_cache
def get_settings() -> Settings:
    return Settings()
