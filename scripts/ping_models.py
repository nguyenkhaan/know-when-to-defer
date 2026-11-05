"""Task 0.3 Step 3: check that M1-M4 answer through OpenRouter and M5 runs on CPU.

For each API model: sends one short JSON-mode prompt twice with the same seed, pinned to the
endpoint in configs/llm.yaml (no fallbacks), and prints latency, tokens, cost, the provider that
served it, whether log-probs came back, whether reasoning tokens were billed, and whether the
two seeded answers match. Then loads bge-small-en-v1.5 and encodes two sentences.

Usage (from the repository root, OPENROUTER_API_KEY in .env):
    uv run python scripts/ping_models.py [--only M1 M2 ...] [--skip-embedding]
Exit code 1 if any check fails. Cost: well under 0.01 USD.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[1]
PROMPT = (
    'Return ONLY this JSON object, filling in the time: {"stop": "Mercy Hospital", '
    '"not_before": "<HH:MM>"}. Request: "Don\'t send anyone to Mercy Hospital until 3 pm."'
)


def load_env(path: Path) -> None:
    """Minimal .env reader (KEY=VALUE lines); existing environment variables win."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def chat(client: httpx.Client, spec: dict) -> tuple[dict, float]:
    body = {
        "model": spec["model"],
        "messages": [{"role": "user", "content": PROMPT}],
        "temperature": 0,
        "seed": 0,
        "max_tokens": 200,
        "response_format": {"type": "json_object"},
        "provider": {
            "order": [spec["endpoint"]],
            "allow_fallbacks": False,
            "require_parameters": True,
        },
        **spec.get("params", {}),
    }
    start = time.perf_counter()
    resp = client.post("/chat/completions", json=body)
    latency = time.perf_counter() - start
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"API error: {data['error']}")
    return data, latency


def ping_api_model(client: httpx.Client, model_id: str, spec: dict) -> bool:
    print(f"\n[{model_id}] {spec['model']} @ {spec['endpoint']} ({spec['role']})")
    try:
        first, latency = chat(client, spec)
        second, _ = chat(client, spec)
    except (RuntimeError, httpx.HTTPError) as exc:
        print(f"  FAIL  {exc}")
        return False

    choice = first["choices"][0]
    content = (choice["message"].get("content") or "").strip()
    usage = first.get("usage", {})
    reasoning_tokens = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
    has_logprobs = bool((choice.get("logprobs") or {}).get("content"))
    same_answer = content == (second["choices"][0]["message"].get("content") or "").strip()
    try:
        json.loads(content)
        valid_json = True
    except json.JSONDecodeError:
        valid_json = False

    print(f"  provider     {first.get('provider')}")
    print(f"  latency      {latency:.2f} s")
    print(f"  tokens       in={usage.get('prompt_tokens')} out={usage.get('completion_tokens')} "
          f"reasoning={reasoning_tokens}")
    print(f"  cost         {usage.get('cost')} USD")
    print(f"  logprobs     {has_logprobs}")
    print(f"  valid JSON   {valid_json}")
    print(f"  same seed => same answer: {same_answer}")
    print(f"  answer       {content[:120]}")

    checks = {"valid JSON": valid_json}
    if spec.get("params", {}).get("logprobs"):
        checks["logprobs returned"] = has_logprobs
    if spec.get("params", {}).get("reasoning", {}).get("enabled") is False:
        checks["no reasoning tokens"] = reasoning_tokens == 0
    failed = [name for name, ok in checks.items() if not ok]
    if not same_answer:
        print("  WARN  seeded answers differ (noted, not a failure: provider may not be fully "
              "deterministic)")
    print(f"  {'FAIL  ' + ', '.join(failed) if failed else 'OK'}")
    return not failed


def ping_embedding(spec: dict) -> bool:
    print(f"\n[M5] {spec['model']} (local CPU)")
    from sentence_transformers import SentenceTransformer

    start = time.perf_counter()
    model = SentenceTransformer(spec["model"], device="cpu")
    sentences = ["Deliver to Mercy Hospital before 15:00.",
                 "Don't send anyone to the hospital until 3."]
    emb = model.encode(sentences, normalize_embeddings=True)
    cosine = float(emb[0] @ emb[1])
    print(f"  load+encode  {time.perf_counter() - start:.2f} s")
    print(f"  shape        {emb.shape}, cosine={cosine:.3f}")
    ok = emb.shape == (2, 384)
    print(f"  {'OK' if ok else 'FAIL  unexpected embedding shape'}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", nargs="*", help="model ids to ping, e.g. M1 M4")
    parser.add_argument("--skip-embedding", action="store_true")
    args = parser.parse_args()

    config = yaml.safe_load((ROOT / "configs" / "llm.yaml").read_text())
    load_env(ROOT / ".env")
    selected = {k: v for k, v in config["models"].items() if not args.only or k in args.only}

    results = {}
    api_models = {k: v for k, v in selected.items() if not v.get("local")}
    if api_models:
        key = os.environ.get(config["backend"]["api_key_env"])
        if not key:
            print(f"Missing {config['backend']['api_key_env']} in .env (see .env.example).")
            return 1
        headers = {"Authorization": f"Bearer {key}"}
        with httpx.Client(base_url=config["backend"]["base_url"], headers=headers,
                          timeout=120) as client:
            credits = client.get("/key")
            if credits.status_code == 200:
                info = credits.json().get("data", {})
                print(f"Key usage so far: {info.get('usage')} USD; limit: {info.get('limit')}")
            for model_id, spec in api_models.items():
                results[model_id] = ping_api_model(client, model_id, spec)

    if "M5" in selected and not args.skip_embedding:
        results["M5"] = ping_embedding(selected["M5"])

    print("\nSummary: " + ", ".join(f"{k}={'OK' if v else 'FAIL'}" for k, v in results.items()))
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
