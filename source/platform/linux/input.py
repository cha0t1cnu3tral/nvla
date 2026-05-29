# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from platform.common.errors import NotSupportedYetError


_MODIFIER_NAMES = {
	"alt": "alt",
	"alt_l": "alt",
	"alt_r": "alt",
	"control": "control",
	"ctrl": "control",
	"control_l": "control",
	"control_r": "control",
	"meta": "meta",
	"super": "super",
	"shift": "shift",
	"shift_l": "shift",
	"shift_r": "shift",
}


@dataclass(frozen=True, slots=True)
class LinuxKeyEvent:
	"""Normalized Linux keyboard event used before real X11/Wayland hook integration."""

	keyName: str
	isPressed: bool
	modifiers: frozenset[str]
	scanCode: int | None = None
	virtualKey: int | None = None

	@property
	def gestureName(self) -> str:
		parts = [*sorted(self.modifiers), self.keyName]
		return "+".join(part for part in parts if part)


def _normalizeKeyName(value: Any) -> str:
	keyName = str(value or "").strip()
	if not keyName:
		return "unknown"
	keyName = keyName.replace(" ", "")
	if len(keyName) == 1:
		return keyName.upper()
	return keyName[0].upper() + keyName[1:]


def _normalizeModifiers(modifiers: Any) -> frozenset[str]:
	if modifiers is None:
		return frozenset()
	normalized: set[str] = set()
	for modifier in modifiers:
		modifierName = str(modifier).strip().lower().replace("-", "_")
		if not modifierName:
			continue
		normalized.add(_MODIFIER_NAMES.get(modifierName, modifierName))
	return frozenset(normalized)


def translateRawKeyEvent(event: Any) -> LinuxKeyEvent:
	"""Translate a backend-specific Linux key event shape into a stable payload."""

	return LinuxKeyEvent(
		keyName=_normalizeKeyName(
			getattr(event, "keyName", None)
			or getattr(event, "key", None)
			or getattr(event, "name", None),
		),
		isPressed=bool(
			getattr(event, "isPressed", None)
			if getattr(event, "isPressed", None) is not None
			else getattr(event, "pressed", True)
		),
		modifiers=_normalizeModifiers(getattr(event, "modifiers", None)),
		scanCode=getattr(event, "scanCode", None),
		virtualKey=getattr(event, "virtualKey", None),
	)


class LinuxInputAdapter:
	def __init__(self) -> None:
		self._keyboardObserver: Any | None = None
		self._keyboardListeners: list[Callable[[LinuxKeyEvent], None]] = []
		self._keyboardInitialized = False

	def initialize_keyboard(self, observer) -> None:
		self._keyboardObserver = observer
		self._keyboardInitialized = True

	def registerKeyboardListener(self, listener: Callable[[LinuxKeyEvent], None]) -> None:
		if listener not in self._keyboardListeners:
			self._keyboardListeners.append(listener)

	def unregisterKeyboardListener(self, listener: Callable[[LinuxKeyEvent], None]) -> None:
		try:
			self._keyboardListeners.remove(listener)
		except ValueError:
			return

	def feedRawKeyboardEvent(self, event: Any) -> LinuxKeyEvent:
		translated = translateRawKeyEvent(event)
		for listener in tuple(self._keyboardListeners):
			listener(translated)
		observer = self._keyboardObserver
		handleKeyEvent = getattr(observer, "handleKeyEvent", None)
		if callable(handleKeyEvent):
			handleKeyEvent(translated)
		return translated

	def initialize_mouse(self) -> None:
		raise NotSupportedYetError("Mouse hook initialization")

	def initialize_touch(self) -> None:
		raise NotSupportedYetError("Touch hook initialization")

	def terminate_keyboard(self) -> None:
		self._keyboardListeners.clear()
		self._keyboardObserver = None
		self._keyboardInitialized = False

	def terminate_mouse(self) -> None:
		raise NotSupportedYetError("Mouse hook termination")

	def terminate_touch(self) -> None:
		raise NotSupportedYetError("Touch hook termination")
