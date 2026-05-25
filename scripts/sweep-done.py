#!/usr/bin/env python3
"""Thin shim for `obsidian_tooling.sweep_done.main`. See that module for details."""

from __future__ import annotations

import sys

from obsidian_tooling.sweep_done import main

if __name__ == "__main__":
    sys.exit(main())
