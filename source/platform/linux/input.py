# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from dataclasses import dataclass, replace
import re
from typing import Any, Callable, Protocol

from platform.common.errors import NotSupportedYetError

try:
	import inputCore
except Exception:
	inputCore = None


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
_MODIFIER_KEY_NAMES = frozenset(_MODIFIER_ORDER)
_IDENTIFIER_RE = re.compile(r"^kb(?:\((.+?)\))?:(.*)$")
_NVDA_KEY_CAPS_LOCK = 1
_NVDA_KEY_NUMPAD_INSERT = 2
_NVDA_KEY_EXTENDED_INSERT = 4
_DEFAULT_NVDA_MODIFIER_KEYS = _NVDA_KEY_NUMPAD_INSERT | _NVDA_KEY_EXTENDED_INSERT
_LINUX_NVDA_MODIFIER_KEY_ALIASES = {
	"caps_lock": "capslock",
	"capslock": "capslock",
	"insert": "insert",
	"insert_l": "insert",
	"insert_r": "insert",
	"ins": "insert",
	"kp_0": "numpadinsert",
	"kp_insert": "numpadinsert",
	"numpad_insert": "numpadinsert",
	"numpadinsert": "numpadinsert",
}


if inputCore is None:

	class _InputGestureBase:
		@property
		def identifiers(self) -> tuple[str, ...]:
			return self._get_identifiers()

else:
	_InputGestureBase = inputCore.InputGesture


def _sortModifiers(modifiers: frozenset[str]) -> list[str]:
	return sorted(modifiers, key=lambda modifier: (_MODIFIER_ORDER.get(modifier, 100), modifier))


def _normalizeGestureIdentifier(identifier: str) -> str:
	inputCoreModule = _getInputCore()
	if inputCoreModule is not None:
		return inputCoreModule.normalizeGestureIdentifier(identifier)
	return identifier.lower()


def _getInputCore() -> Any | None:
	global inputCore
	if inputCore is not None:
		return inputCore
	try:
		import inputCore as inputCoreModule
	except Exception:
		return None
	inputCore = inputCoreModule
	return inputCore


def _getConfiguredNVDAModifierKeys() -> int:
	try:
		import config

		return int(config.conf["keyboard"]["NVDAModifierKeys"])
	except Exception:
		return _DEFAULT_NVDA_MODIFIER_KEYS


def _canonicalizeLinuxKeyName(value: Any) -> str:
	return str(value or "").strip().lower().replace("-", "_").replace(" ", "")


def _getLinuxNVDAModifierKeyName(value: Any, nvdaModifierKeys: int | None = None) -> str | None:
	keyName = _LINUX_NVDA_MODIFIER_KEY_ALIASES.get(_canonicalizeLinuxKeyName(value))
	if keyName is None:
		return None
	if nvdaModifierKeys is None:
		nvdaModifierKeys = _getConfiguredNVDAModifierKeys()
	if keyName == "capslock" and nvdaModifierKeys & _NVDA_KEY_CAPS_LOCK:
		return "NVDA"
	if keyName == "numpadinsert" and nvdaModifierKeys & _NVDA_KEY_NUMPAD_INSERT:
		return "NVDA"
	if keyName == "insert" and nvdaModifierKeys & _NVDA_KEY_EXTENDED_INSERT:
		return "NVDA"
	return None


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


class LinuxKeyboardGesture(_InputGestureBase):
	"""Keyboard gesture that can be handed to NVDA's inputCore gesture map."""

	SPEECHEFFECT_CANCEL = "cancel"
	SPEECHEFFECT_PAUSE = "pause"
	SPEECHEFFECT_RESUME = "resume"
	bypassInputHelp = False
	reportInInputHelp = True
	shouldPreventSystemIdle = False
	wasInSayAll = False
	speechEffectWhenExecuted = SPEECHEFFECT_CANCEL

	def __init__(
		self,
		event: LinuxKeyEvent,
		compatibleLayouts: tuple[str, ...] = ("desktop", "laptop"),
	) -> None:
		self.event = event
		self.compatibleLayouts = compatibleLayouts
		super().__init__()

	def _get_identifiers(self) -> tuple[str, ...]:
		gestureName = self.event.gestureName
		return (
			*(f"kb({layout}):{gestureName}" for layout in self.compatibleLayouts),
			f"kb:{gestureName}",
		)

	@property
	def normalizedIdentifiers(self) -> tuple[str, ...]:
		return tuple(_normalizeGestureIdentifier(identifier) for identifier in self.identifiers)

	@property
	def displayName(self) -> str:
		return self.event.gestureName

	@property
	def isCharacter(self) -> bool:
		return len(self.event.keyName) == 1 and not self.event.modifiers

	@property
	def shouldReportAsCommand(self) -> bool:
		return not self.isCharacter

	@property
	def isModifier(self) -> bool:
		return self.event.keyName in _MODIFIER_KEY_NAMES

	@property
	def scriptableObject(self) -> None:
		return None

	@property
	def script(self) -> Any | None:
		import scriptHandler

		return scriptHandler.findScript(self)

	def send(self) -> None:
		raise NotImplementedError

	def reportExtra(self) -> None:
		return None

	def executeScript(self, script: Callable[["LinuxKeyboardGesture"], None]) -> None:
		import scriptHandler

		scriptHandler.executeScript(script, self)

	@classmethod
	def getDisplayTextForIdentifier(cls, identifier: str) -> tuple[str, str]:
		match = _IDENTIFIER_RE.match(identifier)
		if match is None:
			raise ValueError(f"Invalid keyboard gesture identifier: {identifier}")
		layout, keys = match.groups()
		if layout:
			source = f"{layout} keyboard"
		else:
			source = "keyboard, all layouts"
		return source, keys


def executeKeyboardGesture(
	gesture: LinuxKeyboardGesture,
	manager: Any | None = None,
) -> bool:
	"""Execute a Linux keyboard gesture through NVDA inputCore when available."""

	if manager is None:
		inputCoreModule = _getInputCore()
		if inputCoreModule is None:
			raise NotSupportedYetError("NVDA inputCore gesture execution")
		manager = inputCoreModule.manager
	else:
		inputCoreModule = _getInputCore()
	noInputGestureAction = getattr(inputCoreModule, "NoInputGestureAction", LookupError)
	try:
		manager.executeGesture(gesture)
	except noInputGestureAction:
		return False
	return True


def registerKeyboardGestureSource() -> None:
	"""Register Linux keyboard gestures for `kb:` display lookups when inputCore is loaded."""

	inputCoreModule = _getInputCore()
	if inputCoreModule is not None:
		inputCoreModule.registerGestureSource("kb", LinuxKeyboardGesture)


def _normalizeKeyName(value: Any, nvdaModifierKeys: int | None = None) -> str:
	keyName = str(value or "").strip()
	if not keyName:
		return "unknown"
	keyName = keyName.replace(" ", "")
	nvdaModifierName = _getLinuxNVDAModifierKeyName(keyName, nvdaModifierKeys)
	if nvdaModifierName is not None:
		return nvdaModifierName
	modifierName = _canonicalizeLinuxKeyName(keyName)
	if modifierName in _MODIFIER_NAMES:
		return _MODIFIER_NAMES[modifierName]
	if modifierName in _LINUX_NVDA_MODIFIER_KEY_ALIASES:
		return _LINUX_NVDA_MODIFIER_KEY_ALIASES[modifierName]
	if len(keyName) == 1:
		return keyName.upper()
	return keyName[0].upper() + keyName[1:]


def _normalizeModifiers(modifiers: Any, nvdaModifierKeys: int | None = None) -> frozenset[str]:
	if modifiers is None:
		return frozenset()
	normalized: set[str] = set()
	for modifier in modifiers:
		modifierName = _canonicalizeLinuxKeyName(modifier)
		if not modifierName:
			continue
		nvdaModifierName = _getLinuxNVDAModifierKeyName(modifierName, nvdaModifierKeys)
		if nvdaModifierName is not None:
			normalized.add(nvdaModifierName)
			continue
		normalized.add(_MODIFIER_NAMES.get(modifierName, modifierName))
	return frozenset(normalized)


def _getRawKeyName(event: Any) -> Any:
	return (
		getattr(event, "keyName", None)
		or getattr(event, "key", None)
		or getattr(event, "name", None)
	)


def translateRawKeyEvent(event: Any) -> LinuxKeyEvent:
	"""Translate a backend-specific Linux key event shape into a stable payload."""

	nvdaModifierKeys = getattr(event, "nvdaModifierKeys", None)
	return LinuxKeyEvent(
		keyName=_normalizeKeyName(
			_getRawKeyName(event),
			nvdaModifierKeys,
		),
		isPressed=bool(
			getattr(event, "isPressed", None)
			if getattr(event, "isPressed", None) is not None
			else getattr(event, "pressed", True)
		),
		modifiers=_normalizeModifiers(getattr(event, "modifiers", None), nvdaModifierKeys),
		scanCode=getattr(event, "scanCode", None),
		virtualKey=getattr(event, "virtualKey", None),
	)


class LinuxKeyboardEventSource(Protocol):
	"""Source of raw Linux keyboard events, such as X11 or Wayland backends."""

	def start(self, emit: Callable[[Any], None]) -> None: ...

	def stop(self) -> None: ...


class ManualKeyboardEventSource:
	"""Dependency-light keyboard event source used by tests and early smoke tools."""

	def __init__(self) -> None:
		self._emit: Callable[[Any], None] | None = None
		self.isStarted = False

	def start(self, emit: Callable[[Any], None]) -> None:
		self._emit = emit
		self.isStarted = True

	def stop(self) -> None:
		self._emit = None
		self.isStarted = False

	def emit(self, event: Any) -> None:
		if self._emit is None:
			raise RuntimeError("Keyboard event source has not been started")
		self._emit(event)


class X11KeyboardEventSource:
	"""X11 keyboard event source placeholder for the upcoming XInput2 implementation."""

	def start(self, emit: Callable[[Any], None]) -> None:
		raise NotSupportedYetError("X11 keyboard event capture")

	def stop(self) -> None:
		return None


class WaylandKeyboardEventSource:
	"""Wayland keyboard event source placeholder for portal/compositor-backed capture."""

	def start(self, emit: Callable[[Any], None]) -> None:
		raise NotSupportedYetError("Wayland keyboard event capture")

	def stop(self) -> None:
		return None


def makeKeyboardGesture(event: LinuxKeyEvent) -> LinuxKeyboardGesture:
	return LinuxKeyboardGesture(event=event)


def createKeyboardEventSource(environ: Any | None = None) -> LinuxKeyboardEventSource | None:
	"""Pick the most appropriate keyboard event source for the current Linux session."""

	if environ is None:
		import os

		environ = os.environ
	if environ.get("WAYLAND_DISPLAY"):
		return WaylandKeyboardEventSource()
	if environ.get("DISPLAY"):
		return X11KeyboardEventSource()
	return None


class LinuxInputAdapter:
	def __init__(self, keyboardEventSource: LinuxKeyboardEventSource | None = None) -> None:
		self._keyboardObserver: Any | None = None
		self._keyboardListeners: list[Callable[[LinuxKeyEvent], None]] = []
		self._keyboardGestureExecutor: Callable[[LinuxKeyboardGesture], None] | None = None
		self._keyboardEventSource = keyboardEventSource
		self._keyboardEventSourceStartError: Exception | None = None
		self._keyboardInitialized = False
		self._pressedNVDAModifierKeys: set[str] = set()

	@property
	def keyboardEventSourceStartError(self) -> Exception | None:
		return self._keyboardEventSourceStartError

	def initialize_keyboard(self, observer) -> None:
		self._keyboardObserver = observer
		self._keyboardInitialized = True
		if self._keyboardEventSource is None:
			self._keyboardEventSource = createKeyboardEventSource()
		if self._keyboardEventSource is not None:
			try:
				self._keyboardEventSource.start(self.feedRawKeyboardEvent)
			except NotSupportedYetError as error:
				self._keyboardEventSourceStartError = error

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

	def enableInputCoreGestureExecution(self, manager: Any | None = None) -> None:
		registerKeyboardGestureSource()
		self.setKeyboardGestureExecutor(lambda gesture: executeKeyboardGesture(gesture, manager=manager))

	def _applyPressedNVDAModifierKeys(self, event: Any, translated: LinuxKeyEvent) -> LinuxKeyEvent:
		nvdaModifierKeys = getattr(event, "nvdaModifierKeys", None)
		rawKeyName = _canonicalizeLinuxKeyName(_getRawKeyName(event))
		nvdaModifierName = _getLinuxNVDAModifierKeyName(rawKeyName, nvdaModifierKeys)
		if nvdaModifierName is not None:
			if translated.isPressed:
				self._pressedNVDAModifierKeys.add(rawKeyName)
			else:
				self._pressedNVDAModifierKeys.discard(rawKeyName)
			return translated
		if not self._pressedNVDAModifierKeys or "NVDA" in translated.modifiers:
			return translated
		return replace(translated, modifiers=translated.modifiers | {"NVDA"})

	def feedRawKeyboardEvent(self, event: Any) -> LinuxKeyEvent:
		translated = translateRawKeyEvent(event)
		translated = self._applyPressedNVDAModifierKeys(event, translated)
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
		if self._keyboardEventSource is not None:
			self._keyboardEventSource.stop()
		self._keyboardEventSourceStartError = None
		self._keyboardListeners.clear()
		self._keyboardGestureExecutor = None
		self._keyboardObserver = None
		self._keyboardInitialized = False
		self._pressedNVDAModifierKeys.clear()

	def terminate_mouse(self) -> None:
		raise NotSupportedYetError("Mouse hook termination")

	def terminate_touch(self) -> None:
		raise NotSupportedYetError("Touch hook termination")
