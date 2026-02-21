# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from .atspi_backend import ATSPI2Backend


class LinuxAccessibilityAdapter:
	def __init__(self) -> None:
		self._backend = ATSPI2Backend()
		self._initialized = False

	def initialize(self) -> None:
		self.initialize_iaccessible()

	def pump_all(self) -> None:
		self._backend.pump_all()

	def terminate(self) -> None:
		self.terminate_iaccessible()

	def initialize_uia(self) -> None:
		# Linux accessibility does not use UIA.
		return

	def terminate_uia(self) -> None:
		return

	def initialize_iaccessible(self) -> None:
		if self._initialized:
			return
		self._backend.initialize()
		self._initialized = True

	def terminate_iaccessible(self) -> None:
		if not self._initialized:
			return
		self._backend.terminate()
		self._initialized = False

	def initialize_legacy_console_support(self) -> None:
		# Linux accessibility does not use the Windows console backend.
		return

	def terminate_legacy_console_support(self) -> None:
		return
