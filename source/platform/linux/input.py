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
	"nvda": "NVDA",
	"super": "super",
	"shift": "shift",
	"shift_l": "shift",
	"shift_r": "shift",
}
_MODIFIER_ORDER = {
	"NVDA": 0,
	"control": 1,
	"alt": 2,
	"shift": 3,
	"super": 4,
	"meta": 5,
}


def _sortModifiers(modifiers: frozenset[str]) -> list[str]:
	return sorted(modifiers, key=lambda modifier: (_MODIFIER_ORDER.get(modifier, 100), modifier))


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
		parts = [*_sortModifiers(self.modifiers), self.keyName]
		return "+".join(part for part in parts if part)


@dataclass(frozen=True, slots=True)
class LinuxKeyboardGesture:
	"""Keyboard gesture shape ready for later NVDA inputCore integration."""

	event: LinuxKeyEvent
	source: str = "kb(linux)"

	@property
	def identifiers(self) -> tuple[str, ...]:
		return (f"{self.source}:{self.event.gestureName}",)

	@property
	def normalizedIdentifiers(self) -> tuple[str, ...]:
		return tuple(identifier.lower() for identifier in self.identifiers)

	@property
	def displayName(self) -> str:
		return self.event.gestureName

	@property
	def isCharacter(self) -> bool:
		return len(self.event.keyName) == 1 and not self.event.modifiers


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


def makeKeyboardGesture(event: LinuxKeyEvent) -> LinuxKeyboardGesture:
	return LinuxKeyboardGesture(event=event)


class LinuxInputAdapter:
	def __init__(self) -> None:
		self._keyboardObserver: Any | None = None
		self._keyboardListeners: list[Callable[[LinuxKeyEvent], None]] = []
		self._keyboardGestureExecutor: Callable[[LinuxKeyboardGesture], None] | None = None
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

	def setKeyboardGestureExecutor(
		self,
		executor: Callable[[LinuxKeyboardGesture], None] | None,
	) -> None:
		self._keyboardGestureExecutor = executor

	def feedRawKeyboardEvent(self, event: Any) -> LinuxKeyEvent:
		translated = translateRawKeyEvent(event)
		for listener in tuple(self._keyboardListeners):
			listener(translated)
		observer = self._keyboardObserver
		handleKeyEvent = getattr(observer, "handleKeyEvent", None)
		if callable(handleKeyEvent):
			handleKeyEvent(translated)
		if translated.isPressed and self._keyboardGestureExecutor is not None:
			self._keyboardGestureExecutor(makeKeyboardGesture(translated))
		return translated

	def initialize_mouse(self) -> None:
		raise NotSupportedYetError("Mouse hook initialization")

	def initialize_touch(self) -> None:
		raise NotSupportedYetError("Touch hook initialization")

	def terminate_keyboard(self) -> None:
		self._keyboardListeners.clear()
		self._keyboardGestureExecutor = None
		self._keyboardObserver = None
		self._keyboardInitialized = False

	def terminate_mouse(self) -> None:
		raise NotSupportedYetError("Mouse hook termination")

	def terminate_touch(self) -> None:
		raise NotSupportedYetError("Touch hook termination")
