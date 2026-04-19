"""Tests for scope behavior with the injector backend."""

from __future__ import annotations

import threading

import pytest

from django_autowired import container
from django_autowired.registry import injectable
from django_autowired.scopes import Scope

pytest.importorskip("injector")


class TestSingletonScope:
    def test_same_instance_on_multiple_gets(self):
        @injectable(scope=Scope.SINGLETON)
        class SingletonService:
            pass

        container.initialize(packages=[], backend="injector")
        a = container.get(SingletonService)
        b = container.get(SingletonService)
        assert a is b


class TestTransientScope:
    def test_different_instance_on_every_get(self):
        @injectable(scope=Scope.TRANSIENT)
        class TransientService:
            pass

        container.initialize(packages=[], backend="injector")
        a = container.get(TransientService)
        b = container.get(TransientService)
        assert a is not b


class TestThreadScope:
    def test_same_instance_within_thread_different_across(self):
        @injectable(scope=Scope.THREAD)
        class ThreadService:
            pass

        container.initialize(packages=[], backend="injector")

        results: dict[str, list[int]] = {"main": [], "other": []}

        main1 = container.get(ThreadService)
        main2 = container.get(ThreadService)
        results["main"] = [id(main1), id(main2)]

        def get_in_thread() -> None:
            t1 = container.get(ThreadService)
            t2 = container.get(ThreadService)
            results["other"] = [id(t1), id(t2)]

        t = threading.Thread(target=get_in_thread)
        t.start()
        t.join()

        # Same within each thread
        assert results["main"][0] == results["main"][1]
        assert results["other"][0] == results["other"][1]
        # Different across threads
        assert results["main"][0] != results["other"][0]
