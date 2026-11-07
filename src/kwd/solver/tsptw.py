"""Solve one in-service route snapshot under hard edit constraints (spec 07)."""

import hashlib
import json
from itertools import pairwise
from time import perf_counter
from typing import Literal

from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from pydantic import BaseModel, ConfigDict

from kwd.data.models import RouteSnapshot
from kwd.data.snapshot import travel
from kwd.dsl import EditSet, canonical
from kwd.solver.config import SolverConfig


class Plan(BaseModel):
    model_config = ConfigDict(frozen=True)

    sequence: list[str]
    arrival: dict[str, int]
    service_start: dict[str, int]
    end_time: int
    travel_min: float
    lateness_min: float
    overtime_min: float
    changed_positions: int
    solve_status: str
    solve_time_s: float

    def digest(self) -> str:
        payload = [
            self.sequence,
            [[stop, round(self.service_start[stop] / 60)] for stop in self.sequence],
            round(self.end_time / 60),
        ]
        return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


class Infeasible(BaseModel):
    model_config = ConfigDict(frozen=True)

    reason: Literal["precheck", "no_solution"]
    detail: str


def _index(p: RouteSnapshot) -> dict[str, int]:
    return {stop: i for i, stop in enumerate(p.node_ids)}


def _lower_bounds(p: RouteSnapshot, e: EditSet | None) -> dict[str, int]:
    bounds: dict[str, int] = {}
    if e is None:
        return bounds
    for op in canonical(e, p):
        if op[0] == "set_time_window":
            stop, lower = str(op[1]), int(op[2])
            bounds[stop] = max(bounds.get(stop, p.t_now), lower)
        elif op[0] == "avoid_zone_until":
            zone, lower = str(op[1]), int(op[2])
            for stop in p.remaining:
                if p.stops[stop].zone_id == zone:
                    bounds[stop] = max(bounds.get(stop, p.t_now), lower)
    return bounds


def schedule(
    p: RouteSnapshot, sequence: list[str], e: EditSet | None
) -> tuple[dict[str, int], dict[str, int], int]:
    """Walk `sequence` once, serving every stop at its earliest allowed time."""
    matrix, index = travel(p), _index(p)
    lower = _lower_bounds(p, e)
    arrival: dict[str, int] = {}
    service_start: dict[str, int] = {}
    previous, now = p.current_stop, p.t_now
    for stop in sequence:
        reached = now + int(matrix[index[previous], index[stop]])
        original_start = p.stops[stop].tw[0] if p.stops[stop].tw is not None else reached
        served = max(reached, original_start, lower.get(stop, reached))
        arrival[stop] = reached
        service_start[stop] = served
        now = served + p.stops[stop].service_s
        previous = stop
    end_time = now + int(matrix[index[previous], index[p.depot_id]])
    return arrival, service_start, end_time


def _plan(
    p: RouteSnapshot, sequence: list[str], e: EditSet | None, *, status: str, elapsed: float
) -> Plan:
    arrival, service_start, end_time = schedule(p, sequence, e)
    matrix, index = travel(p), _index(p)
    path = [p.current_stop, *sequence, p.depot_id]
    travel_s = sum(int(matrix[index[a], index[b]]) for a, b in pairwise(path))
    lateness_s = sum(
        max(0, service_start[stop] - p.stops[stop].tw[1])
        for stop in sequence
        if p.stops[stop].tw is not None
    )
    original = [stop for stop in p.remaining if stop in sequence]
    original_position = {stop: i for i, stop in enumerate(original)}
    changed = sum(original_position[stop] != i for i, stop in enumerate(sequence))
    return Plan(
        sequence=sequence,
        arrival=arrival,
        service_start=service_start,
        end_time=end_time,
        travel_min=travel_s / 60,
        lateness_min=lateness_s / 60,
        overtime_min=max(0, end_time - p.shift_end) / 60,
        changed_positions=changed,
        solve_status=status,
        solve_time_s=elapsed,
    )


def current_plan(p: RouteSnapshot) -> Plan:
    return _plan(p, list(p.remaining), None, status="current_plan", elapsed=0.0)


def _precheck(p: RouteSnapshot, e: EditSet | None) -> Infeasible | None:
    if e is None:
        return None
    ops = canonical(e, p)
    removed = {str(op[1]) for op in ops if op[0] == "remove_stop"}
    edges: dict[str, set[str]] = {}
    matrix, index = travel(p), _index(p)
    lower_bounds = {
        stop: p.stops[stop].tw[0]
        for stop in p.remaining
        if stop not in removed and p.stops[stop].tw is not None
    }
    for op in ops:
        if op[0] == "avoid_zone_until":
            zone, lower = str(op[1]), int(op[2])
            for stop in p.remaining:
                if stop not in removed and p.stops[stop].zone_id == zone:
                    lower_bounds[stop] = max(lower_bounds.get(stop, p.t_now), lower)

    for op in ops:
        name = op[0]
        if name == "set_time_window":
            stop, start, end = str(op[1]), int(op[2]), int(op[3])
            if stop in removed:
                continue
            effective_start = max(start, lower_bounds.get(stop, start))
            if effective_start > end:
                return Infeasible(reason="precheck", detail=f"empty window for {stop}")
            earliest = max(
                effective_start,
                p.t_now + int(matrix[index[p.current_stop], index[stop]]),
            )
            if earliest > end:
                return Infeasible(reason="precheck", detail=f"window unreachable for {stop}")
        elif name == "precedence":
            before, after = str(op[1]), str(op[2])
            edges.setdefault(before, set()).add(after)
        elif name == "driver_end_time":
            direct_return = p.t_now + int(matrix[index[p.current_stop], index[p.depot_id]])
            if int(op[1]) < direct_return:
                return Infeasible(
                    reason="precheck", detail="driver end time precedes direct return"
                )

    for before, afters in edges.items():
        if before in removed or any(after in removed for after in afters):
            return Infeasible(reason="precheck", detail="precedence references a removed stop")

    visiting: set[str] = set()
    visited: set[str] = set()

    def cyclic(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(cyclic(other) for other in edges.get(node, ())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    if any(cyclic(node) for node in edges):
        return Infeasible(reason="precheck", detail="precedence cycle")
    return None


def _first_solution(name: str) -> int:
    try:
        return int(getattr(routing_enums_pb2.FirstSolutionStrategy, name))
    except AttributeError:
        raise ValueError(f"unknown first-solution strategy: {name}") from None


def solve(p: RouteSnapshot, e: EditSet | None, cfg: SolverConfig) -> Plan | Infeasible:
    started = perf_counter()
    if error := _precheck(p, e):
        return error

    ops = canonical(e, p) if e is not None else ()
    removed = {str(op[1]) for op in ops if op[0] == "remove_stop"}
    active = [stop for stop in p.remaining if stop not in removed]
    nodes = list(dict.fromkeys([p.current_stop, *active, p.depot_id]))
    local = {stop: i for i, stop in enumerate(nodes)}
    manager = pywrapcp.RoutingIndexManager(
        len(nodes), 1, [local[p.current_stop]], [local[p.depot_id]]
    )
    routing = pywrapcp.RoutingModel(manager)
    matrix, snapshot_index = travel(p), _index(p)
    original_arcs = set(
        zip(
            [p.current_stop, *[s for s in p.remaining if s not in removed]],
            [*[s for s in p.remaining if s not in removed], p.depot_id],
        )
    )

    def transit(from_index: int, to_index: int) -> int:
        origin = nodes[manager.IndexToNode(from_index)]
        destination = nodes[manager.IndexToNode(to_index)]
        service_s = 0 if routing.IsStart(from_index) else p.stops[origin].service_s
        return int(matrix[snapshot_index[origin], snapshot_index[destination]]) + service_s

    transit_index = routing.RegisterTransitCallback(transit)

    deviation_s = round(cfg.dev_weight * 60)

    def arc_cost(from_index: int, to_index: int) -> int:
        origin = nodes[manager.IndexToNode(from_index)]
        destination = nodes[manager.IndexToNode(to_index)]
        travel_s = int(matrix[snapshot_index[origin], snapshot_index[destination]])
        return travel_s + (0 if (origin, destination) in original_arcs else deviation_s)

    routing.SetArcCostEvaluatorOfAllVehicles(routing.RegisterTransitCallback(arc_cost))

    horizon = max(p.shift_end, p.t_now) + 24 * 3600
    routing.AddDimension(transit_index, horizon, horizon, False, "Time")
    time = routing.GetDimensionOrDie("Time")
    time.CumulVar(routing.Start(0)).SetRange(p.t_now, p.t_now)
    for stop in active:
        node = manager.NodeToIndex(local[stop])
        if p.stops[stop].tw is not None:
            start, end = p.stops[stop].tw
            time.CumulVar(node).SetMin(start)
            time.SetCumulVarSoftUpperBound(node, end, round(cfg.late_penalty))
    time.SetCumulVarSoftUpperBound(routing.End(0), p.shift_end, round(cfg.shift_penalty))

    for op in ops:
        name = op[0]
        if name == "set_time_window":
            if str(op[1]) in removed:
                continue
            time.CumulVar(manager.NodeToIndex(local[str(op[1])])).SetRange(int(op[2]), int(op[3]))
        elif name == "precedence":
            before, after = str(op[1]), str(op[2])
            before_var = time.CumulVar(manager.NodeToIndex(local[before]))
            after_var = time.CumulVar(manager.NodeToIndex(local[after]))
            routing.solver().Add(before_var + p.stops[before].service_s <= after_var)
        elif name == "driver_end_time":
            time.CumulVar(routing.End(0)).SetMax(int(op[1]))
        elif name == "avoid_zone_until":
            zone, lower = str(op[1]), int(op[2])
            for stop in active:
                if p.stops[stop].zone_id == zone:
                    time.CumulVar(manager.NodeToIndex(local[stop])).SetMin(lower)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = _first_solution(cfg.first_solution)
    params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    params.solution_limit = cfg.solution_limit
    params.time_limit.FromMilliseconds(round(cfg.time_limit_s * 1000))

    assignment = None
    if cfg.warm_start:
        route = [local[stop] for stop in active]
        initial = routing.ReadAssignmentFromRoutes([route], True)
        if initial is not None:
            assignment = routing.SolveFromAssignmentWithParameters(initial, params)
    if assignment is None:
        assignment = routing.SolveWithParameters(params)
    if assignment is None:
        return Infeasible(reason="no_solution", detail="no plan found within search limits")

    sequence = []
    cursor = routing.NextVar(routing.Start(0))
    index_value = assignment.Value(cursor)
    while not routing.IsEnd(index_value):
        stop = nodes[manager.IndexToNode(index_value)]
        if stop != p.current_stop and stop != p.depot_id:
            sequence.append(stop)
        index_value = assignment.Value(routing.NextVar(index_value))
    elapsed = perf_counter() - started
    status = "time_limit" if elapsed >= cfg.time_limit_s * 0.99 else "solution_limit"
    return _plan(p, sequence, e, status=status, elapsed=elapsed)


def is_fixed_point(p: RouteSnapshot, cfg: SolverConfig) -> bool:
    result = solve(p, None, cfg)
    return isinstance(result, Plan) and result.digest() == current_plan(p).digest()
