"""Tests for the inspect module (binding reports and renderers)."""

from __future__ import annotations

import dataclasses
import json
from abc import ABC, abstractmethod

import pytest

from django_autowired.inspect import (
    BindingReport,
    render_json,
    render_mermaid,
    render_table,
    render_tree,
    report,
)
from django_autowired.registry import Registration, get_registry
from django_autowired.scopes import Scope


class IGreeter(ABC):
    @abstractmethod
    def greet(self) -> str: ...


class PlainService:
    pass


class ServiceWithDep:
    def __init__(self, plain: PlainService) -> None:
        self.plain = plain


class HelloGreeter(IGreeter):
    def __init__(self, svc: ServiceWithDep) -> None:
        self.svc = svc

    def greet(self) -> str:
        return "hi"


def _register(*regs: Registration) -> None:
    for r in regs:
        get_registry().register(r)


class TestReport:
    def test_empty_registry(self):
        assert report() == []

    def test_concrete_registration(self):
        _register(Registration(cls=PlainService, scope=Scope.SINGLETON))
        rows = report()
        assert len(rows) == 1
        row = rows[0]
        assert row.kind == "concrete"
        assert row.scope == "singleton"
        assert row.interface == row.implementation
        assert row.implementation.endswith("PlainService")
        assert row.dependencies == []

    def test_interface_registration(self):
        _register(
            Registration(
                cls=HelloGreeter, scope=Scope.SINGLETON, bind_to=IGreeter
            )
        )
        rows = report()
        assert len(rows) == 1
        row = rows[0]
        assert row.kind == "interface"
        assert row.interface.endswith("IGreeter")
        assert row.implementation.endswith("HelloGreeter")

    def test_dependencies_reflected_from_init(self):
        _register(Registration(cls=ServiceWithDep, scope=Scope.SINGLETON))
        rows = report()
        assert len(rows) == 1
        assert any("PlainService" in dep for dep in rows[0].dependencies)

    def test_transient_scope_label(self):
        _register(Registration(cls=PlainService, scope=Scope.TRANSIENT))
        rows = report()
        assert rows[0].scope == "transient"

    def test_sort_concrete_before_interface(self):
        _register(
            Registration(cls=PlainService, scope=Scope.SINGLETON),
            Registration(
                cls=HelloGreeter, scope=Scope.SINGLETON, bind_to=IGreeter
            ),
            Registration(cls=ServiceWithDep, scope=Scope.SINGLETON),
        )
        rows = report()
        kinds = [r.kind for r in rows]
        # Concretes sort before interfaces alphabetically
        assert kinds.count("concrete") == 2
        assert kinds.count("interface") == 1
        assert kinds[-1] == "interface"


class TestRenderTable:
    def test_empty(self):
        assert render_table([]) == "(no bindings registered)"

    def test_has_headers(self):
        _register(Registration(cls=PlainService, scope=Scope.SINGLETON))
        out = render_table(report())
        assert "INTERFACE" in out
        assert "IMPLEMENTATION" in out
        assert "SCOPE" in out
        assert "KIND" in out
        assert "SOURCE" in out

    def test_contains_row_data(self):
        _register(Registration(cls=PlainService, scope=Scope.SINGLETON))
        out = render_table(report())
        assert "PlainService" in out
        assert "singleton" in out
        assert "concrete" in out


class TestRenderTree:
    def test_empty(self):
        assert render_tree([]) == "(no bindings registered)"

    def test_shows_dependency(self):
        _register(
            Registration(cls=PlainService, scope=Scope.SINGLETON),
            Registration(cls=ServiceWithDep, scope=Scope.SINGLETON),
        )
        out = render_tree(report())
        assert "ServiceWithDep" in out
        assert "PlainService" in out
        assert "→" in out

    def test_interface_arrow(self):
        _register(
            Registration(
                cls=HelloGreeter, scope=Scope.SINGLETON, bind_to=IGreeter
            )
        )
        out = render_tree(report())
        assert "IGreeter" in out
        assert "HelloGreeter" in out


class TestRenderJson:
    def test_empty(self):
        assert json.loads(render_json([])) == []

    def test_valid_json(self):
        _register(Registration(cls=PlainService, scope=Scope.SINGLETON))
        parsed = json.loads(render_json(report()))
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        row = parsed[0]
        assert row["kind"] == "concrete"
        assert row["scope"] == "singleton"
        assert "implementation" in row

    def test_includes_dependencies(self):
        _register(Registration(cls=ServiceWithDep, scope=Scope.SINGLETON))
        parsed = json.loads(render_json(report()))
        assert any("PlainService" in dep for dep in parsed[0]["dependencies"])


class TestRenderMermaid:
    def test_empty(self):
        out = render_mermaid([])
        assert out.startswith("graph TD")
        assert "empty" in out.lower()

    def test_graph_has_nodes_and_edges(self):
        _register(
            Registration(cls=PlainService, scope=Scope.SINGLETON),
            Registration(cls=ServiceWithDep, scope=Scope.SINGLETON),
        )
        out = render_mermaid(report())
        assert out.startswith("graph TD")
        assert "-->" in out

    def test_interface_uses_implements_edge(self):
        _register(
            Registration(
                cls=HelloGreeter, scope=Scope.SINGLETON, bind_to=IGreeter
            )
        )
        out = render_mermaid(report())
        assert "implements" in out


class TestBindingReportDataclass:
    def test_is_frozen(self):
        row = BindingReport(
            interface="I",
            implementation="Impl",
            scope="singleton",
            kind="concrete",
            source_module="x",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            row.scope = "transient"  # type: ignore[misc]
