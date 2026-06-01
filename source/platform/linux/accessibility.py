# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Callable

import controlTypes

from .atspi_backend import ATSPI2Backend
from .atspi_backend import TranslatedATSPISource
from .atspi_backend import TranslatedATSPIEvent
from .atspi_objects import LinuxATSPIObject
from .document_navigation import LinuxDocumentNavigationController, LinuxDocumentNavigator
from .event_dispatch import LinuxEventDispatcher
from .mouse import LinuxMouseEvent
from .mouse_tracking import LinuxMouseTracker


class LinuxATSPINVDAEventBridge:
	_MAX_CACHED_OBJECTS = 512

	def __init__(
		self,
		backend: ATSPI2Backend | None = None,
		onFocusObject: Callable[[LinuxATSPIObject], None] | None = None,
		dispatcher: LinuxEventDispatcher | None = None,
	) -> None:
		self._backend = backend
		self._onFocusObject = onFocusObject
		self._dispatcher = dispatcher or LinuxEventDispatcher()
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
				self._dispatcher.setFocusObject(obj)
				self._dispatcher.queueEvent("gainFocus", obj)
				if self._onFocusObject is not None:
					self._onFocusObject(obj)
			else:
				self._dispatcher.queueEvent("stateChange", obj)
			return
		if event.kind == "caret":
			self._dispatcher.queueEvent("caret", obj)
			return
		if event.kind == "stateChange":
			self._dispatcher.queueEvent("stateChange", obj)
			if controlTypes.State.DEFUNCT in obj.states:
				self._objectsByKey.pop(obj.sourceKey, None)
			return
		if event.kind != "propertyChange":
			return
		if event.propertyName == "name":
			self._dispatcher.queueEvent("nameChange", obj)
		elif event.propertyName == "description":
			self._dispatcher.queueEvent("descriptionChange", obj)
		elif event.propertyName == "value":
			self._dispatcher.queueEvent("valueChange", obj)
		else:
			self._dispatcher.queueEvent("stateChange", obj)


class LinuxAccessibilityAdapter:
	def __init__(self, announce: Callable[[str], None] | None = None) -> None:
		self._backend = ATSPI2Backend()
		self._dispatcher = LinuxEventDispatcher()
		self._documentNavigation = LinuxDocumentNavigationController(announce or self._announce)
		self._eventBridge = LinuxATSPINVDAEventBridge(
			self._backend,
			self._setDocumentNavigationFocus,
			self._dispatcher,
		)
		self._mouseTracker = LinuxMouseTracker(
			getObjectAtPoint=self.getNVDAObjectFromPoint,
			setMouseObject=self._dispatcher.setMouseObject,
			queueEvent=self._dispatcher.queueEvent,
		)
		self._initialized = False

	def initialize(self) -> None:
		self.initialize_iaccessible()

	def pump_all(self) -> None:
		self._backend.pump_all()

	def registerEventListener(self, listener: Callable[[TranslatedATSPIEvent], None]) -> None:
		self._backend.registerEventListener(listener)

	def unregisterEventListener(self, listener: Callable[[TranslatedATSPIEvent], None]) -> None:
		self._backend.unregisterEventListener(listener)

	def registerDispatchListener(self, listener: Callable[..., None]) -> None:
		self._dispatcher.registerListener(listener)

	def unregisterDispatchListener(self, listener: Callable[..., None]) -> None:
		self._dispatcher.unregisterListener(listener)

	def getNVDAObjectFromAccessible(self, accessible: Any) -> LinuxATSPIObject | None:
		return self._eventBridge.getOrCreateObjectForSource(accessible)

	def getNVDAObjectFromPoint(self, x: int, y: int) -> LinuxATSPIObject | None:
		return self.getNVDAObjectFromAccessible(self._backend.getAccessibleAtPoint(x, y))

	def handleMouseEvent(self, event: LinuxMouseEvent) -> None:
		self._mouseTracker.handleMouseEvent(event)

	def createDocumentNavigator(self, root: LinuxATSPIObject) -> LinuxDocumentNavigator:
		return LinuxDocumentNavigator(root)

	def handleKeyboardGesture(self, gesture: Any) -> bool:
		return self._documentNavigation.handleGesture(gesture)

	def _announce(self, text: str) -> None:
		import speech

		speech.speakText(text)

	def _setDocumentNavigationFocus(self, obj: LinuxATSPIObject) -> None:
		root: LinuxATSPIObject | None = obj
		while root is not None and root.role is not controlTypes.Role.DOCUMENT:
			root = root.parent
		self._documentNavigation.setRoot(root)

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
		try:
			self._backend.initialize()
		except Exception:
			self._backend.unregisterEventListener(self._eventBridge.handleEvent)
			self._eventBridge.clearCachedObjects()
			raise
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
