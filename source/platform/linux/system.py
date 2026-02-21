# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from platform.common.errors import NotSupportedYetError


class LinuxSystemAdapter:
	def get_os_version_string(self) -> str:
		raise NotSupportedYetError("System version reporting")

	def register_application_restart(self) -> None:
		raise NotSupportedYetError("Application restart registration")

	def get_battery_status(self) -> str:
		raise NotSupportedYetError("Battery status reporting")
