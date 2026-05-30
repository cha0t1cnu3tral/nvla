# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations


isRunning = False


def initialize() -> None:
	global isRunning
	isRunning = True


def terminate() -> None:
	global isRunning
	isRunning = False


def alive() -> None:
	return


def asleep() -> None:
	return


class WatchdogObserver:
	"""Compatibility observer until Linux-specific recovery behavior is designed."""

	isAttemptingRecovery = False
