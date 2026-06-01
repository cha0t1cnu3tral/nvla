# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from datetime import datetime
import time
from typing import Any, Callable


_MULTI_PRESS_TIMEOUT_SECONDS = 0.5
PREVIEW_GESTURE_NAMES = frozenset(
	(
		"nvda+1",
		"nvda+b",
		"nvda+f12",
		"nvda+h",
		"nvda+q",
		"nvda+t",
		"nvda+tab",
	),
)
_PREVIEW_HELP = (
	"NVDA 1 input help. "
	"NVDA F12 time, press twice for date. "
	"NVDA T active window title. "
	"NVDA Tab focused object. "
	"NVDA B read active accessible tree. "
	"NVDA H command help. "
	"NVDA Q exit Linux preview."
)
_PREVIEW_COMMAND_DESCRIPTIONS = {
	"nvda+1": "Toggle input help",
	"nvda+b": "Read active accessible tree",
	"nvda+f12": "Speak time, press twice for date",
	"nvda+h": "Speak supported native preview commands",
	"nvda+q": "Exit Linux preview",
	"nvda+t": "Speak active window title",
	"nvda+tab": "Speak focused object",
}


class LinuxPreviewCommandController:
	"""Small native command set used before shared global commands are portable."""

	def __init__(
		self,
		*,
		dispatcher: Any,
		announce: Callable[[str], None],
		requestStop: Callable[[], None] | None = None,
		now: Callable[[], datetime] = datetime.now,
		monotonic: Callable[[], float] = time.monotonic,
	) -> None:
		self._dispatcher = dispatcher
		self._announce = announce
		self._requestStop = requestStop
		self._now = now
		self._monotonic = monotonic
		self._inputHelpActive = False
		self._lastDateTimePressTime: float | None = None

	def handleGesture(self, gesture: Any) -> bool:
		gestureName = gesture.event.gestureName.lower()
		if gestureName == "nvda+1":
			self._inputHelpActive = not self._inputHelpActive
			self._announce("Input help on" if self._inputHelpActive else "Input help off")
			return True
		if self._inputHelpActive:
			description = _PREVIEW_COMMAND_DESCRIPTIONS.get(gestureName, "Unassigned")
			self._announce(f"{gesture.event.gestureName}: {description}")
			return True
		focusObject = self._dispatcher.focusObject
		if gestureName == "nvda+t":
			self._announce(formatObjectAnnouncement(_getTopLevelObject(focusObject)) or "No title")
			return True
		if gestureName == "nvda+tab":
			self._announce(formatObjectAnnouncement(focusObject) or "No focus")
			return True
		if gestureName == "nvda+b":
			self._announce(formatObjectTreeAnnouncement(_getTopLevelObject(focusObject)) or "No active window")
			return True
		if gestureName == "nvda+f12":
			pressTime = self._monotonic()
			value = self._now()
			if (
				self._lastDateTimePressTime is not None
				and pressTime - self._lastDateTimePressTime <= _MULTI_PRESS_TIMEOUT_SECONDS
			):
				self._announce(value.strftime("%x"))
			else:
				self._announce(value.strftime("%X"))
			self._lastDateTimePressTime = pressTime
			return True
		if gestureName == "nvda+q" and self._requestStop is not None:
			self._announce("Exiting NVDA Linux preview")
			self._requestStop()
			return True
		if gestureName == "nvda+h":
			self._announce(_PREVIEW_HELP)
			return True
		return False


def formatObjectAnnouncement(obj: Any | None) -> str:
	if obj is None:
		return ""
	parts = []
	for value in (getattr(obj, "name", None), getattr(obj, "description", None)):
		if value and value not in parts:
			parts.append(str(value))
	role = getattr(obj, "role", None)
	roleLabel = getattr(role, "displayString", None) or getattr(role, "name", None)
	if roleLabel:
		roleLabel = str(roleLabel).lower()
		if roleLabel not in parts:
			parts.append(roleLabel)
	return ", ".join(parts)


def formatObjectTreeAnnouncement(root: Any | None, *, maxObjects: int = 100) -> str:
	"""Format a bounded depth-first AT-SPI object walk for the preview read-window command."""

	if root is None:
		return ""
	announcements = []
	visitedObjects = set()
	obj = root
	while obj is not None and len(visitedObjects) < maxObjects:
		objectIdentity = id(obj)
		if objectIdentity in visitedObjects:
			break
		visitedObjects.add(objectIdentity)
		announcement = formatObjectAnnouncement(obj)
		if announcement:
			announcements.append(announcement)
		child = getattr(obj, "firstChild", None)
		if child is not None:
			obj = child
			continue
		while obj is not None and obj is not root and getattr(obj, "next", None) is None:
			obj = getattr(obj, "parent", None)
		if obj is root:
			break
		obj = getattr(obj, "next", None)
	return ". ".join(announcements)


def _getTopLevelObject(obj: Any | None) -> Any | None:
	if obj is None:
		return None
	while (parent := getattr(obj, "parent", None)) is not None:
		obj = parent
	return obj
