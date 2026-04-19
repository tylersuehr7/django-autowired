"""Tests for the CLI entry point."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from django_autowired.cli import main


class TestInspectCommand:
    def test_no_args_exits_nonzero(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main([])
        assert exc.value.code != 0

    def test_unknown_format_rejected(self, capsys):
        with pytest.raises(SystemExit):
            main(["inspect", "django_autowired", "--format", "bogus"])

    def test_inspect_empty_table(self, capsys):
        rc = main(["inspect", "django_autowired", "--format", "table"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "no bindings registered" in out

    def test_inspect_empty_json(self, capsys):
        rc = main(["inspect", "django_autowired", "--format", "json"])
        assert rc == 0
        out = capsys.readouterr().out
        assert json.loads(out) == []

    def test_inspect_real_package(self, capsys, tmp_path, monkeypatch):
        pkg = tmp_path / "mypkg_cli"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "svc.py").write_text(
            "from django_autowired.registry import injectable\n"
            "@injectable()\n"
            "class CliSvc:\n"
            "    pass\n"
        )
        monkeypatch.syspath_prepend(str(tmp_path))
        try:
            rc = main(["inspect", "mypkg_cli", "--format", "json"])
            assert rc == 0
            out = capsys.readouterr().out
            parsed = json.loads(out)
            assert len(parsed) == 1
            assert parsed[0]["implementation"].endswith("CliSvc")
        finally:
            # Clean up imports so other tests don't see this package
            for mod_name in list(sys.modules):
                if mod_name.startswith("mypkg_cli"):
                    del sys.modules[mod_name]

    def test_exclude_flag(self, capsys, tmp_path, monkeypatch):
        pkg = tmp_path / "mypkg_cli2"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "keep.py").write_text(
            "from django_autowired.registry import injectable\n"
            "@injectable()\n"
            "class Keep:\n"
            "    pass\n"
        )
        skip_dir = pkg / "drop"
        skip_dir.mkdir()
        (skip_dir / "__init__.py").write_text("")
        (skip_dir / "skipped.py").write_text(
            "from django_autowired.registry import injectable\n"
            "@injectable()\n"
            "class Dropped:\n"
            "    pass\n"
        )
        monkeypatch.syspath_prepend(str(tmp_path))
        try:
            rc = main(
                ["inspect", "mypkg_cli2", "--format", "json", "--exclude", "drop"]
            )
            assert rc == 0
            parsed = json.loads(capsys.readouterr().out)
            names = [p["implementation"] for p in parsed]
            assert any("Keep" in n for n in names)
            assert not any("Dropped" in n for n in names)
        finally:
            for mod_name in list(sys.modules):
                if mod_name.startswith("mypkg_cli2"):
                    del sys.modules[mod_name]


class TestEntryPoint:
    def test_python_m_django_autowired_runs(self):
        """Smoke test: `python -m django_autowired inspect <pkg>` exits cleanly."""
        result = subprocess.run(
            [sys.executable, "-m", "django_autowired", "inspect", "django_autowired"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
