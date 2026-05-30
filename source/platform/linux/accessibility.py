# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Callable

import api
import controlTypes
import eventHandler

from .atspi_backend import ATSPI2Backend
from .atspi_backend import TranslatedATSPISource
from .atspi_backend import TranslatedATSPIEvent
from .atspi_objects import LinuxATSPIObject


class LinuxATSPINVDAEventBridge:
	_MAX_CACHED_OBJECTS = 512

	def __init__(self, backend: ATSPI2Backend | None = None) -> None:
		self._backend = backend
		self._objectsByKey: OrderedDict[str, LinuxATSPIObject] = OrderedDict()

	def _getCacheKeyFromTranslatedSource(self, source: TranslatedATSPISource) -> str:
		return source.sourceKey or f"atspi:{id(source.source)}"

	def getOrCreateObjectForSource(
		self,
		source: Any,
		translatedSource: TranslatedATSPISource | None = None,
		*,
		updateStates: bool = True,
	) -> LinuxATSPIObject | None:
		if translatedSource is None:
			backend = self._backend
			if backend is None:
				return None
			translatedSource = backend.translateSource(source)
		if translatedSource is None:
			return None
		cacheKey = self._getCacheKeyFromTranslatedSource(translatedSource)
		obj = self._objectsByKey.get(cacheKey)
		if obj is None:
			obj = LinuxATSPIObject(
				chooseBestAPI=False,
				sourceKey=cacheKey,
				accessible=translatedSource.source,
				processID=translatedSource.sourceProcessID,
				name=translatedSource.sourceName,
				description=translatedSource.sourceDescription,
				role=translatedSource.role,
				states=translatedSource.states,
				objectFactory=self.getOrCreateObjectForSource,
			)
			self._objectsByKey[cacheKey] = obj
			self._evictCachedObjectsIfNeeded()
		else:
			self._objectsByKey.move_to_end(cacheKey)
		obj.updateFromTranslatedSource(translatedSource, updateStates=updateStates)
		return obj

	def getOrCreateObjectForEvent(self, event: TranslatedATSPIEvent) -> LinuxATSPIObject | None:
		obj = self.getOrCreateObjectForSource(
			event.source,
			TranslatedATSPISource(
				source=event.source,
				sourceKey=event.sourceKey,
				sourceProcessID=event.sourceProcessID,
				sourceName=event.sourceName,
				sourceDescription=event.sourceDescription,
				role=event.role,
				states=event.states,
			),
			updateStates=event.kind != "stateChange" or event.mappedState is None,
		)
		if obj is None:
			return None
		obj.updateFromTranslatedEvent(event)
		return obj

	def clearCachedObjects(self) -> None:
		self._objectsByKey.clear()

	def _evictCachedObjectsIfNeeded(self) -> None:
		while len(self._objectsByKey) > self._MAX_CACHED_OBJECTS:
			self._objectsByKey.popitem(last=False)

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
		if event.kind == "stateChange":
			eventHandler.queueEvent("stateChange", obj)
			if controlTypes.State.DEFUNCT in obj.states:
				self._objectsByKey.pop(obj.sourceKey, None)
			return
		if event.kind != "propertyChange":
			return
		if event.propertyName == "name":
			eventHandler.queueEvent("nameChange", obj)
		elif event.propertyName == "description":
			eventHandler.queueEvent("descriptionChange", obj)
		elif event.propertyName == "value":
			eventHandler.queueEvent("valueChange", obj)
		else:
			eventHandler.queueEvent("stateChange", obj)


class LinuxAccessibilityAdapter:
	def __init__(self) -> None:
		self._backend = ATSPI2Backend()
		self._eventBridge = LinuxATSPINVDAEventBridge(self._backend)
		self._initialized = False

	def initialize(self) -> None:
		self.initialize_iaccessible()

	def pump_all(self) -> None:
		self._backend.pump_all()

	def registerEventListener(self, listener: Callable[[TranslatedATSPIEvent], None]) -> None:
		self._backend.registerEventListener(listener)

	def unregisterEventListener(self, listener: Callable[[TranslatedATSPIEvent], None]) -> None:
		self._backend.unregisterEventListener(listener)

	def getNVDAObjectFromAccessible(self, accessible: Any) -> LinuxATSPIObject | None:
		return self._eventBridge.getOrCreateObjectForSource(accessible)

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
		self._eventBridge.clearCachedObjects()
		self._initialized = False

	def initialize_legacy_console_support(self) -> None:
		# Linux accessibility does not use the Windows console backend.
		return

	def terminate_legacy_console_support(self) -> None:
		return
