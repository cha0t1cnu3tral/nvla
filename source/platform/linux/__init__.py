# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from typing import Any

__all__ = ["create_platform_services"]


def __getattr__(name: str) -> Any:
	if name != "create_platform_services":
		raise AttributeError(name)
	from .factory import create_platform_services

	return create_platform_services
