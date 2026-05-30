# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

import ast
from pathlib import Path
import unittest


_WINDOWS_ONLY_BOOT_MODULES = {
	"NVDAHelper",
	"JABHandler",
	"audio",
	"audioDucking",
	"comtypes",
	"nvwave",
	"mouseHandler",
	"tones",
	"touchHandler",
}


class TestLinuxCoreBootGuards(unittest.TestCase):
	def test_windows_only_boot_imports_are_platform_guarded(self):
		corePath = Path(__file__).resolve().parents[2] / "source" / "core.py"
		tree = ast.parse(corePath.read_text(encoding="utf-8"))
		parents = {}
		for parent in ast.walk(tree):
			for child in ast.iter_child_nodes(parent):
				parents[child] = parent

		imports = []
		for node in ast.walk(tree):
			if not isinstance(node, ast.Import):
				continue
			for alias in node.names:
				if alias.name in _WINDOWS_ONLY_BOOT_MODULES:
					imports.append((node, alias.name))

		self.assertGreater(len(imports), 0)
		for node, moduleName in imports:
			with self.subTest(moduleName=moduleName, line=node.lineno):
				self.assertTrue(self._hasWindowsPlatformGuard(node, parents))

	def _hasWindowsPlatformGuard(self, node, parents):
		parent = parents.get(node)
		while parent is not None:
			if isinstance(parent, ast.If):
				condition = ast.unparse(parent.test)
				if "sys.platform.startswith('win')" in condition:
					return True
			parent = parents.get(parent)
		return False


if __name__ == "__main__":
	unittest.main()
