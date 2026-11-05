# 06 · Edit DSL

> Status: Draft v0.1 · Updated 2026-11-05 · Final op list frozen at end of week 1 (6–8 ops).

## 1. Purpose

A small, typed JSON language for route edits. The LLM outputs **only** this (no free code). Smaller error surface, and outputs can be validated, compared and scored.

## 2. Envelope

A request maps to an `EditSet` — one or more ops (compound requests → several ops).

```json
{"edits": [ {"op": "set_time_window", "stop": "Mercy Hospital", "start": "15:00", "end": null} ],
 "confidence": 80}
```

- `stop` fields use the **display name** from the snapshot (spec 05 §4.8).
- Times are local `HH:MM` strings in the JSON; parsed to minutes since departure internally.
- `confidence` (0–100) is the verbalized confidence; optional, ignored by the solver.

## 3. Operations (v0.1 candidate list)

| `op` | Arguments | Meaning (hard constraint on `P̂`) |
|---|---|---|
| `set_time_window` | `stop`, `start: HH:MM \| null`, `end: HH:MM \| null` | Arrive at `stop` within `[start, end]`. `null` = open side (`start` → `t_now`, `end` → `shift_end`). |
| `remove_stop` | `stop` | `stop` is not visited. |
| `precedence` | `before`, `after` | `before` is visited before `after`. |
| `driver_end_time` | `time` | Vehicle returns to depot by `time`. |
| `avoid_zone_until` | `zone`, `time` | No arrival at any stop in `zone` before `time`. |
| `service_time` | `stop`, `minutes` | Service duration at `stop` becomes `minutes`. |
| `deadline` | `stop`, `time` | Arrive at `stop` no later than `time`. |

Notes:

- `deadline(s, t)` overlaps with `set_time_window(s, null, t)`. Keep both in the pilot (dispatchers phrase them differently); **canonicalization maps `deadline` → `set_time_window`** so they compare equal.
- Out of scope: inserting new stops, moving stops to another vehicle, changing travel times.
- Week-1 decision: drop any op with near-zero LLM errors in the pilot, or one that is hard to generate realistically.

## 4. Validation (`kwd.dsl.parse`)

Returns `EditSet` or a `ParseError` with a reason code:

| Code | Example |
|---|---|
| `invalid_json` | not parseable |
| `schema` | unknown op, missing/extra field, bad `HH:MM` |
| `unknown_stop` / `unknown_zone` | name not in snapshot remaining stops |
| `done_stop` | refers to an already-delivered stop |
| `bad_interval` | `start > end`, time before `t_now` |

A parse error ⇒ the system **defers automatically** (no execution). Record it; it counts against coverage.

## 5. Canonical form and equivalence (`kwd.dsl.canonical`)

Needed for self-consistency (spec 11) and string-level error rate (spec 13 E1).

1. Resolve names → `stop_id`; times → minutes; `null` bounds → explicit (`t_now`, `shift_end`).
2. Rewrite `deadline` → `set_time_window`.
3. Merge multiple windows on the same stop by intersection.
4. Sort ops by `(op, args)`; drop exact duplicates.
5. Two EditSets are **equivalent** iff canonical forms are equal, with time tolerance `±tol_min` (default 0; configurable).

## 6. Data model

```python
class Edit(BaseModel):          # discriminated union on `op`
    op: Literal["set_time_window","remove_stop","precedence","driver_end_time",
                "avoid_zone_until","service_time","deadline"]
    ...                          # op-specific fields

class EditSet(BaseModel):
    edits: list[Edit]            # 1..4 ops
    confidence: int | None = None
```

Expose `EditSet.json_schema()` — it is pasted into the LLM prompt (spec 10).

## 7. Acceptance criteria

- [ ] Round-trip: `parse(render(e)) == e` for 1,000 random valid EditSets.
- [ ] Each reason code in §4 has a unit test.
- [ ] `canonical` makes `deadline(X, 15:00)` ≡ `set_time_window(X, null, 15:00)`.
- [ ] The hospital wrong edit `[00:00, 15:00]` is **not** equivalent to gold `[15:00, null]`.
