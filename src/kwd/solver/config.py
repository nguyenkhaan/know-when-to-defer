"""Solver configuration (spec 07 §3–§4)."""

from pydantic import BaseModel, ConfigDict, Field


class SolverConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    solution_limit: int = Field(default=100, ge=1)
    time_limit_s: float = Field(default=10.0, gt=0)
    warm_start: bool = True
    first_solution: str = "PATH_CHEAPEST_ARC"
    late_penalty: float = Field(default=10.0, ge=0)
    shift_penalty: float = Field(default=10.0, ge=0)
    dev_weight: float = Field(default=2.0, ge=0)
