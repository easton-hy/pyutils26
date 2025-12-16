try:
    from . import _bindings as _bindings_impl
except ModuleNotFoundError:
    # If the compiled extension is unavailable or the module was not packaged,
    # fall back to the pure-Python implementation that mirrors the same API.
    from . import _bindings_pure as _bindings_impl

(
    is_triangulation,
    compute_triangles,
    Point,
    do_cross,
    Segment,
    FieldNumber,
) = (
    _bindings_impl.is_triangulation,
    _bindings_impl.compute_triangles,
    _bindings_impl.Point,
    _bindings_impl.do_cross,
    _bindings_impl.Segment,
    _bindings_impl.FieldNumber,
)  # pyright: ignore[reportMissingModuleSource]
from .flip_partner_map import FlipPartnerMap

from .flippable_triangulation import FlippableTriangulation
from .flip_partner_map import expand_edges_by_convex_hull_edges
from .draw import draw_flips, draw_edges
from .typing import Edge, ParallelFlipSequence, ParallelFlips, Triangle

__all__ = [
    "is_triangulation",
    "Point",
    "FieldNumber",
    "compute_triangles",
    "do_cross",
    "Segment",
    "FlipPartnerMap",
    "FlippableTriangulation",
    "draw_flips",
    "draw_edges",
    "expand_edges_by_convex_hull_edges",
    "Edge",
    "ParallelFlipSequence",
    "ParallelFlips",
    "Triangle",
]
