# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.


class WindowsDisplayAdapter:
	def set_dpi_awareness(self) -> None:
		from winAPI.dpiAwareness import setDPIAwareness

		setDPIAwareness()

