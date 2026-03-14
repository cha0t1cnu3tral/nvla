# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from typing import Any

import controlTypes
from NVDAObjects import NVDAObject

from .atspi_backend import TranslatedATSPIEvent


class _LinuxStubAppModule:
	"""Minimal app module used until Linux process/app integration is implemented."""

	sleepMode = False

	def __init__(self, processID: int, appName: str = "linux") -> None:
		self.processID = processID
		self.appName = appName
		self._configProfileTrigger = None


class LinuxATSPIObject(NVDAObject):
	"""Minimal NVDA object wrapper for a translated AT-SPI accessible."""

	def __init__(
		self,
		*,
		sourceKey: str,
		accessible: Any = None,
		processID: int = 0,
		appModule: Any | None = None,
		name: str | None = None,
		description: str | None = None,
		role: controlTypes.Role = controlTypes.Role.UNKNOWN,
		states: frozenset[controlTypes.State] | None = None,
	) -> None:
		super().__init__()
		self.sourceKey = sourceKey
		self.accessible = accessible
		self._processID = processID
		self._appModule = appModule or _LinuxStubAppModule(processID=processID)
		self._name = name or ""
		self._description = description or ""
		self._value = ""
		self._role = role
		self._states = set(states or ())

	def _isEqual(self, other):
		return self.sourceKey == other.sourceKey

	def _get_processID(self) -> int:
		return self._processID

	def _get_appModule(self) -> Any:
		return self._appModule

	def _get_name(self) -> str:
		return self._name

	def _get_description(self) -> str:
		return self._description

	def _get_value(self) -> str:
		return self._value

	def _get_role(self) -> controlTypes.Role:
		return self._role

	def _get_states(self) -> set[controlTypes.State]:
		return set(self._states)

	def _get_basicText(self) -> str:
		return self._name or self._description or ""

	def _get_location(self):
		return None

	def _get_isInForeground(self) -> bool:
		return controlTypes.State.FOCUSED in self._states

	def updateFromTranslatedEvent(self, event: TranslatedATSPIEvent) -> None:
		self.accessible = event.source
		if event.sourceName is not None:
			self._name = event.sourceName
		if event.sourceDescription is not None:
			self._description = event.sourceDescription
		if event.propertyName == "name" and event.propertyValue is not None:
			self._name = str(event.propertyValue)
		elif event.propertyName == "description" and event.propertyValue is not None:
			self._description = str(event.propertyValue)
		elif event.propertyName == "value" and event.propertyValue is not None:
			self._value = str(event.propertyValue)
		self._role = event.role
		self._states = set(event.states)
