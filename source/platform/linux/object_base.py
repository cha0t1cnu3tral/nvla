# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from typing import Any


class LinuxNVDAObjectTextInfo:
	"""Small TextInfo contract for Linux objects during native backend bring-up."""

	def __init__(self, obj: Any, position: Any) -> None:
		self.obj = obj
		if hasattr(position, "x") and hasattr(position, "y"):
			offset = self._getOffsetFromPoint(position.x, position.y)
			self._startOffset = self._endOffset = offset
		elif position == "all":
			self._startOffset = 0
			self._endOffset = self._getStoryLength()
		elif position == "caret":
			self._startOffset = self._endOffset = self._getCaretOffset()
		else:
			self._startOffset = self._endOffset = 0

	@property
	def offsets(self) -> tuple[int, int]:
		return self._startOffset, self._endOffset

	@property
	def text(self) -> str:
		getTextRange = getattr(self, "_getTextRange", None)
		if callable(getTextRange):
			return getTextRange(self._startOffset, self._endOffset)
		return self._getStoryText()[self._startOffset : self._endOffset]

	@property
	def boundingRects(self) -> list[Any]:
		return self._get_boundingRects()

	@property
	def pointAtStart(self) -> Any:
		return self._get_pointAtStart()

	def move(self, unit: str, direction: int, endPoint: str | None = None) -> int:
		if unit != "character":
			raise NotImplementedError("Only character movement is supported")
		if endPoint == "start":
			self._startOffset = self._clamp(self._startOffset + direction)
		elif endPoint == "end":
			self._endOffset = self._clamp(self._endOffset + direction)
		else:
			offset = self._clamp(self._endOffset + direction)
			self._startOffset = self._endOffset = offset
		return direction

	def expand(self, unit: str) -> None:
		getOffsets = getattr(self, f"_get{unit.title()}Offsets", None)
		if not callable(getOffsets):
			raise NotImplementedError(f"Unsupported unit: {unit}")
		self._startOffset, self._endOffset = getOffsets(self._startOffset)

	def copy(self) -> "LinuxNVDAObjectTextInfo":
		copy = self.__class__(self.obj, "first")
		copy._startOffset = self._startOffset
		copy._endOffset = self._endOffset
		return copy

	def setEndPoint(self, other: "LinuxNVDAObjectTextInfo", relation: str) -> None:
		if relation == "endToEnd":
			self._endOffset = other._endOffset
		elif relation == "startToStart":
			self._startOffset = other._startOffset
		else:
			raise NotImplementedError(f"Unsupported endpoint relation: {relation}")

	def updateCaret(self) -> None:
		self._setCaretOffset(self._endOffset)

	def updateSelection(self) -> None:
		self._setSelectionOffsets(self._startOffset, self._endOffset)

	def _clamp(self, offset: int) -> int:
		return max(0, min(offset, self._getStoryLength()))


class LinuxNVDAObject:
	TextInfo = LinuxNVDAObjectTextInfo

	def __init__(self, *args: Any, **kwargs: Any) -> None:
		super().__init__()

	def __getattr__(self, name: str) -> Any:
		try:
			getter = object.__getattribute__(self, f"_get_{name}")
		except AttributeError:
			raise AttributeError(name) from None
		return getter()

	def makeTextInfo(self, position: Any) -> LinuxNVDAObjectTextInfo:
		return self.TextInfo(self, position)
