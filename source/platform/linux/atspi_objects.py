# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from typing import Any, Callable

import controlTypes
from NVDAObjects import NVDAObject, NVDAObjectTextInfo

from .atspi_backend import TranslatedATSPISource
from .atspi_backend import TranslatedATSPIEvent


def _clampOffset(offset: int, storyLength: int) -> int:
	return max(0, min(offset, storyLength))


def _callAccessibleMethod(accessible: Any, methodName: str, *args: Any) -> Any | None:
	if accessible is None:
		return None
	method = getattr(accessible, methodName, None)
	if not callable(method):
		return None
	try:
		return method(*args)
	except Exception:
		return None


def _getAccessibleChildCount(accessible: Any) -> int:
	value = getattr(accessible, "childCount", None)
	if value is None:
		value = _callAccessibleMethod(accessible, "getChildCount")
	if value is None:
		children = getattr(accessible, "children", None)
		try:
			return len(children)
		except Exception:
			return 0
	try:
		return max(0, int(value))
	except Exception:
		return 0


def _getAccessibleChildAt(accessible: Any, index: int) -> Any | None:
	if index < 0:
		return None
	child = _callAccessibleMethod(accessible, "getChildAtIndex", index)
	if child is not None:
		return child
	children = getattr(accessible, "children", None)
	try:
		return children[index]
	except Exception:
		return None


def _getAccessibleIndexInParent(accessible: Any) -> int | None:
	value = getattr(accessible, "indexInParent", None)
	if value is None:
		value = _callAccessibleMethod(accessible, "getIndexInParent")
	try:
		index = int(value)
	except Exception:
		return None
	return index if index >= 0 else None


def _getAccessibleParent(accessible: Any) -> Any | None:
	parent = getattr(accessible, "parent", None)
	if parent is not None:
		return parent
	return _callAccessibleMethod(accessible, "getParent") or _callAccessibleMethod(accessible, "get_parent")


class LinuxATSPITextInfo(NVDAObjectTextInfo):
	"""TextInfo implementation backed by AT-SPI text interfaces when available."""

	def _getStoryText(self) -> str:
		return self.obj._getAccessibleText()

	def _getStoryLength(self) -> int:
		return len(self._getStoryText())

	def _getCaretOffset(self) -> int:
		storyLength = self._getStoryLength()
		offset = self.obj._getAccessibleCaretOffset()
		if offset is None:
			offset = 0
		return _clampOffset(offset, storyLength)

	def _setCaretOffset(self, offset: int) -> None:
		storyLength = self._getStoryLength()
		self.obj._setAccessibleCaretOffset(_clampOffset(offset, storyLength))

	def _getSelectionOffsets(self) -> tuple[int, int]:
		storyLength = self._getStoryLength()
		selection = self.obj._getAccessibleSelectionOffsets()
		if selection is None:
			caretOffset = self._getCaretOffset()
			return caretOffset, caretOffset
		start, end = selection
		start = _clampOffset(start, storyLength)
		end = _clampOffset(end, storyLength)
		if start > end:
			start, end = end, start
		return start, end

	def _setSelectionOffsets(self, start: int, end: int) -> None:
		storyLength = self._getStoryLength()
		start = _clampOffset(start, storyLength)
		end = _clampOffset(end, storyLength)
		if start > end:
			start, end = end, start
		self.obj._setAccessibleSelectionOffsets(start, end)


class _LinuxStubAppModule:
	"""Minimal app module used until Linux process/app integration is implemented."""

	sleepMode = False

	def __init__(self, processID: int, appName: str = "linux") -> None:
		self.processID = processID
		self.appName = appName
		self._configProfileTrigger = None


class LinuxATSPIObject(NVDAObject):
	"""Minimal NVDA object wrapper for a translated AT-SPI accessible."""

	TextInfo = LinuxATSPITextInfo

	def __init__(
		self,
		*,
		chooseBestAPI: bool = False,
		sourceKey: str,
		accessible: Any = None,
		processID: int = 0,
		appModule: Any | None = None,
		name: str | None = None,
		description: str | None = None,
		role: controlTypes.Role = controlTypes.Role.UNKNOWN,
		states: frozenset[controlTypes.State] | None = None,
		objectFactory: Callable[[Any], "LinuxATSPIObject | None"] | None = None,
	) -> None:
		super().__init__()
		self.sourceKey = sourceKey
		self.accessible = accessible
		self._objectFactory = objectFactory
		self._processID = processID
		self._appModule = appModule or _LinuxStubAppModule(processID=processID)
		self._name = name or ""
		self._description = description or ""
		self._value = ""
		self._role = role
		self._states = set(states or ())
		self._caretOffset = 0
		self._selectionOffsets: tuple[int, int] | None = None

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

	def _makeObjectFromAccessible(self, accessible: Any) -> "LinuxATSPIObject | None":
		if accessible is None or self._objectFactory is None:
			return None
		return self._objectFactory(accessible)

	def _get_parent(self) -> "LinuxATSPIObject | None":
		return self._makeObjectFromAccessible(_getAccessibleParent(self.accessible))

	def _get_firstChild(self) -> "LinuxATSPIObject | None":
		return self._makeObjectFromAccessible(_getAccessibleChildAt(self.accessible, 0))

	def _get_lastChild(self) -> "LinuxATSPIObject | None":
		childCount = _getAccessibleChildCount(self.accessible)
		if childCount <= 0:
			return None
		return self._makeObjectFromAccessible(_getAccessibleChildAt(self.accessible, childCount - 1))

	def _get_next(self) -> "LinuxATSPIObject | None":
		parent = _getAccessibleParent(self.accessible)
		index = _getAccessibleIndexInParent(self.accessible)
		if parent is None or index is None:
			return None
		return self._makeObjectFromAccessible(_getAccessibleChildAt(parent, index + 1))

	def _get_previous(self) -> "LinuxATSPIObject | None":
		parent = _getAccessibleParent(self.accessible)
		index = _getAccessibleIndexInParent(self.accessible)
		if parent is None or index is None or index <= 0:
			return None
		return self._makeObjectFromAccessible(_getAccessibleChildAt(parent, index - 1))

	def _queryAccessibleText(self) -> Any | None:
		accessible = self.accessible
		if accessible is None:
			return None
		queryText = getattr(accessible, "queryText", None)
		if callable(queryText):
			try:
				return queryText()
			except Exception:
				return None
		return getattr(accessible, "text", None)

	def _getAccessibleText(self) -> str:
		text = self._value
		textInterface = self._queryAccessibleText()
		didReadTextInterface = False
		if textInterface is not None:
			getText = getattr(textInterface, "getText", None)
			if callable(getText):
				try:
					text = str(getText(0, -1))
					didReadTextInterface = True
				except Exception:
					pass
		if didReadTextInterface:
			return text
		if text:
			return text
		if self._name:
			return self._name
		if self._description:
			return self._description
		return ""

	def _getAccessibleCaretOffset(self) -> int | None:
		textInterface = self._queryAccessibleText()
		if textInterface is not None:
			try:
				return int(getattr(textInterface, "caretOffset"))
			except Exception:
				pass
		if self._selectionOffsets is not None:
			return self._selectionOffsets[1]
		return self._caretOffset

	def _setAccessibleCaretOffset(self, offset: int) -> None:
		textInterface = self._queryAccessibleText()
		if textInterface is not None:
			setCaretOffset = getattr(textInterface, "setCaretOffset", None)
			if callable(setCaretOffset):
				try:
					setCaretOffset(offset)
				except Exception:
					pass
		self._caretOffset = offset
		self._selectionOffsets = (offset, offset)

	def _getAccessibleSelectionOffsets(self) -> tuple[int, int] | None:
		textInterface = self._queryAccessibleText()
		if textInterface is not None:
			try:
				getSelection = getattr(textInterface, "getSelection")
				if callable(getSelection):
					return tuple(int(x) for x in getSelection(0))
			except Exception:
				pass
		return self._selectionOffsets

	def _setAccessibleSelectionOffsets(self, start: int, end: int) -> None:
		textInterface = self._queryAccessibleText()
		if textInterface is not None:
			setSelection = getattr(textInterface, "setSelection", None)
			if callable(setSelection):
				try:
					setSelection(0, start, end)
				except Exception:
					pass
		self._selectionOffsets = (start, end)
		self._caretOffset = end

	def updateFromTranslatedSource(self, source: TranslatedATSPISource) -> None:
		self.accessible = source.source
		if source.sourceName is not None:
			self._name = source.sourceName
		if source.sourceDescription is not None:
			self._description = source.sourceDescription
		self._role = source.role
		self._states = set(source.states)

	def updateFromTranslatedEvent(self, event: TranslatedATSPIEvent) -> None:
		self.updateFromTranslatedSource(
			TranslatedATSPISource(
				source=event.source,
				sourceKey=event.sourceKey,
				sourceName=event.sourceName,
				sourceDescription=event.sourceDescription,
				role=event.role,
				states=event.states,
			),
		)
		if event.propertyName == "name" and event.propertyValue is not None:
			self._name = str(event.propertyValue)
		elif event.propertyName == "description" and event.propertyValue is not None:
			self._description = str(event.propertyValue)
		elif event.propertyName == "value" and event.propertyValue is not None:
			self._value = str(event.propertyValue)
		elif event.kind == "caret" and event.caretOffset is not None:
			self._caretOffset = max(0, event.caretOffset)
			self._selectionOffsets = (self._caretOffset, self._caretOffset)
