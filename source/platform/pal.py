# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

import sys

from platform.common.interfaces import PlatformServices


def _create_services() -> PlatformServices:
	if sys.platform.startswith("win"):
		from platform.windows import create_platform_services

		return create_platform_services()
	if sys.platform.startswith("linux"):
		from platform.linux import create_platform_services

		return create_platform_services()
	raise RuntimeError(f"Unsupported platform for NVDA PAL bootstrap: {sys.platform}")


_services = _create_services()


def services() -> PlatformServices:
	return _services

