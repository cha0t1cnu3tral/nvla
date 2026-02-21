# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from typing import Any

import controlTypes
from logHandler import log
from platform.common.errors import NotSupportedYetError

from . import atspi_mappings

_AT_SPI_EVENT_NAMES = (
	"object:state-changed:focused",
	"accessible:property-change",
	"object:text-caret-moved",
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
			return
		while self._mainContext.pending():
			self._mainContext.iteration(False)

	def terminate(self) -> None:
		if not self._initialized or self._atspi is None:
			return
		for eventName in self._registeredEvents:
			try:
				self._atspi.Registry.deregisterEventListener(self._onAtspiEvent, eventName)
			except Exception:
				log.exception(f"Failed to deregister AT-SPI event listener for {eventName}")
		self._registeredEvents.clear()
		self._mainContext = None
		self._atspi = None
		self._initialized = False

	def _onAtspiEvent(self, event: Any) -> None:
		"""AT-SPI callback placeholder for Phase 2 event bridge work."""
		del event
