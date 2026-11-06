# 06 · Edit DSL

> Status: Draft v0.5 · Updated 2026-11-07 · v0.5: `service_time` dropped, 6 ops; the DSL covers constraints on the plan only (§3, decided 07/11) · v0.4: parsing keeps ops as written; edge cases of `schema` / `invalid_json` / `unknown_stop` / `done_stop`; `tol_min` on times (§5) · v0.3: `bad_interval` covers every past time, compared by the minute (§4, decided 07/11) · v0.2: `op_type` defined in §5.1 · Final op list frozen at end of week 1 (6–8 ops).

## 1. Purpose

A small, typed JSON language for route edits. The LLM outputs **only** this (no free code). Smaller error surface, and outputs can be validated, compared and scored.

## 2. Envelope

A request maps to an `EditSet` — one or more ops (compound requests → several ops).

```json
{"edits": [ {"op": "set_time_window", "stop": "Mercy Hospital", "start": "15:00", "end": null} ],
 "confidence": 80}
```

- `stop` fields use the **display name** from the snapshot (spec 05 §4.8).
- Times are local `HH:MM` strings in the JSON; parsed to seconds since departure internally.
- `confidence` (0–100) is the verbalized confidence; optional, ignored by the solver.

## 3. Operations (6 ops since 2026-11-07; the pilot may drop more)

| `op` | Arguments | Meaning (hard constraint on `P̂`) |
|---|---|---|
| `set_time_window` | `stop`, `start: HH:MM \| null`, `end: HH:MM \| null` | Arrive at `stop` within `[start, end]`. `null` = open side (`start` → `t_now`, `end` → `shift_end`). |
| `remove_stop` | `stop` | `stop` is not visited. |
| `precedence` | `before`, `after` | `before` is visited before `after`. |
| `driver_end_time` | `time` | Vehicle returns to depot by `time`. |
| `avoid_zone_until` | `zone`, `time` | No arrival at any stop in `zone` before `time`. |
| `deadline` | `stop`, `time` | Arrive at `stop` no later than `time`. |

Notes:

- `deadline(s, t)` overlaps with `set_time_window(s, null, t)`. Keep both in the pilot (dispatchers phrase them differently); **canonicalization maps `deadline` → `set_time_window`** so they compare equal.
- Out of scope: inserting new stops, moving stops to another vehicle, and edits that change problem data (travel times, service times). Every op is a **constraint on the plan**, so harm rule R1 checks it directly (spec 09 §2). `service_time` was dropped on 2026-11-07 for this reason: it changes data, and judging `P̂` would need gold service durations with the LLM's waits.
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

**Past times (decided 2026-11-07).** `bad_interval` applies to **every** time in an edit: both window bounds, `deadline`, `driver_end_time` and `avoid_zone_until`. Times are compared by the minute: a time is past when its whole local minute is over (`clock_to_s(hhmm) + 60 ≤ t_now`). The current minute stays valid, because `t_now` usually falls inside a minute and the snapshot shows it as the current time. The past time is never repaired (e.g. `"03:00"` is not read as 15:00). Why: a past time is caught by any basic validator, so counting it as a harmful execution would inflate `μ` and flatter the solver signals; rejecting it keeps harm focused on errors that pass every syntactic and feasibility check. The rejected edit stays in every denominator (`π`). In the paper, the parser's checks are one clause in §IV; `bad_interval` gets no separate table entry (it is part of the parse-error rate in T1).

**Edge cases (decided 2026-11-07; never repair the output):**
- The parsed `EditSet` keeps ops as written: `deadline` stays `deadline`, `null` bounds stay open. Only `canonical` (§5) closes bounds and rewrites `deadline`.
- `schema`: window with both bounds `null`; `precedence` of a stop with itself; `confidence` not a whole number in 0–100; a dropped op such as `service_time`.
- `invalid_json`: output wrapped in a code fence. `unknown_stop`: the depot name. `done_stop`: the stop where the vehicle stands (`current_stop`).

## 5. Canonical form and equivalence (`kwd.dsl.canonical`)

Needed for self-consistency (spec 11) and string-level error rate (spec 13 E1).

1. Resolve names → `stop_id`; times → seconds since departure; `null` bounds → explicit (`t_now`, `shift_end`).
2. Rewrite `deadline` → `set_time_window`.
3. Merge multiple windows on the same stop by intersection.
4. Sort ops by `(op, args)`; drop exact duplicates.
5. Two EditSets are **equivalent** iff canonical forms are equal, with time tolerance `±tol_min` (default 0; configurable).

### 5.1 Operation type `op_type(e)`

One shared function gives both the group `ĉ = op_type(ê)` used by per-group CRC (spec 12 §2.2) and the gold type `c = op_type(e*)` (spec 08, error analysis). It is computed on the **canonical** form (steps 1–4 above):

- exactly one op → that op's name (so `deadline` → `set_time_window`);
- two or more ops, even of the same type (e.g. two `set_time_window` on different stops) → `compound`.

Computing it on raw op names would split one meaning across two groups and shrink them (spec 12 §2.2, sample floor).

## 6. Data model

```python
class Edit(BaseModel):          # discriminated union on `op`
    op: Literal["set_time_window","remove_stop","precedence","driver_end_time",
                "avoid_zone_until","deadline"]
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
- [ ] `op_type` returns `set_time_window` for a single `deadline`, and `compound` for two ops of the same type.
- [ ] The hospital wrong edit `[00:00, 15:00]` is **not** equivalent to gold `[15:00, null]`.
