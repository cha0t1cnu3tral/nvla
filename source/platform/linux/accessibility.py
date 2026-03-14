# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from typing import Callable

import api
import eventHandler

from .atspi_backend import ATSPI2Backend
from .atspi_backend import TranslatedATSPIEvent
from .atspi_objects import LinuxATSPIObject


class LinuxATSPINVDAEventBridge:
	def __init__(self) -> None:
		self._objectsByKey: dict[str, LinuxATSPIObject] = {}

	def _getCacheKey(self, event: TranslatedATSPIEvent) -> str | None:
		if event.sourceKey is not None:
			return event.sourceKey
		if event.source is not None:
			return f"atspi:{id(event.source)}"
		return None

	def getOrCreateObjectForEvent(self, event: TranslatedATSPIEvent) -> LinuxATSPIObject | None:
		cacheKey = self._getCacheKey(event)
		if cacheKey is None:
			return None
		obj = self._objectsByKey.get(cacheKey)
		if obj is None:
			obj = LinuxATSPIObject(
				chooseBestAPI=False,
				sourceKey=cacheKey,
				accessible=event.source,
				name=event.sourceName,
				description=event.sourceDescription,
				role=event.role,
				states=event.states,
			)
			self._objectsByKey[cacheKey] = obj
		else:
			obj.updateFromTranslatedEvent(event)
		return obj

	def handleEvent(self, event: TranslatedATSPIEvent) -> None:
		obj = self.getOrCreateObjectForEvent(event)
		if obj is None:
			return
		if event.kind == "focus":
			if event.isFocused:
				api.setFocusObject(obj)
				eventHandler.queueEvent("gainFocus", obj)
			else:
				eventHandler.queueEvent("stateChange", obj)
			return
		if event.kind == "caret":
			eventHandler.queueEvent("caret", obj)
			return
		if event.kind != "propertyChange":
			return
		if event.propertyName == "name":
			eventHandler.queueEvent("nameChange", obj)
		elif event.propertyName == "description":
			eventHandler.queueEvent("descriptionChange", obj)
		elif event.propertyName == "value":
			eventHandler.queueEvent("valueChange", obj)


class LinuxAccessibilityAdapter:
	def __init__(self) -> None:
		self._backend = ATSPI2Backend()
		self._eventBridge = LinuxATSPINVDAEventBridge()
		self._initialized = False

	def initialize(self) -> None:
		self.initialize_iaccessible()

	def pump_all(self) -> None:
		self._backend.pump_all()

	def registerEventListener(self, listener: Callable[[TranslatedATSPIEvent], None]) -> None:
		self._backend.registerEventListener(listener)

	def unregisterEventListener(self, listener: Callable[[TranslatedATSPIEvent], None]) -> None:
		self._backend.unregisterEventListener(listener)

	def terminate(self) -> None:
		self.terminate_iaccessible()

	def initialize_uia(self) -> None:
		# Linux accessibility does not use UIA.
		return

	def terminate_uia(self) -> None:
		return

	def initialize_iaccessible(self) -> None:
		if self._initialized:
			return
		self._backend.registerEventListener(self._eventBridge.handleEvent)
		self._backend.initialize()
		self._initialized = True

	def terminate_iaccessible(self) -> None:
		if not self._initialized:
			return
		self._backend.unregisterEventListener(self._eventBridge.handleEvent)
		self._backend.terminate()
		self._initialized = False

	def initialize_legacy_console_support(self) -> None:
		# Linux accessibility does not use the Windows console backend.
		return

	def terminate_legacy_console_support(self) -> None:
		return
