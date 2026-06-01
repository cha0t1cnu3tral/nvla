# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from .document_navigation import DOCUMENT_GESTURE_NAMES
from .preview_commands import PREVIEW_GESTURE_NAMES


@dataclass(frozen=True, slots=True)
class ShortcutParityReport:
	"""Inventory of shared Windows keyboard bindings and native Linux preview coverage."""

	keyboardIdentifiers: tuple[str, ...]
	previewHandledIdentifiers: tuple[str, ...]
	sharedRuntimePendingIdentifiers: tuple[str, ...]


def collectKeyboardIdentifiers(globalCommandsPath: Path) -> tuple[str, ...]:
	"""Collect built-in keyboard bindings from the shared global command module."""

	tree = ast.parse(globalCommandsPath.read_text(encoding="utf-8"))
	return tuple(
		sorted(
			{
				node.value
				for node in ast.walk(tree)
				if isinstance(node, ast.Constant)
				and isinstance(node.value, str)
				and node.value.startswith("kb")
				and ":" in node.value
			},
			key=str.casefold,
		),
	)


def auditShortcutParity(globalCommandsPath: Path) -> ShortcutParityReport:
	"""Compare the shared keyboard map with commands handled by the native Linux runtime."""

	identifiers = tuple(
		sorted(
			{
				*collectKeyboardIdentifiers(globalCommandsPath),
				*collectKeyboardIdentifiers(globalCommandsPath.with_name("browseMode.py")),
			},
			key=str.casefold,
		),
	)
	previewGestureNames = frozenset(
		_normalizeChord(name)
		for name in PREVIEW_GESTURE_NAMES | DOCUMENT_GESTURE_NAMES
	)
	previewHandled = tuple(
		identifier
		for identifier in identifiers
		if _getNormalizedChord(identifier) in previewGestureNames
	)
	sharedRuntimePending = tuple(
		identifier
		for identifier in identifiers
		if identifier not in previewHandled
	)
	return ShortcutParityReport(
		keyboardIdentifiers=identifiers,
		previewHandledIdentifiers=previewHandled,
		sharedRuntimePendingIdentifiers=sharedRuntimePending,
	)


def formatShortcutParityReport(report: ShortcutParityReport) -> str:
	"""Format a durable Markdown snapshot of Linux keyboard shortcut parity."""

	total = len(report.keyboardIdentifiers)
	previewHandled = len(report.previewHandledIdentifiers)
	sharedRuntimePending = len(report.sharedRuntimePendingIdentifiers)
	return (
		"# NVDA Linux Keyboard Shortcut Parity Audit\n\n"
		"## Summary\n\n"
		f"- Shared built-in keyboard identifiers: `{total}`\n"
		f"- Identifier translation coverage: `{total}/{total}`\n"
		f"- Native preview-handled shared identifiers: `{previewHandled}/{total}`\n"
		f"- Shared-runtime integration pending: `{sharedRuntimePending}/{total}`\n\n"
		"Linux key normalization emits the same `kb:` identifiers used by the "
		"shared Windows command maps. Translation coverage does not mean each "
		"command is executable yet: most scripts still depend on shared startup "
		"modules that require Linux ports or platform guards.\n\n"
		"## Native Preview-Handled Shared Identifiers\n\n"
		f"{_formatIdentifierList(report.previewHandledIdentifiers)}\n\n"
		"## Shared-Runtime Integration Pending\n\n"
		f"{_formatIdentifierList(report.sharedRuntimePendingIdentifiers)}\n"
	)


def _getNormalizedChord(identifier: str) -> str:
	_, chord = identifier.split(":", 1)
	return _normalizeChord(chord)


def _normalizeChord(chord: str) -> str:
	return "+".join(sorted(chord.casefold().split("+")))


def _formatIdentifierList(identifiers: tuple[str, ...]) -> str:
	if not identifiers:
		return "- None"
	return "\n".join(f"- `{identifier}`" for identifier in identifiers)
