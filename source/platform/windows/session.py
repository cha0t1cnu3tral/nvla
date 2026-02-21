# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.


class WindowsSessionAdapter:
	def initialize(self) -> None:
		from winAPI import sessionTracking

		sessionTracking.initialize()

	def pump_all(self) -> None:
		from winAPI import sessionTracking

		sessionTracking.pumpAll()

