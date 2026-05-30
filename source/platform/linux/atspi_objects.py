# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from typing import Any, Callable, NamedTuple

import controlTypes
from NVDAObjects import NVDAObject, NVDAObjectTextInfo

from .atspi_backend import TranslatedATSPISource
from .atspi_backend import TranslatedATSPIEvent


def _clampOffset(offset: int, storyLength: int) -> int:
	return max(0, min(offset, storyLength))


class LinuxPoint(NamedTuple):
	x: int
	y: int


class LinuxRectLTWH(NamedTuple):
	left: int
	top: int
	width: int
	height: int

	@property
	def right(self) -> int:
		return self.left + self.width

	@property
	def bottom(self) -> int:
		return self.top + self.height

	@property
	def topLeft(self) -> LinuxPoint:
		return LinuxPoint(self.left, self.top)

	@property
	def center(self) -> LinuxPoint:
		return LinuxPoint(
			int(round(self.left + self.width / 2.0)),
			int(round(self.top + self.height / 2.0)),
		)


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


def _coerceRect(value: Any) -> LinuxRectLTWH | None:
	if value is None:
		return None
	if isinstance(value, (tuple, list)) and len(value) >= 4:
		parts = value[:4]
	else:
		parts = (
			getattr(value, "x", getattr(value, "left", None)),
			getattr(value, "y", getattr(value, "top", None)),
			getattr(value, "width", None),
			getattr(value, "height", None),
		)
	try:
		left, top, width, height = (int(part) for part in parts)
	except Exception:
		return None
	if width < 0 or height < 0:
		return None
	return LinuxRectLTWH(left, top, width, height)


def _unionRects(*rects: LinuxRectLTWH) -> LinuxRectLTWH | None:
	rects = tuple(rect for rect in rects if rect is not None)
	if not rects:
		return None
	left = min(rect.left for rect in rects)
	top = min(rect.top for rect in rects)
	right = max(rect.right for rect in rects)
	bottom = max(rect.bottom for rect in rects)
	return LinuxRectLTWH(left, top, right - left, bottom - top)


def _coerceOffsetRange(value: Any) -> tuple[int, int] | None:
	if value is None:
		return None
	try:
		parts = tuple(value)
	except Exception:
		return None
	if len(parts) < 2:
		return None
	if len(parts) >= 3 and isinstance(parts[1], int) and isinstance(parts[2], int):
		start, end = parts[1], parts[2]
	else:
		start, end = parts[0], parts[1]
	try:
		start = int(start)
		end = int(end)
	except Exception:
		return None
	if start < 0 or end < start:
		return None
	return start, end


def _getTextAtOffsetRange(
	textInterface: Any,
	offset: int,
	boundaryNames: tuple[str, ...],
) -> tuple[int, int] | None:
	getTextAtOffset = getattr(textInterface, "getTextAtOffset", None)
	if not callable(getTextAtOffset):
		return None
	for boundaryName in boundaryNames:
		boundaryValue = getattr(textInterface, boundaryName, boundaryName)
		try:
			offsetRange = _coerceOffsetRange(getTextAtOffset(offset, boundaryValue))
		except Exception:
			offsetRange = None
		if offsetRange is not None:
			return offsetRange
	return None


def _getLineOffsetsFromText(text: str, offset: int) -> tuple[int, int]:
	if not text:
		return 0, 0
	offset = _clampOffset(offset, len(text) - 1)
	start = text.rfind("\n", 0, offset + 1) + 1
	end = text.find("\n", offset)
	if end < 0:
		end = len(text)
	else:
		end += 1
	return start, end


def _getWordOffsetsFromText(text: str, offset: int) -> tuple[int, int]:
	if not text:
		return 0, 0
	offset = _clampOffset(offset, len(text) - 1)
	if text[offset].isspace():
		start = offset
		while start > 0 and text[start - 1].isspace():
			start -= 1
		end = offset
		while end < len(text) and text[end].isspace():
			end += 1
		return start, end
	start = offset
	while start > 0 and not text[start - 1].isspace():
		start -= 1
	end = offset
	while end < len(text) and not text[end].isspace():
		end += 1
	return start, end


def _getSentenceOffsetsFromText(text: str, offset: int) -> tuple[int, int]:
	if not text:
		return 0, 0
	offset = _clampOffset(offset, len(text) - 1)
	start = offset
	while start > 0 and text[start - 1] not in ".!?":
		start -= 1
	while start < len(text) and text[start].isspace():
		start += 1
	end = offset
	while end < len(text) and text[end] not in ".!?":
		end += 1
	if end < len(text):
		end += 1
		while end < len(text) and text[end].isspace():
			end += 1
	return start, end


def _getParagraphOffsetsFromText(text: str, offset: int) -> tuple[int, int]:
	if not text:
		return 0, 0
	offset = _clampOffset(offset, len(text) - 1)
	start = text.rfind("\n\n", 0, offset + 1)
	start = 0 if start < 0 else start + 2
	end = text.find("\n\n", offset)
	if end < 0:
		end = len(text)
	return start, end


def _getAccessibleExtents(accessible: Any) -> LinuxRectLTWH | None:
	if accessible is None:
		return None
	component = _callAccessibleMethod(accessible, "queryComponent")
	if component is None:
		component = getattr(accessible, "component", None)
	for coordType in (0, None):
		if coordType is None:
			extents = _callAccessibleMethod(component, "getExtents")
		else:
			extents = _callAccessibleMethod(component, "getExtents", coordType)
		rect = _coerceRect(extents)
		if rect is not None:
			return rect
	position = _callAccessibleMethod(component, "getPosition", 0)
	size = _callAccessibleMethod(component, "getSize")
	if position is not None and size is not None:
		try:
			return LinuxRectLTWH(int(position[0]), int(position[1]), int(size[0]), int(size[1]))
		except Exception:
			return None
	for attrName in ("extents", "location"):
		rect = _coerceRect(getattr(accessible, attrName, None))
		if rect is not None:
			return rect
	return None


class LinuxATSPITextInfo(NVDAObjectTextInfo):
	"""TextInfo implementation backed by AT-SPI text interfaces when available."""

	def _getStoryText(self) -> str:
		return self.obj._getAccessibleText()

	def _getStoryLength(self) -> int:
		textInterface = self.obj._queryAccessibleText()
		if textInterface is not None:
			try:
				return max(0, int(getattr(textInterface, "characterCount")))
			except Exception:
				pass
		return len(self._getStoryText())

	def _getTextRange(self, start: int, end: int) -> str:
		textInterface = self.obj._queryAccessibleText()
		if textInterface is not None:
			getText = getattr(textInterface, "getText", None)
			if callable(getText):
				try:
					return str(getText(start, end))
				except Exception:
					pass
		return self._getStoryText()[start:end]

	def _getLineOffsets(self, offset: int) -> tuple[int, int]:
		textInterface = self.obj._queryAccessibleText()
		if textInterface is not None:
			offsetRange = _getTextAtOffsetRange(
				textInterface,
				offset,
				("TEXT_BOUNDARY_LINE_START", "line", "lineStart"),
			)
			if offsetRange is not None:
				return offsetRange
		return _getLineOffsetsFromText(self._getStoryText(), offset)

	def _getWordOffsets(self, offset: int) -> tuple[int, int]:
		textInterface = self.obj._queryAccessibleText()
		if textInterface is not None:
			offsetRange = _getTextAtOffsetRange(
				textInterface,
				offset,
				("TEXT_BOUNDARY_WORD_START", "word", "wordStart"),
			)
			if offsetRange is not None:
				return offsetRange
		return _getWordOffsetsFromText(self._getStoryText(), offset)

	def _getSentenceOffsets(self, offset: int) -> tuple[int, int]:
		textInterface = self.obj._queryAccessibleText()
		if textInterface is not None:
			offsetRange = _getTextAtOffsetRange(
				textInterface,
				offset,
				("TEXT_BOUNDARY_SENTENCE_START", "sentence", "sentenceStart"),
			)
			if offsetRange is not None:
				return offsetRange
		return _getSentenceOffsetsFromText(self._getStoryText(), offset)

	def _getParagraphOffsets(self, offset: int) -> tuple[int, int]:
		textInterface = self.obj._queryAccessibleText()
		if textInterface is not None:
			offsetRange = _getTextAtOffsetRange(
				textInterface,
				offset,
				("TEXT_BOUNDARY_PARAGRAPH_START", "paragraph", "paragraphStart"),
			)
			if offsetRange is not None:
				return offsetRange
		return _getParagraphOffsetsFromText(self._getStoryText(), offset)

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

	def _getBoundingRectFromOffset(self, offset: int) -> LinuxRectLTWH:
		textInterface = self.obj._queryAccessibleText()
		if textInterface is None:
			raise NotImplementedError
		storyLength = self._getStoryLength()
		offset = _clampOffset(offset, max(storyLength - 1, 0))
		getCharacterExtents = getattr(textInterface, "getCharacterExtents", None)
		if callable(getCharacterExtents):
			try:
				rect = _coerceRect(getCharacterExtents(offset, 0))
			except Exception:
				rect = None
			if rect is not None:
				return rect
		getRangeExtents = getattr(textInterface, "getRangeExtents", None)
		if callable(getRangeExtents):
			try:
				rect = _coerceRect(getRangeExtents(offset, min(offset + 1, storyLength), 0))
			except Exception:
				rect = None
			if rect is not None:
				return rect
		raise NotImplementedError

	def _getOffsetFromPoint(self, x: int, y: int) -> int:
		textInterface = self.obj._queryAccessibleText()
		if textInterface is None:
			raise NotImplementedError
		getOffsetAtPoint = getattr(textInterface, "getOffsetAtPoint", None)
		if not callable(getOffsetAtPoint):
			raise NotImplementedError
		try:
			offset = int(getOffsetAtPoint(x, y, 0))
		except Exception as e:
			raise LookupError from e
		if offset < 0:
			raise LookupError
		return _clampOffset(offset, self._getStoryLength())

	def _get_boundingRects(self) -> list[LinuxRectLTWH]:
		if self._startOffset == self._endOffset:
			return []
		textInterface = self.obj._queryAccessibleText()
		if textInterface is not None:
			getRangeExtents = getattr(textInterface, "getRangeExtents", None)
			if callable(getRangeExtents):
				try:
					rect = _coerceRect(getRangeExtents(self._startOffset, self._endOffset, 0))
				except Exception:
					rect = None
				if rect is not None:
					return [rect]
		startRect = self._getBoundingRectFromOffset(self._startOffset)
		endRect = self._getBoundingRectFromOffset(max(self._endOffset - 1, self._startOffset))
		rect = _unionRects(startRect, endRect)
		if rect is None:
			raise LookupError
		return [rect]

	def _get_pointAtStart(self) -> LinuxPoint:
		return self._getBoundingRectFromOffset(self._startOffset).topLeft


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

	def _get_location(self) -> LinuxRectLTWH | None:
		return _getAccessibleExtents(self.accessible)

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
					selection = _coerceOffsetRange(getSelection(0))
					if selection is not None:
						return selection
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

	def updateFromTranslatedSource(
		self,
		source: TranslatedATSPISource,
		*,
		updateStates: bool = True,
	) -> None:
		self.accessible = source.source
		self._processID = source.sourceProcessID
		if isinstance(self._appModule, _LinuxStubAppModule):
			self._appModule.processID = source.sourceProcessID
		if source.sourceName is not None:
			self._name = source.sourceName
		if source.sourceDescription is not None:
			self._description = source.sourceDescription
		self._role = source.role
		if updateStates:
			self._states = set(source.states)

	def updateFromTranslatedEvent(self, event: TranslatedATSPIEvent) -> None:
		self.updateFromTranslatedSource(
			TranslatedATSPISource(
				source=event.source,
				sourceKey=event.sourceKey,
				sourceProcessID=event.sourceProcessID,
				sourceName=event.sourceName,
				sourceDescription=event.sourceDescription,
				role=event.role,
				states=event.states,
			),
			updateStates=event.kind != "stateChange" or event.mappedState is None,
		)
		if event.kind == "stateChange" and event.mappedState is not None:
			if event.isMappedStateEnabled:
				self._states.add(event.mappedState)
			else:
				self._states.discard(event.mappedState)
		elif event.propertyName == "name" and event.propertyValue is not None:
			self._name = str(event.propertyValue)
		elif event.propertyName == "description" and event.propertyValue is not None:
			self._description = str(event.propertyValue)
		elif event.propertyName == "value" and event.propertyValue is not None:
			self._value = str(event.propertyValue)
		elif event.kind == "caret" and event.caretOffset is not None:
			self._caretOffset = max(0, event.caretOffset)
			self._selectionOffsets = (self._caretOffset, self._caretOffset)
