# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.


class WindowsAccessibilityAdapter:
	def initialize(self) -> None:
		self.initialize_legacy_console_support()
		self.initialize_uia()
		self.initialize_iaccessible()

	def pump_all(self) -> None:
		import IAccessibleHandler

		IAccessibleHandler.pumpAll()

	def terminate(self) -> None:
		self.terminate_iaccessible()
		self.terminate_uia()
		self.terminate_legacy_console_support()

	def initialize_uia(self) -> None:
		import UIAHandler

		UIAHandler.initialize()

	def terminate_uia(self) -> None:
		import UIAHandler

		UIAHandler.terminate()

	def initialize_iaccessible(self) -> None:
		import IAccessibleHandler

		IAccessibleHandler.initialize()

	def terminate_iaccessible(self) -> None:
		import IAccessibleHandler

		IAccessibleHandler.terminate()

	def initialize_legacy_console_support(self) -> None:
		import winConsoleHandler

		winConsoleHandler.initialize()

	def terminate_legacy_console_support(self) -> None:
		import winConsoleHandler

		winConsoleHandler.terminate()
