"""configs/llm.yaml respects the roster rules of spec 10 §2 and the 10 USD budget."""

from pathlib import Path

import yaml

CONFIG = yaml.safe_load((Path(__file__).parents[1] / "configs" / "llm.yaml").read_text())
MODELS = CONFIG["models"]


def test_roster_has_five_models():
    assert set(MODELS) == {"M1", "M2", "M3", "M4", "M5"}


def test_budget_fits_total_with_reserve():
    allocated = sum(m["max_usd"] for m in MODELS.values())
    assert allocated + CONFIG["budget"]["reserve_usd"] <= CONFIG["budget"]["total_usd"]


def test_m1_requests_logprobs():
    assert MODELS["M1"]["params"]["logprobs"] is True


def test_support_models_are_from_other_families():
    translators = {MODELS["M1"]["family"], MODELS["M2"]["family"]}
    assert MODELS["M3"]["family"] not in translators
    assert MODELS["M4"]["family"] not in translators
    assert MODELS["M3"]["family"] != MODELS["M4"]["family"]


def test_api_models_pin_an_endpoint_and_price():
    for model_id, m in MODELS.items():
        if m.get("local"):
            continue
        assert "/" in m["endpoint"], model_id
        assert m["price"]["input"] > 0 and m["price"]["output"] > 0, model_id
        assert m["max_usd"] > 0, model_id
