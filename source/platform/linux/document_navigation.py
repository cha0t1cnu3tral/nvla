# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable


_QUICK_NAV_ROLE_NAMES: dict[str, frozenset[str]] = {
	"heading": frozenset({"HEADING"}),
	"link": frozenset({"LINK"}),
	"button": frozenset({"BUTTON", "TOGGLEBUTTON"}),
	"edit": frozenset({"EDITABLETEXT", "PASSWORDEDIT"}),
	"formField": frozenset(
		{
			"BUTTON",
			"TOGGLEBUTTON",
			"CHECKBOX",
			"RADIOBUTTON",
			"COMBOBOX",
			"EDITABLETEXT",
			"PASSWORDEDIT",
		},
	),
	"list": frozenset({"LIST"}),
	"listItem": frozenset({"LISTITEM"}),
	"table": frozenset({"TABLE"}),
	"landmark": frozenset({"LANDMARK", "SECTION"}),
}
_QUICK_NAV_GESTURES = {
	"h": "heading",
	"k": "link",
	"b": "button",
	"e": "edit",
	"f": "formField",
	"l": "list",
	"i": "listItem",
	"t": "table",
	"d": "landmark",
}
_FOCUS_MODE_ROLE_NAMES = frozenset(
	{
		"COMBOBOX",
		"EDITABLETEXT",
		"PASSWORDEDIT",
	}
)


@dataclass(frozen=True)
class DocumentPosition:
	obj: Any
	lineIndex: int
	text: str


def _roleName(obj: Any) -> str:
	role = getattr(obj, "role", None)
	return getattr(role, "name", str(role)).upper()


def _iterChildren(obj: Any) -> Iterable[Any]:
	children = getattr(obj, "children", ())
	try:
		return tuple(children)
	except TypeError:
		return ()


def _getText(obj: Any) -> str:
	for attributeName in ("basicText", "name", "description"):
		value = getattr(obj, attributeName, "")
		if isinstance(value, str) and value.strip():
			return value
	return ""


class LinuxDocumentNavigator:
	"""Linear AT-SPI document navigation without Windows virtual buffers."""

	def __init__(self, root: Any) -> None:
		self.root = root
		self._objects = tuple(self._walk(root))
		self._lines = tuple(self._buildLinePositions())
		self._lineIndex = -1
		self._currentObject: Any | None = None

	def _walk(self, obj: Any) -> Iterable[Any]:
		yield obj
		for child in _iterChildren(obj):
			yield from self._walk(child)

	def _buildLinePositions(self) -> Iterable[DocumentPosition]:
		for obj in self._objects:
			for lineIndex, line in enumerate(_getText(obj).splitlines()):
				text = line.strip()
				if text:
					yield DocumentPosition(obj=obj, lineIndex=lineIndex, text=text)

	@property
	def currentPosition(self) -> DocumentPosition | None:
		if self._lineIndex < 0 or self._lineIndex >= len(self._lines):
			return None
		return self._lines[self._lineIndex]

	def moveLine(self, direction: int) -> DocumentPosition | None:
		if not self._lines or direction == 0:
			return self.currentPosition
		nextIndex = self._lineIndex + (1 if direction > 0 else -1)
		if self._lineIndex < 0 and direction > 0:
			nextIndex = 0
		nextIndex = max(0, min(nextIndex, len(self._lines) - 1))
		self._lineIndex = nextIndex
		self._currentObject = self._lines[nextIndex].obj
		return self.currentPosition

	def moveQuickNav(self, kind: str, direction: int = 1) -> DocumentPosition | None:
		roleNames = _QUICK_NAV_ROLE_NAMES.get(kind)
		if roleNames is None:
			raise ValueError(f"Unsupported quick navigation kind: {kind}")
		currentObjectIndex = self._getCurrentObjectIndex()
		step = 1 if direction >= 0 else -1
		start = currentObjectIndex + step
		for objectIndex in range(start, len(self._objects) if step > 0 else -1, step):
			obj = self._objects[objectIndex]
			if _roleName(obj) not in roleNames:
				continue
			return self._setCurrentObject(obj)
		return None

	def _getCurrentObjectIndex(self) -> int:
		if self._currentObject is None:
			return -1
		return self._objects.index(self._currentObject)

	def _setCurrentObject(self, obj: Any) -> DocumentPosition | None:
		self._currentObject = obj
		for lineIndex, position in enumerate(self._lines):
			if position.obj is obj:
				self._lineIndex = lineIndex
				return position
		return DocumentPosition(obj=obj, lineIndex=0, text=_getText(obj) or _roleName(obj).lower())


class LinuxDocumentNavigationController:
	"""Handle a small browse-navigation key set until shared browse mode is portable."""

	def __init__(self, announce: Callable[[str], None]) -> None:
		self._announce = announce
		self._root: Any | None = None
		self._navigator: LinuxDocumentNavigator | None = None
		self._focusObject: Any | None = None
		self._isFocusMode = False
		self._isFocusModeForced = False

	def setRoot(self, root: Any | None) -> None:
		if root is self._root:
			return
		self._root = root
		self._navigator = LinuxDocumentNavigator(root) if root is not None else None
		self._isFocusModeForced = False
		self._updateAutomaticFocusMode()

	def setFocusObject(self, obj: Any | None) -> None:
		self._focusObject = obj
		if not self._isFocusModeForced:
			self._updateAutomaticFocusMode()

	@property
	def isFocusMode(self) -> bool:
		return self._isFocusMode

	def _updateAutomaticFocusMode(self) -> None:
		obj = self._focusObject
		self._isFocusMode = (
			self._navigator is not None
			and obj is not None
			and (
				_roleName(obj) in _FOCUS_MODE_ROLE_NAMES
				or bool(getattr(obj, "isEditable", False))
			)
		)

	def handleGesture(self, gesture: Any) -> bool:
		navigator = self._navigator
		if navigator is None:
			return False
		gestureName = gesture.event.gestureName.lower()
		if gestureName == "nvda+space":
			self._isFocusMode = not self._isFocusMode
			self._isFocusModeForced = True
			self._announce("Focus mode" if self._isFocusMode else "Browse mode")
			return True
		if self._isFocusMode:
			return False
		if gestureName == "downarrow":
			position = navigator.moveLine(1)
		elif gestureName == "uparrow":
			position = navigator.moveLine(-1)
		else:
			isPrevious = gestureName.startswith("shift+")
			key = gestureName.removeprefix("shift+")
			kind = _QUICK_NAV_GESTURES.get(key)
			if kind is None:
				return False
			position = navigator.moveQuickNav(kind, direction=-1 if isPrevious else 1)
		if position is None:
			return True
		self._announce(position.text)
		return True
