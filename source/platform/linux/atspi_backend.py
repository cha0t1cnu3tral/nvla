# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, replace
from typing import Any, Callable

import controlTypes
from logHandler import log
from platform.common.errors import NotSupportedYetError

from . import atspi_mappings

_AT_SPI_EVENT_NAMES = (
	"object:state-changed:focused",
	"accessible:property-change",
	"object:text-caret-moved",
)
_MAX_QUEUED_TRANSLATED_EVENTS = 256


@dataclass(frozen=True, slots=True)
class TranslatedATSPIEvent:
	"""Normalized AT-SPI event payload shared with higher Linux accessibility layers."""

	kind: str
	rawType: str
	source: Any
	sourceKey: str | None
	sourceName: str | None
	sourceDescription: str | None
	role: controlTypes.Role
	states: frozenset[controlTypes.State]
	isFocused: bool | None = None
	propertyName: str | None = None
	propertyValue: Any = None
	caretOffset: int | None = None


def _coerce_bool(value: Any) -> bool:
	if isinstance(value, bool):
		return value
	if isinstance(value, (int, float)):
		return value != 0
	if isinstance(value, str):
		return value.strip().lower() not in ("", "0", "false", "no")
	return bool(value)


def _iter_state_values(stateObj: Any) -> tuple[int, ...]:
	if stateObj is None:
		return ()
	try:
		if hasattr(stateObj, "getStates"):
			return tuple(int(s) for s in stateObj.getStates())
		return tuple(int(s) for s in stateObj)
	except Exception:
		return ()


def _get_source_role_value(source: Any) -> int | None:
	if source is None:
		return None
	try:
		if hasattr(source, "getRole"):
			return int(source.getRole())
	except Exception:
		return None
	roleValue = getattr(source, "role", None)
	if roleValue is None:
		return None
	try:
		return int(roleValue)
	except Exception:
		return None


def _get_source_state_values(source: Any) -> tuple[int, ...]:
	if source is None:
		return ()
	try:
		if hasattr(source, "getState"):
			return _iter_state_values(source.getState())
	except Exception:
		return ()
	return _iter_state_values(getattr(source, "state", None))


def _make_source_key(source: Any) -> str | None:
	if source is None:
		return None
	for attrName in ("path", "accessibleId", "id"):
		value = getattr(source, attrName, None)
		if value is None:
			continue
		if isinstance(value, (tuple, list)):
			return ":".join(str(part) for part in value)
		return str(value)
	name = getattr(source, "name", None)
	roleValue = _get_source_role_value(source)
	if name is not None or roleValue is not None:
		return f"{roleValue}:{name}"
	return None


def _parse_property_name(rawType: str) -> str | None:
	prefix = "accessible:property-change"
	if not rawType.startswith(prefix):
		return None
	if rawType == prefix:
		return None
	return rawType[len(prefix) + 1 :] if rawType.startswith(prefix + ":") else None


def translate_atspi_event(
	event: Any,
	roleMap: dict[int, controlTypes.Role],
	stateMap: dict[int, controlTypes.State],
	invertedStateValues: set[int],
) -> TranslatedATSPIEvent | None:
	rawType = str(getattr(event, "type", "") or "")
	if not rawType:
		return None
	if rawType == "object:state-changed:focused":
		kind = "focus"
	elif rawType.startswith("accessible:property-change"):
		kind = "propertyChange"
	elif rawType == "object:text-caret-moved":
		kind = "caret"
	else:
		return None

	source = getattr(event, "source", None)
	roleValue = _get_source_role_value(source)
	role = (
		atspi_mappings.map_role(roleValue, roleMap)
		if roleValue is not None
		else controlTypes.Role.UNKNOWN
	)
	states = frozenset(
		atspi_mappings.map_states(
			_get_source_state_values(source),
			stateMap,
			invertedStateValues,
		),
	)

	translated = TranslatedATSPIEvent(
		kind=kind,
		rawType=rawType,
		source=source,
		sourceKey=_make_source_key(source),
		sourceName=getattr(source, "name", None),
		sourceDescription=getattr(source, "description", None),
		role=role,
		states=states,
	)
	if kind == "focus":
		return replace(
			translated,
			isFocused=_coerce_bool(getattr(event, "detail1", False)),
		)
	if kind == "caret":
		caretOffset = getattr(event, "detail1", None)
		try:
			caretOffset = int(caretOffset) if caretOffset is not None else None
		except Exception:
			caretOffset = None
		return replace(translated, caretOffset=caretOffset)
	return replace(
		translated,
		propertyName=_parse_property_name(rawType),
		propertyValue=getattr(event, "any_data", None),
	)


class ATSPI2Backend:
	"""AT-SPI2 initialization and event-listener lifecycle for Linux PAL."""

	def __init__(self) -> None:
		self._atspi: Any | None = None
		self._mainContext: Any | None = None
		self._registeredEvents: list[str] = []
		self._initialized = False
		self.roleMap: dict[int, controlTypes.Role] = {}
		self.stateMap: dict[int, controlTypes.State] = {}
		self.invertedStateValues: set[int] = set()
		self._translatedEventsByKey: OrderedDict[tuple[Any, ...], TranslatedATSPIEvent] = OrderedDict()
		self._eventListeners: list[Callable[[TranslatedATSPIEvent], None]] = []
		self._maxQueuedTranslatedEvents = _MAX_QUEUED_TRANSLATED_EVENTS

	def registerEventListener(self, listener: Callable[[TranslatedATSPIEvent], None]) -> None:
		if listener not in self._eventListeners:
			self._eventListeners.append(listener)

	def unregisterEventListener(self, listener: Callable[[TranslatedATSPIEvent], None]) -> None:
		try:
			self._eventListeners.remove(listener)
		except ValueError:
			return

	def _makeEventQueueKey(self, event: TranslatedATSPIEvent) -> tuple[Any, ...]:
		if event.kind == "propertyChange":
			return (event.kind, event.sourceKey, event.propertyName)
		return (event.kind, event.sourceKey)

	def _queueTranslatedEvent(self, event: TranslatedATSPIEvent) -> None:
		queueKey = self._makeEventQueueKey(event)
		if queueKey in self._translatedEventsByKey:
			self._translatedEventsByKey[queueKey] = event
			return
		self._translatedEventsByKey[queueKey] = event
		while len(self._translatedEventsByKey) > self._maxQueuedTranslatedEvents:
			self._dropLowestPriorityQueuedEvent()

	def _dropLowestPriorityQueuedEvent(self) -> None:
		for queueKey, queuedEvent in self._translatedEventsByKey.items():
			if queuedEvent.kind != "focus":
				del self._translatedEventsByKey[queueKey]
				return
		self._translatedEventsByKey.popitem(last=False)

	def _dispatchTranslatedEvents(self) -> None:
		events = self.drainTranslatedEvents()
		if not events:
			return
		for event in events:
			for listener in tuple(self._eventListeners):
				try:
					listener(event)
				except Exception:
					log.exception("Failed to dispatch translated AT-SPI event")

	def initialize(self) -> None:
		if self._initialized:
			return
		try:
			import pyatspi
		except ImportError as e:
			raise NotSupportedYetError("AT-SPI2 python bindings (pyatspi)") from e

		self._atspi = pyatspi
		self.roleMap = atspi_mappings.build_role_map(pyatspi)
		self.stateMap, self.invertedStateValues = atspi_mappings.build_state_map(pyatspi)

		try:
			from gi.repository import GLib
		except Exception:
			self._mainContext = None
			log.debug("GLib main context unavailable; relying on pyatspi internal dispatch.")
		else:
			self._mainContext = GLib.MainContext.default()

		for eventName in _AT_SPI_EVENT_NAMES:
			try:
				pyatspi.Registry.registerEventListener(self._onAtspiEvent, eventName)
			except Exception:
				log.exception(f"Failed to register AT-SPI event listener for {eventName}")
			else:
				self._registeredEvents.append(eventName)

		self._initialized = True

	def pump_all(self) -> None:
		if not self._initialized:
			return
		if self._mainContext is None:
			self._dispatchTranslatedEvents()
			return
		while self._mainContext.pending():
			self._mainContext.iteration(False)
		self._dispatchTranslatedEvents()

	def terminate(self) -> None:
		if not self._initialized or self._atspi is None:
			return
		for eventName in self._registeredEvents:
			try:
				self._atspi.Registry.deregisterEventListener(self._onAtspiEvent, eventName)
			except Exception:
				log.exception(f"Failed to deregister AT-SPI event listener for {eventName}")
		self._registeredEvents.clear()
		self._translatedEventsByKey.clear()
		self._eventListeners.clear()
		self._mainContext = None
		self._atspi = None
		self._initialized = False

	def drainTranslatedEvents(self) -> list[TranslatedATSPIEvent]:
		events = list(self._translatedEventsByKey.values())
		self._translatedEventsByKey.clear()
		return events

	def translateEvent(self, event: Any) -> TranslatedATSPIEvent | None:
		return translate_atspi_event(
			event,
			self.roleMap,
			self.stateMap,
			self.invertedStateValues,
		)

	def _onAtspiEvent(self, event: Any) -> None:
		try:
			translated = self.translateEvent(event)
		except Exception:
			log.exception("Failed to translate AT-SPI event")
			return
		if translated is None:
			return
		self._queueTranslatedEvent(translated)
