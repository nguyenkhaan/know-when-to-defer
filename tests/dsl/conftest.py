from pathlib import Path

import pytest

from kwd.data.lmrc import load_route
from kwd.data.models import RouteSnapshot
from kwd.data.snapshot import build_snapshot, load_fixture_snapshot

MINI = Path(__file__).parent.parent / "fixtures" / "lmrc_mini"
MINI_ROUTE = "RouteID_00143bdd-0a6b-49ec-bb35-36593d303e77"


@pytest.fixture
def hospital() -> RouteSnapshot:
    """Departs 13:00:00, t_now = 13:00, shift ends 17:30, zones A and B, nothing done yet."""
    return load_fixture_snapshot("hospital")


@pytest.fixture
def mini(tmp_path) -> RouteSnapshot:
    """Real route departing 09:02:10 local, with three done stops (TG, GP, HT)."""
    return build_snapshot(load_route(MINI, MINI_ROUTE), 0.25, 0, travel_dir=tmp_path)
