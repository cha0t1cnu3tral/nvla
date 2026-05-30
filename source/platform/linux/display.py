# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

class LinuxDisplayAdapter:
	def set_dpi_awareness(self) -> None:
		# Linux desktop scaling is handled by the toolkit and compositor.
		return
