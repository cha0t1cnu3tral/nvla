# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

"""NVDA platform abstraction package.

This package intentionally uses the module name ``platform`` to match the PAL plan.
To avoid breaking existing code that expects Python's stdlib ``platform`` module,
unknown attributes are delegated to the stdlib implementation.
"""

from __future__ import annotations

import importlib.util
import os
import sysconfig
from types import ModuleType


def _load_stdlib_platform() -> ModuleType:
	stdlib_path = os.path.join(sysconfig.get_path("stdlib"), "platform.py")
	spec = importlib.util.spec_from_file_location("_nvda_stdlib_platform", stdlib_path)
	if spec is None or spec.loader is None:
		raise RuntimeError("Unable to load stdlib platform module for compatibility delegation.")
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


_stdlib_platform = _load_stdlib_platform()


def __getattr__(name: str):
	return getattr(_stdlib_platform, name)


def __dir__():
	return sorted(set(globals().keys()) | set(dir(_stdlib_platform)))

