# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

import os


class LinuxSystemAdapter:
	def get_os_version_string(self) -> str:
		try:
			return " ".join(os.uname())
		except AttributeError:
			return "Linux"

	def register_application_restart(self) -> None:
		return

	def get_battery_status(self) -> str:
		return "Unknown power status"
