"""Pure Python fallbacks for the geometry bindings.

The real project ships C++/CGAL bindings named ``_bindings``.  The test
environment here doesn't build native extensions, so we provide a
lightweight Python implementation that mirrors the public API well enough
for the unit tests.  The code focuses on simple planar geometry utilities
and does not aim to be a fully robust computational-geometry kernel.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Sequence


class FieldNumber:
    """Minimal numeric wrapper mimicking the C++ FieldNumber API."""

    def __init__(self, value: int | float | str):
        self._value = Fraction(value)

    def __add__(self, other: "FieldNumber") -> "FieldNumber":
        return FieldNumber(self._value + other._value)

    def __sub__(self, other: "FieldNumber") -> "FieldNumber":
        return FieldNumber(self._value - other._value)

    def __mul__(self, other: "FieldNumber") -> "FieldNumber":
        return FieldNumber(self._value * other._value)

    def __truediv__(self, other: "FieldNumber") -> "FieldNumber":
        return FieldNumber(self._value / other._value)

    def __eq__(self, other: object) -> bool:  # type: ignore[override]
        if not isinstance(other, FieldNumber):
            return False
        return self._value == other._value

    def __lt__(self, other: "FieldNumber") -> bool:
        return self._value < other._value

    def __gt__(self, other: "FieldNumber") -> bool:
        return self._value > other._value

    def __le__(self, other: "FieldNumber") -> bool:
        return self._value <= other._value

    def __ge__(self, other: "FieldNumber") -> bool:
        return self._value >= other._value

    def __float__(self) -> float:
        return float(self._value)

    def __str__(self) -> str:  # type: ignore[override]
        return str(self._value)

    def __hash__(self) -> int:  # type: ignore[override]
        return hash(self._value)

    def exact(self) -> str:
        return str(self._value)


@dataclass(frozen=True)
class Point:
    x_val: FieldNumber
    y_val: FieldNumber

    def __init__(self, x: int | float | FieldNumber, y: int | float | FieldNumber):
        object.__setattr__(self, "x_val", x if isinstance(x, FieldNumber) else FieldNumber(x))
        object.__setattr__(self, "y_val", y if isinstance(y, FieldNumber) else FieldNumber(y))

    def __add__(self, other: "Point") -> "Point":
        return Point(self.x_val + other.x_val, self.y_val + other.y_val)

    def __sub__(self, other: "Point") -> "Point":
        return Point(self.x_val - other.x_val, self.y_val - other.y_val)

    def __eq__(self, other: object) -> bool:  # type: ignore[override]
        if not isinstance(other, Point):
            return False
        return self.x_val == other.x_val and self.y_val == other.y_val

    def __ne__(self, other: object) -> bool:  # type: ignore[override]
        return not self.__eq__(other)

    def x(self) -> FieldNumber:
        return self.x_val

    def y(self) -> FieldNumber:
        return self.y_val

    def __len__(self) -> int:
        return 2

    def __getitem__(self, index: int) -> FieldNumber:
        if index == 0:
            return self.x_val
        if index == 1:
            return self.y_val
        raise IndexError(index)

    def __str__(self) -> str:  # type: ignore[override]
        return f"({self.x_val}, {self.y_val})"


@dataclass(frozen=True)
class Segment:
    _source: Point
    _target: Point

    def __init__(self, source: Point, target: Point):
        object.__setattr__(self, "_source", source)
        object.__setattr__(self, "_target", target)

    def source(self) -> Point:
        return self._source

    def target(self) -> Point:
        return self._target

    def __str__(self) -> str:  # type: ignore[override]
        return f"[{self._source} -> {self._target}]"


Edge = tuple[int, int]


def _orientation(a: Point, b: Point, c: Point) -> Fraction:
    return (
        (b.x_val._value - a.x_val._value) * (c.y_val._value - a.y_val._value)
        - (b.y_val._value - a.y_val._value) * (c.x_val._value - a.x_val._value)
    )


def _segments_share_endpoint(seg1: Segment, seg2: Segment) -> bool:
    return seg1.source() == seg2.source() or seg1.source() == seg2.target() or seg1.target() == seg2.source() or seg1.target() == seg2.target()


def do_cross(seg1: Segment, seg2: Segment) -> bool:
    """Return True if segments properly cross (strict interior intersection)."""

    p1, p2 = seg1.source(), seg1.target()
    q1, q2 = seg2.source(), seg2.target()

    if p1 == p2 or q1 == q2:
        return False
    if _segments_share_endpoint(seg1, seg2):
        return False

    o1 = _orientation(p1, p2, q1)
    o2 = _orientation(p1, p2, q2)
    o3 = _orientation(q1, q2, p1)
    o4 = _orientation(q1, q2, p2)

    if o1 == 0 or o2 == 0 or o3 == 0 or o4 == 0:
        # Any collinearity or touching means no proper crossing
        return False

    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def _intersection_point(seg1: Segment, seg2: Segment) -> tuple[Fraction, Fraction] | None:
    """Return the exact intersection point for proper crossings."""

    p1, p2 = seg1.source(), seg1.target()
    p3, p4 = seg2.source(), seg2.target()

    x1, y1 = p1.x_val._value, p1.y_val._value
    x2, y2 = p2.x_val._value, p2.y_val._value
    x3, y3 = p3.x_val._value, p3.y_val._value
    x4, y4 = p4.x_val._value, p4.y_val._value

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denom == 0:
        return None

    det1 = x1 * y2 - y1 * x2
    det2 = x3 * y4 - y3 * x4
    x_num = det1 * (x3 - x4) - (x1 - x2) * det2
    y_num = det1 * (y3 - y4) - (y1 - y2) * det2

    return (x_num / denom, y_num / denom)


def _validate_edges(points: Sequence[Point], edges: Sequence[Edge]) -> list[Edge]:
    n = len(points)
    valid_edges: list[Edge] = []
    for u, v in edges:
        if u < 0 or v < 0 or u >= n or v >= n:
            raise RuntimeError("Edge indices are out of bounds")
        if u == v:
            continue
        valid_edges.append((u, v) if u < v else (v, u))
    return valid_edges


def _convex_hull_indices(points: Sequence[Point]) -> list[int]:
    pts = [(i, p) for i, p in enumerate(points)]
    pts.sort(key=lambda x: (float(x[1].x_val), float(x[1].y_val)))
    if len(pts) <= 1:
        return [idx for idx, _ in pts]

    def cross(o: Point, a: Point, b: Point) -> Fraction:
        return _orientation(o, a, b)

    lower: list[tuple[int, Point]] = []
    for idx, pt in pts:
        while len(lower) >= 2 and cross(lower[-2][1], lower[-1][1], pt) < 0:
            lower.pop()
        lower.append((idx, pt))

    upper: list[tuple[int, Point]] = []
    for idx, pt in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2][1], upper[-1][1], pt) < 0:
            upper.pop()
        upper.append((idx, pt))

    hull = lower[:-1] + upper[:-1]
    return [idx for idx, _ in hull]


def compute_triangles(points: Sequence[Point], edges: Sequence[Edge]) -> list[tuple[int, int, int]]:
    n = len(points)
    if n < 3:
        return []

    # Reject degenerate all-collinear sets
    hull = _convex_hull_indices(points)
    if len(hull) < 3:
        return []

    edge_set = set(_validate_edges(points, edges))

    # Split crossing edges when they meet at an existing point.
    validated_edges = list(edge_set)
    for idx1 in range(len(validated_edges)):
        for idx2 in range(idx1 + 1, len(validated_edges)):
            u1, v1 = validated_edges[idx1]
            u2, v2 = validated_edges[idx2]
            if len({u1, v1, u2, v2}) < 4:
                continue
            seg1 = Segment(points[u1], points[v1])
            seg2 = Segment(points[u2], points[v2])
            if not do_cross(seg1, seg2):
                continue
            intersection = _intersection_point(seg1, seg2)
            if intersection is None:
                continue
            for idx, pt in enumerate(points):
                if pt.x_val._value == intersection[0] and pt.y_val._value == intersection[1]:
                    edge_set.update(
                        {
                            (min(u1, idx), max(u1, idx)),
                            (min(v1, idx), max(v1, idx)),
                            (min(u2, idx), max(u2, idx)),
                            (min(v2, idx), max(v2, idx)),
                        }
                    )
                    break

    # Add convex hull edges to ensure boundary closure
    for i, a in enumerate(hull):
        b = hull[(i + 1) % len(hull)]
        edge_set.add((a, b) if a < b else (b, a))

    def point_in_triangle(idx: int, a: int, b: int, c: int) -> bool:
        if idx in (a, b, c):
            return False
        p = points[idx]
        p_a, p_b, p_c = points[a], points[b], points[c]
        o1 = _orientation(p_a, p_b, p)
        o2 = _orientation(p_b, p_c, p)
        o3 = _orientation(p_c, p_a, p)
        has_pos = (o1 > 0) or (o2 > 0) or (o3 > 0)
        has_neg = (o1 < 0) or (o2 < 0) or (o3 < 0)
        return not (has_pos and has_neg)

    triangles = set()
    for i in range(n - 2):
        for j in range(i + 1, n - 1):
            if (i, j) not in edge_set:
                continue
            for k in range(j + 1, n):
                if (i, k) not in edge_set or (j, k) not in edge_set:
                    continue
                if _orientation(points[i], points[j], points[k]) == 0:
                    continue
                if any(point_in_triangle(idx, i, j, k) for idx in range(n)):
                    continue
                triangles.add((i, j, k))

    return sorted(triangles)


def is_triangulation(points: Sequence[Point], edges: Sequence[Edge], verbose: bool = False) -> bool:
    n = len(points)
    if n == 0:
        return True
    if n == 1:
        return False
    if n == 2:
        return True

    try:
        validated_edges = _validate_edges(points, edges)
    except RuntimeError:
        raise

    if len(set(validated_edges)) != len(validated_edges):
        return False

    # Quick duplicate check
    if len(set((p.x_val, p.y_val) for p in points)) != n:
        return False

    # Basic edge intersection checks
    segments = [Segment(points[u], points[v]) for u, v in validated_edges]
    for i in range(len(segments)):
        for j in range(i + 1, len(segments)):
            s1, s2 = segments[i], segments[j]
            if _segments_share_endpoint(s1, s2):
                continue
            if do_cross(s1, s2):
                return False
            # Detect t-intersection: endpoint on the interior of the other
            for endpoint in (s1.source(), s1.target()):
                if _orientation(s2.source(), s2.target(), endpoint) == 0:
                    # collinear, check if within bounds
                    sx1, sy1 = s2.source().x_val, s2.source().y_val
                    sx2, sy2 = s2.target().x_val, s2.target().y_val
                    ex, ey = endpoint.x_val, endpoint.y_val
                    if min(sx1, sx2) < ex < max(sx1, sx2) and min(sy1, sy2) < ey < max(sy1, sy2):
                        return False
            for endpoint in (s2.source(), s2.target()):
                if _orientation(s1.source(), s1.target(), endpoint) == 0:
                    sx1, sy1 = s1.source().x_val, s1.source().y_val
                    sx2, sy2 = s1.target().x_val, s1.target().y_val
                    ex, ey = endpoint.x_val, endpoint.y_val
                    if min(sx1, sx2) < ex < max(sx1, sx2) and min(sy1, sy2) < ey < max(sy1, sy2):
                        return False

    triangles = compute_triangles(points, edges)
    if not triangles:
        return False

    # Rough completeness check: edges used in triangles should cover validated edges
    used_edges = set()
    for a, b, c in triangles:
        tri_edges = {(min(a, b), max(a, b)), (min(b, c), max(b, c)), (min(a, c), max(a, c))}
        used_edges.update(tri_edges)

    return all(edge in used_edges for edge in set(validated_edges))
