#!/usr/bin/env python3
"""Thin shim for `obsidian_tooling.setup.main`. See that module for details."""

from __future__ import annotations

import sys

from obsidian_tooling.setup import main

if __name__ == "__main__":
    sys.exit(main())
