"""Company commit-message policy plugin."""

from __future__ import annotations

import re
from typing import Any

from autoship.core.audit_logger import AuditLogger
from autoship.core.context import CommandContext
from autoship.core.fix import FixSuggestion
from autoship.exceptions import VerifyError
from autoship.hookspec import hookimpl
from commit_policy.locales import MESSAGES

_CONVENTIONAL_RE = re.compile(
    r"^(?P<type>feat|fix|docs|style|refactor|test|chore)(?:\((?P<scope>[a-z0-9_-]+)\))?: (?P<subject>.+)$"
)
_WIP_RE = re.compile(r"\b(WIP|TODO|XXX)\b", re.IGNORECASE)


class CommitPolicyPlugin:
    """Enforce company commit-message rules."""

    def __init__(self, block_wip: bool = True, locale: str = "en") -> None:
        self.block_wip = block_wip
        self.locale = locale

    def _t(self, key: str, **kwargs: Any) -> str:
        return MESSAGES.get(self.locale, MESSAGES["en"]).get(key, key).format(**kwargs)

    @hookimpl
    def pre_commit(self, context: CommandContext) -> None:
        """Validate the commit message supplied via context.extras['message']."""
        message = context.extras.get("message", "")
        if not message:
            # Let AutoShip generate a message; post-validation happens later.
            return

        audit = AuditLogger(context.config)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        audit.record("commit_policy.check", {"message": message})

        match = _CONVENTIONAL_RE.match(message)
        if not match:
            audit.record("commit_policy.rejected", {"reason": "format", "message": message})
            raise VerifyError(
                self._t("commit_policy.format", message=message),
                details={"rule": "conventional_commits"},
            )

        if self.block_wip and _WIP_RE.search(message):
            audit.record("commit_policy.rejected", {"reason": "wip", "message": message})
            raise VerifyError(
                self._t("commit_policy.wip", message=message),
                details={"rule": "block_wip"},
            )

    @hookimpl
    def on_error(self, context: CommandContext, error: Exception) -> FixSuggestion | None:
        """Suggest a rewrite when the message violates policy."""
        if not isinstance(error, VerifyError):
            return None
        details = getattr(error, "details", {}) or {}
        if details.get("rule") == "conventional_commits":
            return FixSuggestion(
                description=self._t("commit_policy.suggestion_format"),
                patch="",
            )
        if details.get("rule") == "block_wip":
            return FixSuggestion(
                description=self._t("commit_policy.suggestion_wip"),
                patch="",
            )
        return None


def register() -> CommitPolicyPlugin:
    """Entry-point factory used by AutoShip."""
    return CommitPolicyPlugin()
