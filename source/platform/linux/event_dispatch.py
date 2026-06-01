# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

import importlib
from typing import Any, Callable


class LinuxEventDispatcher:
	"""Dependency-light Linux event state until shared NVDA dispatch is portable."""

	def __init__(self) -> None:
		self._listeners: list[Callable[..., None]] = []
		self.lastQueuedFocusObject: Any | None = None

	def registerListener(self, listener: Callable[..., None]) -> None:
		if listener not in self._listeners:
			self._listeners.append(listener)

	def unregisterListener(self, listener: Callable[..., None]) -> None:
		try:
			self._listeners.remove(listener)
		except ValueError:
			return

	def setFocusObject(self, obj: Any) -> bool:
		importlib.import_module("globalVars").focusObject = obj
		return True

	def setMouseObject(self, obj: Any) -> bool:
		importlib.import_module("globalVars").mouseObject = obj
		return True

	def queueEvent(self, eventName: str, obj: Any, **kwargs: Any) -> None:
		if eventName == "gainFocus":
			self.lastQueuedFocusObject = obj
		for listener in tuple(self._listeners):
			listener(eventName, obj, **kwargs)
