"""Smoke tests — the package imports and the CLI wiring is intact.

this_file: tests/test_smoke.py
"""

import vexy_vid


def test_package_has_version():
    assert isinstance(vexy_vid.__version__, str)
    assert vexy_vid.__version__


def test_cli_dispatch_table():
    from vexy_vid.crop import crop
    from vexy_vid.trim import trim

    # main() wires fire to these two callables; confirm they are importable.
    assert callable(crop)
    assert callable(trim)


def test_main_shows_help_without_args(monkeypatch, capsys):
    # fire prints the command group and returns when given no subcommand;
    # this exercises the cli.main() wiring without touching ffmpeg.
    import vexy_vid.cli as cli

    monkeypatch.setattr("sys.argv", ["vexy-vid"])
    cli.main()
    out = capsys.readouterr().out + capsys.readouterr().err
    assert "crop" in out or "trim" in out


def test_constants_are_sane():
    from vexy_vid import constants

    assert constants.BLACK_THRESHOLD > 0
    assert constants.MAX_WORKERS >= 1
    assert constants.HARDWARE_ENCODERS
    assert constants.SOFTWARE_ENCODERS == ["libx265", "libx264"]
