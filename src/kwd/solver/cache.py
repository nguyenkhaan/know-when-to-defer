"""Append-only disk cache for deterministic solver calls (spec 07 §6).

Several processes may read and write one key at once. On Windows a file that another process has
open cannot be replaced, and a file being replaced cannot be opened: both raise `PermissionError`
for a moment. Results are deterministic, so whichever writer lands first gives the right entry.
"""

import hashlib
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import sleep

from kwd.data.models import RouteSnapshot
from kwd.dsl import EditSet, canonical
from kwd.solver.config import SolverConfig
from kwd.solver.tsptw import Infeasible, Plan, solve

_ATTEMPTS = 20
_RETRY_WAIT_S = 0.05


def _key(p: RouteSnapshot, e: EditSet | None, cfg: SolverConfig) -> str:
    payload = {
        "snapshot_id": p.snapshot_id,
        "edit": canonical(e, p) if e is not None else None,
        "config": cfg.model_dump(mode="json"),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _read(path: Path) -> Plan | Infeasible | None:
    """Return the cached result, or None if the key has no entry yet."""
    for attempt in range(1, _ATTEMPTS + 1):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except PermissionError:
            if attempt == _ATTEMPTS:
                raise
            sleep(_RETRY_WAIT_S)
        else:
            model = Plan if data.pop("kind") == "plan" else Infeasible
            return model.model_validate(data)
    raise AssertionError("unreachable")


def _publish(temporary: Path, path: Path) -> None:
    """Move `temporary` to `path`, or drop it if another writer already published the key."""
    try:
        for attempt in range(1, _ATTEMPTS + 1):
            try:
                temporary.replace(path)
                return
            except PermissionError:
                if path.exists():
                    return
                if attempt == _ATTEMPTS:
                    raise
                sleep(_RETRY_WAIT_S)
    finally:
        temporary.unlink(missing_ok=True)


def solve_cached(
    p: RouteSnapshot,
    e: EditSet | None,
    cfg: SolverConfig,
    cache_dir: Path,
) -> Plan | Infeasible:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{_key(p, e, cfg)}.json"
    cached = _read(path)
    if cached is not None:
        return cached

    result = solve(p, e, cfg)
    data = result.model_dump(mode="json")
    data["kind"] = "plan" if isinstance(result, Plan) else "infeasible"
    with NamedTemporaryFile(
        "w", encoding="utf-8", dir=cache_dir, prefix=f"{path.stem}.", suffix=".tmp", delete=False
    ) as output:
        json.dump(data, output, sort_keys=True)
        temporary = Path(output.name)
    _publish(temporary, path)
    return result
