# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import importlib
import re
import select
import threading
import time
from types import SimpleNamespace
from typing import Any, Callable, Protocol

from platform.common.errors import NotSupportedYetError

from .mouse import (
	LinuxMouseEvent,
	LinuxMouseEventSource,
	MouseCaptureMode,
	createMouseEventSource,
	translateRawMouseEvent,
)

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
	"super": "windows",
	"super_l": "windows",
	"super_r": "windows",
	"win": "windows",
	"windows": "windows",
	"windows_l": "windows",
	"windows_r": "windows",
	"shift": "shift",
	"shift_l": "shift",
	"shift_r": "shift",
}
_MODIFIER_ORDER = {
	"NVDA": 0,
	"control": 1,
	"alt": 2,
	"shift": 3,
	"windows": 4,
	"meta": 5,
}
_MODIFIER_KEY_NAMES = frozenset(_MODIFIER_ORDER)
_IDENTIFIER_RE = re.compile(r"^kb(?:\((.+?)\))?:(.*)$")
_NVDA_KEY_CAPS_LOCK = 1
_NVDA_KEY_NUMPAD_INSERT = 2
_NVDA_KEY_EXTENDED_INSERT = 4
_DEFAULT_NVDA_MODIFIER_KEYS = _NVDA_KEY_NUMPAD_INSERT | _NVDA_KEY_EXTENDED_INSERT
_DEFAULT_MULTI_PRESS_TIMEOUT_SECONDS = 0.5
_X11_BROWSE_KEY_NAMES = (
	"Up",
	"Down",
	"h",
	"k",
	"b",
	"e",
	"f",
	"l",
	"i",
	"t",
	"d",
)
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
_LINUX_KEY_NAME_ALIASES = {
	"back_space": "backspace",
	"caps_lock": "capslock",
	"down": "downArrow",
	"down_arrow": "downArrow",
	"esc": "escape",
	"kp_0": "numpadinsert",
	"kp_1": "numpad1",
	"kp_2": "numpad2",
	"kp_3": "numpad3",
	"kp_4": "numpad4",
	"kp_5": "numpad5",
	"kp_6": "numpad6",
	"kp_7": "numpad7",
	"kp_8": "numpad8",
	"kp_9": "numpad9",
	"kp_add": "numpadPlus",
	"kp_decimal": "numpadDelete",
	"kp_delete": "numpadDelete",
	"kp_divide": "numpadDivide",
	"kp_enter": "numpadEnter",
	"kp_insert": "numpadinsert",
	"kp_multiply": "numpadMultiply",
	"kp_subtract": "numpadMinus",
	"left": "leftArrow",
	"left_arrow": "leftArrow",
	"num_lock": "numLock",
	"page_down": "pageDown",
	"page_up": "pageUp",
	"print_screen": "printScreen",
	"right": "rightArrow",
	"right_arrow": "rightArrow",
	"scroll_lock": "scrollLock",
	"up": "upArrow",
	"up_arrow": "upArrow",
}


class KeyboardCaptureMode(Enum):
	DISABLED = "disabled"
	GLOBAL = "global"
	GLOBAL_COMMANDS = "globalCommands"
	GLOBAL_OBSERVE_ONLY = "globalObserveOnly"
	LOCAL_ONLY = "localOnly"


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
	prefix, keys = identifier.lower().split(":", 1)
	return f"{prefix}:{'+'.join(sorted(keys.split('+')))}"


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


def _getConfiguredMultiPressTimeoutSeconds() -> float:
	try:
		import config

		return float(config.conf["keyboard"]["multiPressTimeout"]) / 1000
	except Exception:
		return _DEFAULT_MULTI_PRESS_TIMEOUT_SECONDS


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
	shouldPassThrough: bool = False

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
	if modifierName in _LINUX_KEY_NAME_ALIASES:
		return _LINUX_KEY_NAME_ALIASES[modifierName]
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

	supportsPassThroughEnforcement: bool

	def start(self, emit: Callable[[Any], LinuxKeyEvent]) -> None: ...

	def stop(self) -> None: ...


class ManualKeyboardEventSource:
	"""Dependency-light keyboard event source used by tests and early smoke tools."""

	supportsPassThroughEnforcement = True

	def __init__(self) -> None:
		self._emit: Callable[[Any], LinuxKeyEvent] | None = None
		self.isStarted = False

	def start(self, emit: Callable[[Any], LinuxKeyEvent]) -> None:
		self._emit = emit
		self.isStarted = True

	def stop(self) -> None:
		self._emit = None
		self.isStarted = False

	def emit(self, event: Any) -> LinuxKeyEvent:
		if self._emit is None:
			raise RuntimeError("Keyboard event source has not been started")
		return self._emit(event)


class X11KeyboardEventSource:
	"""Observe global X11 key events through the X RECORD extension."""

	supportsPassThroughEnforcement = False

	def __init__(
		self,
		*,
		loadXlibModules: Callable[[], Any] | None = None,
	) -> None:
		self._loadXlibModules = loadXlibModules or _loadXlibModules
		self._emit: Callable[[Any], LinuxKeyEvent] | None = None
		self._modules: Any | None = None
		self._controlDisplay: Any | None = None
		self._recordDisplay: Any | None = None
		self._context: Any | None = None
		self._thread: threading.Thread | None = None
		self._pressedModifiers: set[str] = set()

	def start(self, emit: Callable[[Any], LinuxKeyEvent]) -> None:
		if self._thread is not None:
			return
		modules = self._loadXlibModules()
		controlDisplay = modules.display.Display()
		recordDisplay = modules.display.Display()
		try:
			if not controlDisplay.has_extension("RECORD"):
				raise NotSupportedYetError("X11 RECORD extension")
			context = recordDisplay.record_create_context(
				0,
				[modules.record.AllClients],
				[
					{
						"core_requests": (0, 0),
						"core_replies": (0, 0),
						"ext_requests": (0, 0, 0, 0),
						"ext_replies": (0, 0, 0, 0),
						"delivered_events": (0, 0),
						"device_events": (modules.X.KeyPress, modules.X.KeyRelease),
						"errors": (0, 0),
						"client_started": False,
						"client_died": False,
					},
				],
			)
		except Exception:
			controlDisplay.close()
			recordDisplay.close()
			raise
		self._modules = modules
		self._emit = emit
		self._controlDisplay = controlDisplay
		self._recordDisplay = recordDisplay
		self._context = context
		self._thread = threading.Thread(
			target=recordDisplay.record_enable_context,
			args=(context, self._handleRecordReply),
			name="X11KeyboardEventSource",
			daemon=True,
		)
		self._thread.start()

	def stop(self) -> None:
		thread = self._thread
		controlDisplay = self._controlDisplay
		context = self._context
		if controlDisplay is not None and context is not None:
			try:
				controlDisplay.record_disable_context(context)
				controlDisplay.flush()
			except Exception:
				pass
		if thread is not None:
			thread.join(timeout=1)
		if controlDisplay is not None and context is not None:
			try:
				controlDisplay.record_free_context(context)
			except Exception:
				pass
		for display in (self._recordDisplay, controlDisplay):
			if display is not None:
				try:
					display.close()
				except Exception:
					pass
		self._emit = None
		self._modules = None
		self._controlDisplay = None
		self._recordDisplay = None
		self._context = None
		self._thread = None
		self._pressedModifiers.clear()

	def _handleRecordReply(self, reply: Any) -> None:
		modules = self._modules
		emit = self._emit
		if (
			modules is None
			or emit is None
			or reply.category != modules.record.FromServer
			or reply.client_swapped
			or not reply.data
		):
			return
		data = reply.data
		while data:
			event, data = modules.rq.EventField(None).parse_binary_value(
				data,
				self._recordDisplay.display,
				None,
				None,
			)
			if event.type not in (modules.X.KeyPress, modules.X.KeyRelease):
				continue
			keyName = self._getKeyName(event.detail)
			isPressed = event.type == modules.X.KeyPress
			modifierName = _MODIFIER_NAMES.get(_canonicalizeLinuxKeyName(keyName))
			modifiers = set(self._pressedModifiers)
			if modifierName is not None:
				if isPressed:
					self._pressedModifiers.add(keyName)
				else:
					self._pressedModifiers.discard(keyName)
			emit(
				SimpleNamespace(
					key=keyName,
					pressed=isPressed,
					modifiers=modifiers,
					scanCode=event.detail,
				),
			)

	def _getKeyName(self, keyCode: int) -> str:
		modules = self._modules
		keysym = self._recordDisplay.keycode_to_keysym(keyCode, 0)
		return modules.XK.keysym_to_string(keysym) or f"keycode_{keyCode}"


class X11NVDAModifierKeyboardEventSource:
	"""Capture X11 NVDA modifier chords through synchronous passive grabs."""

	supportsPassThroughEnforcement = False
	supportsHandledGestureSuppression = True

	def __init__(
		self,
		*,
		loadXlibModules: Callable[[], Any] | None = None,
		nvdaModifierKeys: int | None = None,
	) -> None:
		self._loadXlibModules = loadXlibModules or _loadXlibModules
		self._nvdaModifierKeys = (
			_getConfiguredNVDAModifierKeys()
			if nvdaModifierKeys is None
			else nvdaModifierKeys
		)
		self._emit: Callable[[Any], LinuxKeyEvent] | None = None
		self._modules: Any | None = None
		self._display: Any | None = None
		self._rootWindow: Any | None = None
		self._grabbedKeys: tuple[tuple[int, int], ...] = ()
		self._stopEvent = threading.Event()
		self._thread: threading.Thread | None = None

	def start(self, emit: Callable[[Any], LinuxKeyEvent]) -> None:
		if self._thread is not None:
			return
		modules = self._loadXlibModules()
		display = modules.display.Display()
		rootWindow = display.screen().root
		grabbedKeys = self._getConfiguredKeys(modules, display)
		try:
			for keyCode, modifiers in grabbedKeys:
				rootWindow.grab_key(
					keyCode,
					modifiers,
					False,
					modules.X.GrabModeAsync,
					modules.X.GrabModeSync,
				)
			display.sync()
		except Exception:
			for keyCode, modifiers in grabbedKeys:
				try:
					rootWindow.ungrab_key(keyCode, modifiers)
				except Exception:
					pass
			display.close()
			raise
		self._modules = modules
		self._display = display
		self._rootWindow = rootWindow
		self._grabbedKeys = grabbedKeys
		self._emit = emit
		self._stopEvent.clear()
		self._thread = threading.Thread(
			target=self._run,
			name="X11NVDAModifierKeyboardEventSource",
			daemon=True,
		)
		self._thread.start()

	def stop(self) -> None:
		thread = self._thread
		display = self._display
		rootWindow = self._rootWindow
		modules = self._modules
		self._stopEvent.set()
		if thread is not None:
			thread.join(timeout=1)
		if display is not None and rootWindow is not None and modules is not None:
			for keyCode, modifiers in self._grabbedKeys:
				try:
					rootWindow.ungrab_key(keyCode, modifiers)
				except Exception:
					pass
			try:
				display.flush()
			except Exception:
				pass
			try:
				display.close()
			except Exception:
				pass
		self._emit = None
		self._modules = None
		self._display = None
		self._rootWindow = None
		self._grabbedKeys = ()
		self._thread = None

	def _run(self) -> None:
		display = self._display
		if display is None:
			return
		while not self._stopEvent.wait(0.01):
			while display.pending_events():
				self._handleGrabbedEvent(display.next_event())

	def _handleGrabbedEvent(self, event: Any) -> None:
		modules = self._modules
		display = self._display
		emit = self._emit
		if modules is None or display is None or emit is None:
			return
		if event.type not in (modules.X.KeyPress, modules.X.KeyRelease):
			return
		translated = emit(
			SimpleNamespace(
				key=self._getKeyName(event.detail),
				pressed=event.type == modules.X.KeyPress,
				modifiers=self._getModifiers(event.state),
				nvdaModifierKeys=self._nvdaModifierKeys,
				scanCode=event.detail,
			),
		)
		display.allow_events(
			modules.X.ReplayKeyboard if translated.shouldPassThrough else modules.X.SyncKeyboard,
			getattr(event, "time", modules.X.CurrentTime),
		)
		display.flush()

	def _getConfiguredKeys(self, modules: Any, display: Any) -> tuple[tuple[int, int], ...]:
		keyNames = []
		if self._nvdaModifierKeys & _NVDA_KEY_CAPS_LOCK:
			keyNames.append("Caps_Lock")
		if self._nvdaModifierKeys & _NVDA_KEY_NUMPAD_INSERT:
			keyNames.extend(("KP_Insert", "KP_0"))
		if self._nvdaModifierKeys & _NVDA_KEY_EXTENDED_INSERT:
			keyNames.append("Insert")
		keys = {
			(keyCode, modules.X.AnyModifier)
			for keyName in keyNames
			if (keyCode := self._getKeyCode(modules, display, keyName))
		}
		browseModifierMasks = self._getBrowseModifierMasks(modules)
		keys.update(
			(keyCode, modifiers)
			for keyName in _X11_BROWSE_KEY_NAMES
			if (keyCode := self._getKeyCode(modules, display, keyName))
			for modifiers in browseModifierMasks
		)
		return tuple(
			sorted(
				keys,
			),
		)

	def _getKeyCode(self, modules: Any, display: Any, keyName: str) -> int:
		try:
			return display.keysym_to_keycode(modules.XK.string_to_keysym(keyName))
		except Exception:
			return 0

	def _getBrowseModifierMasks(self, modules: Any) -> tuple[int, ...]:
		shiftMask = modules.X.ShiftMask
		ignoredMasks = (
			getattr(modules.X, "LockMask", 0),
			getattr(modules.X, "Mod2Mask", 0),
		)
		return tuple(
			sorted(
				{
					baseMask | lockMask | numLockMask
					for baseMask in (0, shiftMask)
					for lockMask in (0, ignoredMasks[0])
					for numLockMask in (0, ignoredMasks[1])
				},
			),
		)

	def _getKeyName(self, keyCode: int) -> str:
		keysym = self._display.keycode_to_keysym(keyCode, 0)
		return self._modules.XK.keysym_to_string(keysym) or f"keycode_{keyCode}"

	def _getModifiers(self, state: int) -> set[str]:
		modules = self._modules
		modifierMasks = (
			(modules.X.ControlMask, "control"),
			(modules.X.Mod1Mask, "alt"),
			(modules.X.ShiftMask, "shift"),
			(modules.X.Mod4Mask, "super"),
		)
		return {name for mask, name in modifierMasks if state & mask}


class WaylandKeyboardEventSource:
	"""Capture Wayland keyboard events through evdev and replay unhandled keys with uinput."""

	supportsPassThroughEnforcement = True

	def __init__(
		self,
		*,
		loadEvdevModule: Callable[[], Any] | None = None,
		selectReadable: Callable[..., Any] = select.select,
	) -> None:
		self._loadEvdevModule = loadEvdevModule or _loadEvdevModule
		self._selectReadable = selectReadable
		self._emit: Callable[[Any], LinuxKeyEvent] | None = None
		self._module: Any | None = None
		self._devices: tuple[Any, ...] = ()
		self._uinput: Any | None = None
		self._pressedModifiers: set[str] = set()
		self._stopEvent = threading.Event()
		self._thread: threading.Thread | None = None

	def start(self, emit: Callable[[Any], LinuxKeyEvent]) -> None:
		if self._thread is not None:
			return
		module = self._loadEvdevModule()
		devices = _openEvdevKeyboards(module)
		if not devices:
			raise NotSupportedYetError("readable Wayland evdev keyboard devices")
		uinput = None
		grabbedDevices = []
		try:
			uinput = module.UInput.from_device(*devices, name="NVDA Linux Wayland keyboard replay")
			for device in devices:
				device.grab()
				grabbedDevices.append(device)
		except Exception:
			for device in grabbedDevices:
				try:
					device.ungrab()
				except Exception:
					pass
			for device in devices:
				try:
					device.close()
				except Exception:
					pass
			if uinput is not None:
				try:
					uinput.close()
				except Exception:
					pass
			raise
		self._module = module
		self._devices = devices
		self._uinput = uinput
		self._emit = emit
		self._stopEvent.clear()
		self._thread = threading.Thread(
			target=self._run,
			name="WaylandKeyboardEventSource",
			daemon=True,
		)
		self._thread.start()

	def stop(self) -> None:
		thread = self._thread
		self._stopEvent.set()
		if thread is not None:
			thread.join(timeout=1)
		for device in self._devices:
			try:
				device.ungrab()
			except Exception:
				pass
			try:
				device.close()
			except Exception:
				pass
		if self._uinput is not None:
			try:
				self._uinput.close()
			except Exception:
				pass
		self._emit = None
		self._module = None
		self._devices = ()
		self._uinput = None
		self._pressedModifiers.clear()
		self._thread = None

	def _run(self) -> None:
		while not self._stopEvent.is_set():
			readable, _writable, _exceptional = self._selectReadable(self._devices, (), (), 0.1)
			for device in readable:
				for event in device.read():
					self._handleInputEvent(event)

	def _handleInputEvent(self, event: Any) -> None:
		module = self._module
		emit = self._emit
		uinput = self._uinput
		if module is None or emit is None or uinput is None or event.type != module.ecodes.EV_KEY:
			return
		keyName = _getEvdevKeyName(module.ecodes, event.code)
		translated = emit(
			SimpleNamespace(
				key=keyName,
				pressed=event.value != 0,
				modifiers=set(self._pressedModifiers),
				scanCode=event.code,
			),
		)
		modifierName = _MODIFIER_NAMES.get(_canonicalizeLinuxKeyName(keyName))
		if modifierName is not None:
			if event.value != 0:
				self._pressedModifiers.add(keyName)
			else:
				self._pressedModifiers.discard(keyName)
		if translated.shouldPassThrough or (
			modifierName is not None
			and _getLinuxNVDAModifierKeyName(keyName) is None
		):
			uinput.write(module.ecodes.EV_KEY, event.code, event.value)
			uinput.syn()


def _loadEvdevModule() -> Any:
	try:
		return importlib.import_module("evdev")
	except ImportError as error:
		raise NotSupportedYetError("python3-evdev for Wayland keyboard capture") from error


def _isEvdevKeyboard(device: Any, ecodes: Any) -> bool:
	keyCapabilities = device.capabilities().get(ecodes.EV_KEY, ())
	return ecodes.KEY_A in keyCapabilities and ecodes.KEY_Z in keyCapabilities


def _openEvdevKeyboards(module: Any) -> tuple[Any, ...]:
	keyboards = []
	for path in module.list_devices():
		try:
			device = module.InputDevice(path)
		except OSError:
			continue
		if _isEvdevKeyboard(device, module.ecodes):
			keyboards.append(device)
		else:
			device.close()
	return tuple(keyboards)


def _getEvdevKeyName(ecodes: Any, code: int) -> str:
	name = ecodes.KEY.get(code, f"KEYCODE_{code}")
	if isinstance(name, tuple):
		name = name[0]
	name = str(name).removeprefix("KEY_").lower()
	return {
		"leftctrl": "control_l",
		"rightctrl": "control_r",
		"leftalt": "alt_l",
		"rightalt": "alt_r",
		"leftshift": "shift_l",
		"rightshift": "shift_r",
		"leftmeta": "super_l",
		"rightmeta": "super_r",
		"capslock": "caps_lock",
		"kp0": "kp_0",
		"kpinsert": "kp_insert",
	}.get(name, name)


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
		return X11NVDAModifierKeyboardEventSource()
	return None


class LinuxInputAdapter:
	def __init__(
		self,
		keyboardEventSource: LinuxKeyboardEventSource | None = None,
		clock: Callable[[], float] = time.monotonic,
		multiPressTimeoutSeconds: float | None = None,
	) -> None:
		self._keyboardObserver: Any | None = None
		self._keyboardListeners: list[Callable[[LinuxKeyEvent], None]] = []
		self._keyboardGestureExecutor: Callable[[LinuxKeyboardGesture], bool | None] | None = None
		self._keyboardGestureHandlers: list[Callable[[LinuxKeyboardGesture], bool]] = []
		self._keyboardEventSource = keyboardEventSource
		self._keyboardEventSourceStarted = False
		self._keyboardEventSourceStartError: Exception | None = None
		self._keyboardCaptureMode = KeyboardCaptureMode.DISABLED
		self._keyboardInitialized = False
		self._mouseListeners: list[Callable[[LinuxMouseEvent], None]] = []
		self._mouseEventSource: LinuxMouseEventSource | None = None
		self._mouseEventSourceStarted = False
		self._mouseEventSourceStartError: Exception | None = None
		self._mouseCaptureMode = MouseCaptureMode.DISABLED
		self._mouseInitialized = False
		self._pressedNVDAModifierKeys: set[str] = set()
		self._bypassedNVDAModifierKeys: set[str] = set()
		self._pressedPassThroughKeys: set[str] = set()
		self._passNextKeyThroughArmed = False
		self._requestedPassThroughKeys: set[str] = set()
		self._lastNVDAModifierKey: str | None = None
		self._lastNVDAModifierReleaseTime: float | None = None
		self._clock = clock
		self._multiPressTimeoutSeconds = (
			_getConfiguredMultiPressTimeoutSeconds()
			if multiPressTimeoutSeconds is None
			else multiPressTimeoutSeconds
		)

	@property
	def keyboardEventSourceStartError(self) -> Exception | None:
		return self._keyboardEventSourceStartError

	@property
	def keyboardCaptureMode(self) -> KeyboardCaptureMode:
		return self._keyboardCaptureMode

	@property
	def mouseEventSourceStartError(self) -> Exception | None:
		return self._mouseEventSourceStartError

	@property
	def mouseCaptureMode(self) -> MouseCaptureMode:
		return self._mouseCaptureMode

	def initialize_keyboard(self, observer) -> None:
		if self._keyboardInitialized:
			return
		self._keyboardObserver = observer
		self._keyboardInitialized = True
		if self._keyboardEventSource is None:
			self._keyboardEventSource = createKeyboardEventSource()
		if self._keyboardEventSource is not None:
			try:
				self._keyboardEventSource.start(self.feedRawKeyboardEvent)
			except Exception as error:
				try:
					self._keyboardEventSource.stop()
				except Exception:
					pass
				self._keyboardEventSourceStartError = error
				self._keyboardCaptureMode = KeyboardCaptureMode.LOCAL_ONLY
			else:
				self._keyboardEventSourceStarted = True
				self._keyboardCaptureMode = (
					KeyboardCaptureMode.GLOBAL
					if getattr(self._keyboardEventSource, "supportsPassThroughEnforcement", False)
					else KeyboardCaptureMode.GLOBAL_COMMANDS
					if getattr(self._keyboardEventSource, "supportsHandledGestureSuppression", False)
					else KeyboardCaptureMode.GLOBAL_OBSERVE_ONLY
				)
		else:
			self._keyboardCaptureMode = KeyboardCaptureMode.LOCAL_ONLY

	def registerKeyboardListener(self, listener: Callable[[LinuxKeyEvent], None]) -> None:
		if listener not in self._keyboardListeners:
			self._keyboardListeners.append(listener)

	def unregisterKeyboardListener(self, listener: Callable[[LinuxKeyEvent], None]) -> None:
		try:
			self._keyboardListeners.remove(listener)
		except ValueError:
			return

	def registerMouseListener(self, listener: Callable[[LinuxMouseEvent], None]) -> None:
		if listener not in self._mouseListeners:
			self._mouseListeners.append(listener)

	def unregisterMouseListener(self, listener: Callable[[LinuxMouseEvent], None]) -> None:
		try:
			self._mouseListeners.remove(listener)
		except ValueError:
			return

	def setKeyboardGestureExecutor(
		self,
		executor: Callable[[LinuxKeyboardGesture], bool | None] | None,
	) -> None:
		self._keyboardGestureExecutor = executor

	def registerKeyboardGestureHandler(
		self,
		handler: Callable[[LinuxKeyboardGesture], bool],
		*,
		first: bool = False,
	) -> None:
		if handler not in self._keyboardGestureHandlers:
			if first:
				self._keyboardGestureHandlers.insert(0, handler)
			else:
				self._keyboardGestureHandlers.append(handler)

	def unregisterKeyboardGestureHandler(self, handler: Callable[[LinuxKeyboardGesture], bool]) -> None:
		try:
			self._keyboardGestureHandlers.remove(handler)
		except ValueError:
			return

	def enableInputCoreGestureExecution(self, manager: Any | None = None) -> None:
		registerKeyboardGestureSource()
		self.setKeyboardGestureExecutor(lambda gesture: executeKeyboardGesture(gesture, manager=manager))

	def passNextKeyThrough(self) -> None:
		"""Replay the next physical key sequence without invoking NVDA commands."""

		self._passNextKeyThroughArmed = True

	def _applyPressedNVDAModifierKeys(self, event: Any, translated: LinuxKeyEvent) -> LinuxKeyEvent:
		nvdaModifierKeys = getattr(event, "nvdaModifierKeys", None)
		rawKeyName = _canonicalizeLinuxKeyName(_getRawKeyName(event))
		nvdaModifierName = _getLinuxNVDAModifierKeyName(rawKeyName, nvdaModifierKeys)
		if nvdaModifierName is not None:
			if translated.isPressed:
				if rawKeyName in self._bypassedNVDAModifierKeys or (
					rawKeyName == self._lastNVDAModifierKey
					and self._lastNVDAModifierReleaseTime is not None
					and self._clock() - self._lastNVDAModifierReleaseTime < self._multiPressTimeoutSeconds
				):
					self._bypassedNVDAModifierKeys.add(rawKeyName)
					return replace(
						translated,
						keyName=_normalizeKeyName(rawKeyName, nvdaModifierKeys=0),
						shouldPassThrough=True,
					)
				self._pressedNVDAModifierKeys.add(rawKeyName)
			else:
				if rawKeyName in self._bypassedNVDAModifierKeys:
					self._bypassedNVDAModifierKeys.discard(rawKeyName)
					return replace(
						translated,
						keyName=_normalizeKeyName(rawKeyName, nvdaModifierKeys=0),
						shouldPassThrough=True,
					)
				self._pressedNVDAModifierKeys.discard(rawKeyName)
				if rawKeyName == self._lastNVDAModifierKey:
					self._lastNVDAModifierReleaseTime = self._clock()
			self._lastNVDAModifierKey = rawKeyName
			return translated
		if translated.isPressed:
			self._lastNVDAModifierKey = None
			self._lastNVDAModifierReleaseTime = None
		if not self._pressedNVDAModifierKeys or "NVDA" in translated.modifiers:
			return translated
		return replace(translated, modifiers=translated.modifiers | {"NVDA"})

	def feedRawKeyboardEvent(self, event: Any) -> LinuxKeyEvent:
		translated = translateRawKeyEvent(event)
		translated = self._applyPressedNVDAModifierKeys(event, translated)
		rawKeyName = _canonicalizeLinuxKeyName(_getRawKeyName(event))
		if (
			translated.isPressed
			and (self._passNextKeyThroughArmed or self._requestedPassThroughKeys)
		) or rawKeyName in self._requestedPassThroughKeys:
			translated = replace(translated, shouldPassThrough=True)
			if translated.isPressed:
				self._passNextKeyThroughArmed = False
				if rawKeyName:
					self._requestedPassThroughKeys.add(rawKeyName)
			else:
				self._requestedPassThroughKeys.discard(rawKeyName)
		if rawKeyName in self._pressedPassThroughKeys:
			translated = replace(translated, shouldPassThrough=True)
			if not translated.isPressed:
				self._pressedPassThroughKeys.discard(rawKeyName)
		gesture = makeKeyboardGesture(translated)
		if (
			translated.isPressed
			and not translated.shouldPassThrough
			and not gesture.isModifier
			and not any(handler(gesture) for handler in tuple(self._keyboardGestureHandlers))
			and (
				self._keyboardGestureExecutor is None
				or self._keyboardGestureExecutor(gesture) is False
			)
		):
			translated = replace(translated, shouldPassThrough=True)
			if rawKeyName:
				self._pressedPassThroughKeys.add(rawKeyName)
			self._pressedNVDAModifierKeys.clear()
		for listener in tuple(self._keyboardListeners):
			listener(translated)
		observer = self._keyboardObserver
		handleKeyEvent = getattr(observer, "handleKeyEvent", None)
		if callable(handleKeyEvent):
			handleKeyEvent(translated)
		return translated

	def feedRawMouseEvent(self, event: Any) -> LinuxMouseEvent:
		translated = translateRawMouseEvent(event)
		for listener in tuple(self._mouseListeners):
			listener(translated)
		return translated

	def initialize_mouse(self, eventSource: LinuxMouseEventSource | None = None) -> None:
		if self._mouseInitialized:
			return
		self._mouseInitialized = True
		if eventSource is None:
			import os

			eventSource = createMouseEventSource(os.environ)
		self._mouseEventSource = eventSource
		if eventSource is None:
			self._mouseCaptureMode = MouseCaptureMode.LOCAL_ONLY
			return
		try:
			eventSource.start(self.feedRawMouseEvent)
		except Exception as error:
			try:
				eventSource.stop()
			except Exception:
				pass
			self._mouseEventSourceStartError = error
			self._mouseCaptureMode = MouseCaptureMode.LOCAL_ONLY
		else:
			self._mouseEventSourceStarted = True
			self._mouseCaptureMode = MouseCaptureMode.GLOBAL_OBSERVE_ONLY

	def initialize_touch(self) -> None:
		raise NotSupportedYetError("Touch hook initialization")

	def terminate_keyboard(self) -> None:
		if not self._keyboardInitialized:
			return
		if self._keyboardEventSourceStarted and self._keyboardEventSource is not None:
			try:
				self._keyboardEventSource.stop()
			except Exception:
				pass
		self._keyboardEventSourceStarted = False
		self._keyboardEventSourceStartError = None
		self._keyboardCaptureMode = KeyboardCaptureMode.DISABLED
		self._keyboardListeners.clear()
		self._keyboardGestureExecutor = None
		self._keyboardObserver = None
		self._keyboardInitialized = False
		self._pressedNVDAModifierKeys.clear()
		self._bypassedNVDAModifierKeys.clear()
		self._pressedPassThroughKeys.clear()
		self._passNextKeyThroughArmed = False
		self._requestedPassThroughKeys.clear()
		self._lastNVDAModifierKey = None
		self._lastNVDAModifierReleaseTime = None

	def terminate_mouse(self) -> None:
		if not self._mouseInitialized:
			return
		if self._mouseEventSourceStarted and self._mouseEventSource is not None:
			try:
				self._mouseEventSource.stop()
			except Exception:
				pass
		self._mouseListeners.clear()
		self._mouseEventSource = None
		self._mouseEventSourceStarted = False
		self._mouseEventSourceStartError = None
		self._mouseCaptureMode = MouseCaptureMode.DISABLED
		self._mouseInitialized = False

	def terminate_touch(self) -> None:
		raise NotSupportedYetError("Touch hook termination")


def _loadXlibModules() -> Any:
	try:
		return SimpleNamespace(
			X=importlib.import_module("Xlib.X"),
			XK=importlib.import_module("Xlib.XK"),
			display=importlib.import_module("Xlib.display"),
			record=importlib.import_module("Xlib.ext.record"),
			rq=importlib.import_module("Xlib.protocol.rq"),
		)
	except ImportError as error:
		raise NotSupportedYetError("python-xlib for X11 global keyboard capture") from error
