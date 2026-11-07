"""Append-only disk cache for deterministic solver calls (spec 07 §6)."""

import hashlib
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from kwd.data.models import RouteSnapshot
from kwd.dsl import EditSet, canonical
from kwd.solver.config import SolverConfig
from kwd.solver.tsptw import Infeasible, Plan, solve


def _key(p: RouteSnapshot, e: EditSet | None, cfg: SolverConfig) -> str:
    payload = {
        "snapshot_id": p.snapshot_id,
        "edit": canonical(e, p) if e is not None else None,
        "config": cfg.model_dump(mode="json"),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def solve_cached(
    p: RouteSnapshot,
    e: EditSet | None,
    cfg: SolverConfig,
    cache_dir: Path,
) -> Plan | Infeasible:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{_key(p, e, cfg)}.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        model = Plan if data.pop("kind") == "plan" else Infeasible
        return model.model_validate(data)

    result = solve(p, e, cfg)
    data = result.model_dump(mode="json")
    data["kind"] = "plan" if isinstance(result, Plan) else "infeasible"
    with NamedTemporaryFile(
        "w", encoding="utf-8", dir=cache_dir, prefix=f"{path.stem}.", suffix=".tmp", delete=False
    ) as output:
        json.dump(data, output, sort_keys=True)
        temporary = Path(output.name)
    temporary.replace(path)
    return result
