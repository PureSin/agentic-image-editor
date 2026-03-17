"""Shared helper for running ImageMagick CLI commands."""

import subprocess


def run(args: list[str]) -> tuple[bool, str]:
    """Run `magick <args>`. Returns (success, message)."""
    cmd = ["magick"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return True, result.stdout.strip()
    return False, result.stderr.strip() or f"magick exited with code {result.returncode}"
