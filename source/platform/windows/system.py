# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.


class WindowsSystemAdapter:
	def get_os_version_string(self) -> str:
		import winVersion

		return str(winVersion.getWinVer())

	def register_application_restart(self) -> None:
		import winBindings.kernel32

		winBindings.kernel32.RegisterApplicationRestart(None, 0)

	def get_battery_status(self) -> str:
		import winBindings.kernel32
		import winKernel

		status = winBindings.kernel32.SYSTEM_POWER_STATUS()
		if not winKernel.GetSystemPowerStatus(status):
			return "Unknown power status"
		if status.BatteryFlag == 0xFF:
			return "Unknown power status"
		if status.BatteryFlag & 0x80:
			return "No system battery"
		ac_status = "Plugged in" if status.ACLineStatus & 0x1 else "Unplugged"
		return f"{status.BatteryLifePercent}% ({ac_status})"
