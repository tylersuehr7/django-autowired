"""Tests for the package scanner."""

from __future__ import annotations

import logging
import sys
import types

from django_autowired.registry import get_registry
from django_autowired.scanner import scan_packages


def _make_fake_package(
    name: str,
    submodules: dict[str, types.ModuleType | None] | None = None,
) -> types.ModuleType:
    """Create a fake package module with __path__ set."""
    mod = types.ModuleType(name)
    mod.__path__ = [f"/fake/{name.replace('.', '/')}"]
    mod.__package__ = name
    sys.modules[name] = mod
    if submodules:
        for sub_name, sub_mod in submodules.items():
            full = f"{name}.{sub_name}"
            if sub_mod is None:
                sub_mod = types.ModuleType(full)
            sub_mod.__name__ = full
            sys.modules[full] = sub_mod
    return mod


class TestScanPackages:
    def test_scans_package_and_triggers_injectable(self, tmp_path):
        """Create a real package on disk with an @injectable class."""
        pkg_dir = tmp_path / "fakepkg"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "services.py").write_text(
            "from django_autowired.registry import injectable\n"
            "from django_autowired.scopes import Scope\n"
            "@injectable()\n"
            "class RealService:\n"
            "    pass\n"
        )
        sys.path.insert(0, str(tmp_path))
        try:
            scan_packages("fakepkg")
            regs = get_registry().all()
            assert len(regs) == 1
            assert regs[0].cls.__name__ == "RealService"
        finally:
            sys.path.remove(str(tmp_path))
            for key in list(sys.modules):
                if key.startswith("fakepkg"):
                    del sys.modules[key]

    def test_skips_migrations(self, tmp_path):
        pkg_dir = tmp_path / "mypkg"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        mig_dir = pkg_dir / "migrations"
        mig_dir.mkdir()
        (mig_dir / "__init__.py").write_text("")
        (mig_dir / "0001.py").write_text(
            "from django_autowired.registry import injectable\n"
            "@injectable()\n"
            "class ShouldNotBeScanned:\n"
            "    pass\n"
        )
        sys.path.insert(0, str(tmp_path))
        try:
            scan_packages("mypkg")
            assert len(get_registry()) == 0
        finally:
            sys.path.remove(str(tmp_path))
            for key in list(sys.modules):
                if key.startswith("mypkg"):
                    del sys.modules[key]

    def test_skips_tests_directory(self, tmp_path):
        pkg_dir = tmp_path / "mypkg2"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        tests_dir = pkg_dir / "tests"
        tests_dir.mkdir()
        (tests_dir / "__init__.py").write_text("")
        (tests_dir / "test_thing.py").write_text(
            "from django_autowired.registry import injectable\n"
            "@injectable()\n"
            "class TestService:\n"
            "    pass\n"
        )
        sys.path.insert(0, str(tmp_path))
        try:
            scan_packages("mypkg2")
            assert len(get_registry()) == 0
        finally:
            sys.path.remove(str(tmp_path))
            for key in list(sys.modules):
                if key.startswith("mypkg2"):
                    del sys.modules[key]

    def test_custom_exclude_patterns(self, tmp_path):
        pkg_dir = tmp_path / "mypkg3"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "services.py").write_text(
            "from django_autowired.registry import injectable\n"
            "@injectable()\n"
            "class GoodService:\n"
            "    pass\n"
        )
        gen_dir = pkg_dir / "generated"
        gen_dir.mkdir()
        (gen_dir / "__init__.py").write_text("")
        (gen_dir / "stuff.py").write_text(
            "from django_autowired.registry import injectable\n"
            "@injectable()\n"
            "class BadService:\n"
            "    pass\n"
        )
        sys.path.insert(0, str(tmp_path))
        try:
            scan_packages("mypkg3", exclude_patterns={"generated"})
            regs = get_registry().all()
            assert len(regs) == 1
            assert regs[0].cls.__name__ == "GoodService"
        finally:
            sys.path.remove(str(tmp_path))
            for key in list(sys.modules):
                if key.startswith("mypkg3"):
                    del sys.modules[key]

    def test_import_error_in_submodule_is_skipped(self, tmp_path, caplog):
        pkg_dir = tmp_path / "mypkg4"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "good.py").write_text(
            "from django_autowired.registry import injectable\n"
            "@injectable()\n"
            "class GoodClass:\n"
            "    pass\n"
        )
        (pkg_dir / "bad.py").write_text("import nonexistent_module_xyz\n")
        sys.path.insert(0, str(tmp_path))
        try:
            with caplog.at_level(logging.WARNING, logger="django_autowired.scanner"):
                scan_packages("mypkg4")
            assert len(get_registry()) == 1
            assert "mypkg4.bad" in caplog.text
        finally:
            sys.path.remove(str(tmp_path))
            for key in list(sys.modules):
                if key.startswith("mypkg4"):
                    del sys.modules[key]

    def test_nonexistent_root_package_logs_error(self, caplog):
        with caplog.at_level(logging.ERROR, logger="django_autowired.scanner"):
            scan_packages("totally_nonexistent_package_xyz")
        assert "totally_nonexistent_package_xyz" in caplog.text
        assert len(get_registry()) == 0

    def test_scan_is_idempotent(self, tmp_path):
        pkg_dir = tmp_path / "mypkg5"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "svc.py").write_text(
            "from django_autowired.registry import injectable\n"
            "@injectable()\n"
            "class IdempotentService:\n"
            "    pass\n"
        )
        sys.path.insert(0, str(tmp_path))
        try:
            scan_packages("mypkg5")
            scan_packages("mypkg5")  # second scan
            assert len(get_registry()) == 1
        finally:
            sys.path.remove(str(tmp_path))
            for key in list(sys.modules):
                if key.startswith("mypkg5"):
                    del sys.modules[key]
