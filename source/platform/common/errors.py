# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.


class NotSupportedYetError(NotImplementedError):
	"""Raised for PAL methods that are intentionally stubbed in early Linux work."""

	def __init__(self, capability: str):
		super().__init__(f"{capability} is not supported yet on Linux in this rewrite phase.")

