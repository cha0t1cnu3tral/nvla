# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

import importlib
from typing import Any, Callable

from .mouse import LinuxMouseEvent


class LinuxMouseTracker:
	"""Translate observed pointer motion into Linux-native NVDA mouse objects."""

	def __init__(
		self,
		*,
		getObjectAtPoint: Callable[[int, int], Any | None],
		setMouseObject: Callable[[Any], Any] | None = None,
		queueEvent: Callable[..., Any] | None = None,
	) -> None:
		self._getObjectAtPoint = getObjectAtPoint
		self._setMouseObject = setMouseObject or _setMouseObject
		self._queueEvent = queueEvent or _queueEvent
		self._lastObject: Any | None = None
		self._lastPosition: tuple[int, int] | None = None

	def handleMouseEvent(self, event: LinuxMouseEvent) -> None:
		if event.kind != "move":
			return
		position = (event.x, event.y)
		if position == self._lastPosition:
			return
		self._lastPosition = position
		try:
			obj = self._getObjectAtPoint(*position)
		except Exception:
			return
		if obj is None:
			return
		if obj is not self._lastObject:
			if self._setMouseObject(obj) is False:
				return
			self._lastObject = obj
		self._queueEvent("mouseMove", obj, x=event.x, y=event.y)


def _setMouseObject(obj: Any) -> Any:
	return importlib.import_module("api").setMouseObject(obj)


def _queueEvent(eventName: str, obj: Any, **kwargs: Any) -> Any:
	return importlib.import_module("eventHandler").queueEvent(eventName, obj, **kwargs)
