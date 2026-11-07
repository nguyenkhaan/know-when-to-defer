"""Configuration of the data pipeline, read from `configs/data.yaml` (spec 14 §2).

Every value comes from the YAML: the models have no defaults, so a missing key is an error.
"""

import hashlib
import json
from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator


class _Section(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SelectionConfig(_Section):
    seed: int
    pilot_n: int = Field(ge=1)
    reserve_frac: float = Field(ge=0)
    min_stops: int = Field(ge=1)
    max_stops: int = Field(ge=1)


class SnapshotConfig(_Section):
    seed: int
    rho_min: float = Field(ge=0, lt=1)
    rho_max: float = Field(ge=0, lt=1)
    shift_slack_min: int = Field(ge=0)
    min_remaining: int = Field(ge=1)

    @model_validator(mode="after")
    def _ordered(self) -> Self:
        if self.rho_min > self.rho_max:
            raise ValueError("rho_min must not exceed rho_max")
        return self


class DataConfig(_Section):
    raw_dir: Path
    interim_dir: Path
    selection: SelectionConfig
    snapshot: SnapshotConfig

    @field_serializer("raw_dir", "interim_dir")
    def _posix(self, path: Path) -> str:
        return path.as_posix()


def load_data_config(path: Path) -> DataConfig:
    return DataConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def config_hash(cfg: DataConfig) -> str:
    """sha256 of the resolved config, so comments and key order in the YAML do not change it."""
    resolved = json.dumps(cfg.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(resolved.encode()).hexdigest()
