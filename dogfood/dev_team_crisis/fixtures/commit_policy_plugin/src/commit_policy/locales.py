"""Localized messages for the commit-policy plugin."""

from __future__ import annotations

MESSAGES = {
    "en": {
        "commit_policy.format": "Commit message does not follow conventional commit format: {message}",
        "commit_policy.wip": "Commit message contains WIP/TODO/XXX: {message}",
        "commit_policy.suggestion_format": "Rewrite the message as 'type(scope): subject'.",
        "commit_policy.suggestion_wip": "Remove WIP/TODO/XXX markers before committing.",
    },
    "zh": {
        "commit_policy.format": "提交信息不符合约定式提交格式：{message}",
        "commit_policy.wip": "提交信息包含 WIP/TODO/XXX：{message}",
        "commit_policy.suggestion_format": "请按 'type(scope): subject' 格式重写提交信息。",
        "commit_policy.suggestion_wip": "提交前请移除 WIP/TODO/XXX 标记。",
    },
    "ja": {
        "commit_policy.format": "コミットメッセージが conventional commit 形式ではありません：{message}",
        "commit_policy.wip": "コミットメッセージに WIP/TODO/XXX が含まれています：{message}",
        "commit_policy.suggestion_format": "'type(scope): subject' 形式で書き直してください。",
        "commit_policy.suggestion_wip": "コミット前に WIP/TODO/XXX マーカーを削除してください。",
    },
}
