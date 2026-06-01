# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

import os
from pathlib import Path


class LinuxSystemAdapter:
	def __init__(self, powerSupplyPath: Path = Path("/sys/class/power_supply")) -> None:
		self._powerSupplyPath = powerSupplyPath

	def get_os_version_string(self) -> str:
		try:
			return " ".join(os.uname())
		except AttributeError:
			return "Linux"

	def register_application_restart(self) -> None:
		return

	def get_battery_status(self) -> str:
		battery = next(self._iterBatteries(), None)
		if battery is None:
			return "No system battery"
		parts = []
		if (capacity := self._readInt(battery / "capacity")) is not None:
			parts.append(f"{capacity} percent")
		status = self._readText(battery / "status").lower()
		if status in ("charging", "full", "not charging"):
			parts.append("plugged in")
		elif status == "discharging":
			parts.append("not plugged in")
			if (remainingMinutes := self._getRemainingMinutes(battery)) is not None:
				parts.append(self._formatRemainingTime(remainingMinutes))
		return ", ".join(parts) or "Unknown power status"

	def _iterBatteries(self):
		try:
			powerSupplies = tuple(self._powerSupplyPath.iterdir())
		except OSError:
			return
		for powerSupply in powerSupplies:
			if self._readText(powerSupply / "type").lower() == "battery":
				yield powerSupply

	def _getRemainingMinutes(self, battery: Path) -> int | None:
		for availableName, rateName in (("energy_now", "power_now"), ("charge_now", "current_now")):
			available = self._readInt(battery / availableName)
			rate = self._readInt(battery / rateName)
			if available is not None and rate:
				return max(1, round(available / rate * 60))
		return None

	@staticmethod
	def _formatRemainingTime(minutes: int) -> str:
		hours, minutes = divmod(minutes, 60)
		if hours and minutes:
			return f"{hours} hours and {minutes} minutes remaining"
		if hours:
			return f"{hours} hours remaining"
		return f"{minutes} minutes remaining"

	@staticmethod
	def _readText(path: Path) -> str:
		try:
			return path.read_text(encoding="utf-8").strip()
		except OSError:
			return ""

	@classmethod
	def _readInt(cls, path: Path) -> int | None:
		try:
			return int(cls._readText(path))
		except ValueError:
			return None
