# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

import unittest

from platform.linux.object_base import LinuxNVDAObject, LinuxNVDAObjectTextInfo


class _TextInfo(LinuxNVDAObjectTextInfo):
	def _getStoryText(self):
		return self.obj.text

	def _getStoryLength(self):
		return len(self._getStoryText())

	def _getLineOffsets(self, offset):
		return 0, len(self._getStoryText())

	def _getCaretOffset(self):
		return self.obj.caret

	def _setCaretOffset(self, offset):
		self.obj.caret = offset

	def _setSelectionOffsets(self, start, end):
		self.obj.selection = start, end


class _Object(LinuxNVDAObject):
	TextInfo = _TextInfo

	def __init__(self):
		self.text = "hello"
		self.caret = 2
		self.selection = None

	def _get_name(self):
		return "example"


class TestLinuxNVDAObjectBase(unittest.TestCase):
	def testResolvesGetterProperties(self):
		self.assertEqual("example", _Object().name)

	def testMissingGetterRaisesAttributeErrorWithoutRecursing(self):
		with self.assertRaises(AttributeError):
			_Object().children

	def testCreatesAndMovesTextInfo(self):
		obj = _Object()
		info = obj.makeTextInfo("caret")
		self.assertEqual((2, 2), info.offsets)
		info.move("character", 2)
		info.updateCaret()
		self.assertEqual(4, obj.caret)

	def testExpandsAndUpdatesSelection(self):
		obj = _Object()
		info = obj.makeTextInfo("caret")
		info.expand("line")
		info.updateSelection()
		self.assertEqual((0, 5), obj.selection)


if __name__ == "__main__":
	unittest.main()
