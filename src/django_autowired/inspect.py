"""Introspection — report on what's bound to what.

The Spring Boot ``/actuator/beans`` analog. Produces a structured
``BindingReport`` for each registration, and ships renderers for table,
tree, JSON, and Mermaid output formats.

This module reads from the registry directly — a running container is not
required. Call :func:`scan` first (or :func:`django_autowired.container.initialize`)
to populate registrations.
"""

from __future__ import annotations

import inspect as _inspect
import json
from dataclasses import asdict, dataclass, field
from typing import Any

from django_autowired.registry import get_registry
from django_autowired.scanner import scan_packages
from django_autowired.scopes import Scope


@dataclass(frozen=True)
class BindingReport:
    """A single row in the binding report.

    Attributes:
        interface: The type used as a resolution key (``bind_to`` if set, else the class).
        implementation: The concrete class that will be constructed.
        scope: Lifecycle scope.
        kind: ``"concrete"`` if ``interface is implementation``, else ``"interface"``.
        source_module: Dotted module path where the implementation was declared.
        dependencies: Types consumed by the implementation's ``__init__``, in order.
    """

    interface: str
    implementation: str
    scope: str
    kind: str
    source_module: str
    dependencies: list[str] = field(default_factory=list)


def scan(*packages: str, exclude_patterns: set[str] | None = None) -> None:
    """Populate the registry by scanning packages, without building a container."""
    scan_packages(*packages, exclude_patterns=exclude_patterns)


def report() -> list[BindingReport]:
    """Build a report from the current registry.

    Does not require a running container — reads registrations directly.
    """
    rows: list[BindingReport] = []
    for reg in get_registry().all():
        iface = reg.target
        impl = reg.cls
        kind = "concrete" if iface is impl else "interface"
        rows.append(
            BindingReport(
                interface=_qualname(iface),
                implementation=_qualname(impl),
                scope=_scope_label(reg.scope),
                kind=kind,
                source_module=getattr(impl, "__module__", "<unknown>"),
                dependencies=_dependency_names(impl),
            )
        )
    rows.sort(key=lambda r: (r.kind, r.interface))
    return rows


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------


def render_table(rows: list[BindingReport]) -> str:
    """Render the report as a plain-text, aligned table."""
    if not rows:
        return "(no bindings registered)"

    headers = ("INTERFACE", "IMPLEMENTATION", "SCOPE", "KIND", "SOURCE")

    def _row(r: BindingReport) -> tuple[str, ...]:
        return (r.interface, r.implementation, r.scope, r.kind, r.source_module)

    data = [headers, *[_row(r) for r in rows]]
    widths = [max(len(cell) for cell in col) for col in zip(*data, strict=False)]

    def _fmt(cols: tuple[str, ...]) -> str:
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(cols))

    lines = [_fmt(headers), "  ".join("-" * w for w in widths)]
    lines.extend(_fmt(_row(r)) for r in rows)
    return "\n".join(lines)


def render_tree(rows: list[BindingReport]) -> str:
    """Render the report as an ASCII dependency tree.

    Each binding is a top-level node; its ``__init__`` dependencies are
    shown as children. Cycles are not drawn (dependencies of dependencies
    appear as leaf names only — follow up with another lookup).
    """
    if not rows:
        return "(no bindings registered)"

    lines = []
    for i, r in enumerate(rows):
        is_last = i == len(rows) - 1
        prefix = "└── " if is_last else "├── "
        header = f"{prefix}{r.interface}  →  {r.implementation}  [{r.scope}]"
        lines.append(header)

        dep_prefix = "    " if is_last else "│   "
        for j, dep in enumerate(r.dependencies):
            dep_is_last = j == len(r.dependencies) - 1
            dep_marker = "└── " if dep_is_last else "├── "
            lines.append(f"{dep_prefix}{dep_marker}{dep}")
    return "\n".join(lines)


def render_json(rows: list[BindingReport]) -> str:
    """Render the report as a JSON array."""
    return json.dumps([asdict(r) for r in rows], indent=2, sort_keys=True)


def render_mermaid(rows: list[BindingReport]) -> str:
    """Render the report as a Mermaid flowchart (graph TD).

    Dependency edges point from the consumer to the dependency type.
    Paste into a Mermaid renderer (GitHub, Mermaid Live) to visualize.
    """
    if not rows:
        return "graph TD\n    empty[No bindings registered]"

    known_ids: dict[str, str] = {}

    def _id(name: str) -> str:
        if name not in known_ids:
            safe = (
                name.replace(".", "_").replace("<", "_").replace(">", "_").replace("-", "_")
            )
            known_ids[name] = f"n{len(known_ids)}_{safe}"
        return known_ids[name]

    lines = ["graph TD"]
    for r in rows:
        iface_id = _id(r.interface)
        impl_id = _id(r.implementation)
        if r.kind == "interface":
            lines.append(f'    {iface_id}["{r.interface}"]')
            lines.append(f'    {impl_id}["{r.implementation}"]')
            lines.append(f"    {iface_id} -. implements .-> {impl_id}")
        else:
            lines.append(f'    {impl_id}["{r.implementation}"]')
        for dep in r.dependencies:
            dep_id = _id(dep)
            lines.append(f'    {dep_id}["{dep}"]')
            lines.append(f"    {impl_id} --> {dep_id}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _qualname(obj: Any) -> str:
    module: str = getattr(obj, "__module__", "") or ""
    qual: str = (
        getattr(obj, "__qualname__", None) or getattr(obj, "__name__", None) or repr(obj)
    )
    return f"{module}.{qual}" if module and module != "builtins" else qual


def _scope_label(scope: Scope) -> str:
    return scope.value if isinstance(scope, Scope) else str(scope)


def _dependency_names(cls: type) -> list[str]:
    """Return type names for each constructor parameter, skipping ``self``."""
    init = cls.__dict__.get("__init__")
    if init is None:
        return []
    try:
        sig = _inspect.signature(init)
    except (TypeError, ValueError):
        return []
    deps: list[str] = []
    for param in sig.parameters.values():
        if param.name == "self":
            continue
        if param.annotation is _inspect.Parameter.empty:
            deps.append(f"{param.name}: <unannotated>")
        else:
            deps.append(_qualname(param.annotation))
    return deps
