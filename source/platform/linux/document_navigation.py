# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


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
