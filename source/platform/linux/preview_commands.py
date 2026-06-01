# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from typing import Any, Callable


class LinuxPreviewCommandController:
	"""Small native command set used before shared global commands are portable."""

	def __init__(self, *, dispatcher: Any, announce: Callable[[str], None]) -> None:
		self._dispatcher = dispatcher
		self._announce = announce

	def handleGesture(self, gesture: Any) -> bool:
		if gesture.event.gestureName.lower() != "nvda+t":
			return False
		announcement = formatObjectAnnouncement(self._dispatcher.focusObject)
		self._announce(announcement or "unknown")
		return True


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
