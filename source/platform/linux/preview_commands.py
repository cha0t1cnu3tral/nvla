# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from typing import Any, Callable


class LinuxPreviewCommandController:
	"""Small native command set used before shared global commands are portable."""

	def __init__(
		self,
		*,
		dispatcher: Any,
		announce: Callable[[str], None],
		requestStop: Callable[[], None] | None = None,
	) -> None:
		self._dispatcher = dispatcher
		self._announce = announce
		self._requestStop = requestStop

	def handleGesture(self, gesture: Any) -> bool:
		gestureName = gesture.event.gestureName.lower()
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
		if gestureName == "nvda+q" and self._requestStop is not None:
			self._announce("Exiting NVDA Linux preview")
			self._requestStop()
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
