# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.


class WindowsInputAdapter:
	def initialize_keyboard(self, observer) -> None:
		import keyboardHandler

		keyboardHandler.initialize(observer)

	def initialize_mouse(self) -> None:
		import mouseHandler

		mouseHandler.initialize()

	def initialize_touch(self) -> None:
		import touchHandler

		touchHandler.initialize()

	def terminate_keyboard(self) -> None:
		import keyboardHandler

		keyboardHandler.terminate()

	def terminate_mouse(self) -> None:
		import mouseHandler

		mouseHandler.terminate()

	def terminate_touch(self) -> None:
		import touchHandler

		touchHandler.terminate()

