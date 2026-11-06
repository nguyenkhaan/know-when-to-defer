"""Phase 0b smoke test: hand-written requests -> M1, M2 -> a table to grade by eye.

One-off script (plans/phase-0b-smoke-test.md, Step 3): no cache, no tests.

    uv run python scripts/smoke_translate.py prepare   # items_draft.txt -> items.jsonl (+ checks)
    uv run python scripts/smoke_translate.py run       # items.jsonl -> outputs.jsonl, review.md

Files live in data/smoke/ (not committed). Prompt follows spec 10 §3.
"""

import argparse
import difflib
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "data" / "smoke"
KINDS = {"time_direction", "indirect", "confusable", "relative_time", "compound", "implicit"}
# op -> argument names, in the order used by items_draft.txt
OPS = {
    "set_time_window": ["stop", "start", "end"],
    "deadline": ["stop", "time"],
    "remove_stop": ["stop"],
    "precedence": ["before", "after"],
    "driver_end_time": ["time"],
    "avoid_zone_until": ["zone", "time"],
    "service_time": ["stop", "minutes"],
}
TIME = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
SYSTEM = """You convert a dispatcher's request into route edits.
Output ONLY a JSON object: {"edits": [<edit>, ...], "confidence": <0-100>}
Allowed edits (1 to 4 per request):
  {"op": "set_time_window", "stop": S, "start": T|null, "end": T|null}  arrive at S within [start, end]; null = open side
  {"op": "deadline", "stop": S, "time": T}            arrive at S no later than T
  {"op": "remove_stop", "stop": S}                    S is not visited
  {"op": "precedence", "before": S, "after": S}       visit `before` before `after`
  {"op": "driver_end_time", "time": T}                vehicle back at depot by T
  {"op": "avoid_zone_until", "zone": Z, "time": T}    no arrival at any stop in zone Z before T
  {"op": "service_time", "stop": S, "minutes": N}     service duration at S becomes N minutes
Use stop names exactly as listed. Times are local HH:MM (24h).
"confidence" = how sure you are (0-100) that the edits match the request."""


def load_routes() -> dict[str, dict]:
    """routes.md -> {route: {"text": section shown to the LLM, "stops": set, "zones": set}}."""
    routes, name = {}, None
    for line in (SMOKE / "routes.md").read_text().splitlines():
        if line.startswith("## "):
            name = line[3:].strip()
            routes[name] = {"lines": [], "stops": set(), "zones": set()}
        elif name:
            routes[name]["lines"].append(line)
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 4 and cells[0].isdigit():
                routes[name]["stops"].add(cells[1])
                routes[name]["zones"].add(cells[3])
    for r in routes.values():
        r["text"] = "\n".join(r.pop("lines")).strip()
    return routes


def parse_edit(line: str, route: dict) -> tuple[dict | None, str | None]:
    m = re.fullmatch(r"(\w+)\((.*)\)", line.strip())
    if not m or m[1] not in OPS:
        return None, f"lệnh không hợp lệ: {line.strip()!r}"
    names, args = OPS[m[1]], [a.strip() for a in m[2].split(",")]
    if len(args) != len(names):
        return None, f"{m[1]} cần {len(names)} tham số ({', '.join(names)}), có {len(args)}"
    edit = {"op": m[1]}
    for key, val in zip(names, args):
        if key in ("stop", "before", "after"):
            if val not in route["stops"]:
                near = difflib.get_close_matches(val, route["stops"], n=1, cutoff=0.6)
                hint = f" (ý bạn là {near[0]!r}?)" if near else ""
                return None, f"không có điểm {val!r} trong tuyến{hint}"
        elif key in ("start", "end", "time"):
            if val == "null" and key != "time":
                val = None
            elif not TIME.match(val):
                return None, f"giờ sai định dạng: {val!r} (cần HH:MM)"
        elif key == "zone" and val not in route["zones"]:
            return None, f"không có khu {val!r}"
        elif key == "minutes":
            if not val.isdigit():
                return None, f"số phút phải là số nguyên: {val!r}"
            val = int(val)
        edit[key] = val
    if m[1] == "set_time_window" and edit["start"] is None and edit["end"] is None:
        return None, "set_time_window cần ít nhất một trong start/end"
    return edit, None


def prepare() -> int:
    routes, items, errors, empty = load_routes(), [], [], 0
    current = None
    for no, line in enumerate((SMOKE / "items_draft.txt").read_text().splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.lstrip().startswith("->"):
            body = line.split("->", 1)[1].strip()
            if current is None or not body:
                continue
            edit, err = parse_edit(body, routes[current["route"]])
            if err:
                errors.append(f"dòng {no} ({current['id']}): {err}")
            else:
                current["gold"]["edits"].append(edit)
            continue
        parts = [p.strip() for p in line.split("|", 3)]
        if len(parts) != 4:
            errors.append(f"dòng {no}: cần dạng 'id | route | kind | câu'")
            current = None
            continue
        sid, route, kind, q = parts
        if route not in routes or kind not in KINDS:
            errors.append(f"dòng {no} ({sid}): route {route!r} hoặc kind {kind!r} không hợp lệ")
            current = None
            continue
        current = {"id": sid, "route": route, "kind": kind, "q": q, "gold": {"edits": []}}
        items.append(current)

    done = []
    for it in items:
        if not it["q"] and not it["gold"]["edits"]:
            empty += 1
        elif not it["q"] or not it["gold"]["edits"]:
            errors.append(f"{it['id']}: thiếu {'câu' if not it['q'] else 'đáp án'}")
        else:
            done.append(it)
    ids = [it["id"] for it in done]
    errors += [f"trùng id {i}" for i in sorted({i for i in ids if ids.count(i) > 1})]

    by_route = {r: sum(it["route"] == r for it in done) for r in routes}
    by_kind = {k: sum(it["kind"] == k for it in done) for k in sorted(KINDS)}
    print(f"Câu đã viết: {len(done)}  (khung còn trống: {empty})")
    print("Theo tuyến:", by_route)
    print("Theo nhóm: ", by_kind)
    if errors:
        print(f"\n{len(errors)} lỗi, chưa ghi items.jsonl:")
        print("\n".join("  - " + e for e in errors))
        return 1
    with open(SMOKE / "items.jsonl", "w") as f:
        f.writelines(json.dumps(it, ensure_ascii=False) + "\n" for it in done)
    print(f"\nOK -> {SMOKE / 'items.jsonl'}")
    return 0


def call(client: httpx.Client, spec: dict, route_text: str, q: str) -> str:
    body = {
        "model": spec["model"],
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f'{route_text}\n\nRequest: "{q}"'},
        ],
        "temperature": 0,
        "seed": 0,
        "max_tokens": 600,
        "response_format": {"type": "json_object"},
        "provider": {
            "order": [spec["endpoint"]],
            "allow_fallbacks": False,
            "require_parameters": True,
        },
        **{k: v for k, v in spec.get("params", {}).items() if k != "logprobs"},
    }
    for attempt in range(5):
        try:
            resp = client.post("/chat/completions", json=body)
            data = resp.json()
            if resp.status_code == 200 and "choices" in data:
                return (data["choices"][0]["message"].get("content") or "").strip()
            err = data.get("error", resp.text[:200])
        except (httpx.HTTPError, ValueError) as exc:
            err = str(exc)
        time.sleep(2**attempt * 3)  # 3, 6, 12, 24, 48 s: rides out 429 rate limits
    return f"<API error: {err}>"


def parsed(raw: str) -> dict | None:
    try:
        out = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(out, dict) or not isinstance(out.get("edits"), list):
        return None
    return out if all(isinstance(e, dict) and e.get("op") in OPS for e in out["edits"]) else None


def canon(edits: list[dict]) -> list[str]:
    """Rough canonical form for the hint column only (grading is still by eye)."""
    out = []
    for e in edits:
        e = dict(e)
        if e.get("op") == "deadline":
            e = {
                "op": "set_time_window",
                "stop": e.get("stop"),
                "start": None,
                "end": e.get("time"),
            }
        out.append(json.dumps(e, sort_keys=True))
    return sorted(set(out))


def short(edits: list[dict]) -> str:
    return "<br>".join(
        f"{e.get('op')}("
        + ", ".join("null" if v is None else str(v) for k, v in e.items() if k != "op")
        + ")"
        for e in edits
    )


def run(models: list[str], retry_failed: bool = False) -> int:
    config = yaml.safe_load((ROOT / "configs" / "llm.yaml").read_text())
    for line in (ROOT / ".env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("'\""))
    routes = load_routes()
    items = [json.loads(x) for x in (SMOKE / "items.jsonl").read_text().splitlines() if x]
    headers = {"Authorization": f"Bearer {os.environ[config['backend']['api_key_env']]}"}
    rows, results = [], {}
    previous = {}
    if retry_failed and (SMOKE / "outputs.jsonl").exists():
        for line in (SMOKE / "outputs.jsonl").read_text().splitlines():
            r = json.loads(line)
            if not r["raw"].startswith("<API error"):
                previous[(r["id"], r["model"])] = r["raw"]
    with (
        httpx.Client(
            base_url=config["backend"]["base_url"], headers=headers, timeout=120
        ) as client,
        ThreadPoolExecutor(4) as pool,
    ):
        for m in models:
            spec = config["models"][m]

            def get(it, s=spec, m=m):
                if (it["id"], m) in previous:
                    return previous[(it["id"], m)]
                return call(client, s, routes[it["route"]]["text"], it["q"])

            raws = list(pool.map(get, items))
            for it, raw in zip(items, raws):
                p = parsed(raw)
                results[(it["id"], m)] = p
                rows.append(
                    {
                        "id": it["id"],
                        "model": m,
                        "model_id": spec["model"],
                        "raw": raw,
                        "parsed_ok": p is not None,
                    }
                )
            print(
                f"{m}: {sum(r['parsed_ok'] for r in rows if r['model'] == m)}/{len(items)} "
                "parsed OK"
            )
    with open(SMOKE / "outputs.jsonl", "w") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)

    cols = []
    for m in models:
        cols += [f"{m} trả về", f"{m} conf", f"{m} tự so", f"{m} đánh giá"]
    lines = [
        "# Smoke test review",
        "",
        "Nhãn: ✅ đúng · 🟡 sai vô hại · 🔴 sai có hại (ghi loại lỗi) · ⚪ hỏng.",
        "Cột 'tự so' chỉ là gợi ý (= khớp đáp án sau khi đổi deadline → set_time_window).",
        "",
        "| id | tuyến | nhóm | câu | đáp án | " + " | ".join(cols) + " |",
        "|" + "---|" * (5 + len(cols)),
    ]
    for it in items:
        cells = [
            it["id"],
            it["route"],
            it["kind"],
            it["q"].replace("|", "/"),
            short(it["gold"]["edits"]),
        ]
        for m in models:
            p = results[(it["id"], m)]
            if p is None:
                cells += [
                    "⚪ "
                    + next(r["raw"] for r in rows if r["id"] == it["id"] and r["model"] == m)[
                        :80
                    ].replace("|", "/"),
                    "",
                    "",
                    "",
                ]
            else:
                same = canon(p["edits"]) == canon(it["gold"]["edits"])
                cells += [short(p["edits"]), str(p.get("confidence", "")), "=" if same else "≠", ""]
        lines.append("| " + " | ".join(cells) + " |")
    (SMOKE / "review.md").write_text("\n".join(lines) + "\n")
    print(f"-> {SMOKE / 'review.md'}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 0b smoke test")
    parser.add_argument("command", choices=["prepare", "run"])
    parser.add_argument("--models", nargs="+", default=["M1", "M2"])
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="reuse outputs.jsonl; only re-call rows that hit an API error",
    )
    args = parser.parse_args()
    sys.exit(prepare() if args.command == "prepare" else run(args.models, args.retry_failed))
