"""Tests for system prompt assembly and integrity."""
from config.prompt import (
    SYSTEM_PROMPT,
    _ROLE,
    _PERSONA,
    _TONE,
    _CONSTRAINTS,
    _LOCAL,
    _CONTEXT,
    _TOOLS,
    _REMINDERS,
)


class TestSystemPrompt:
    def test_all_sections_non_empty(self):
        for name, section in [
            ("_ROLE", _ROLE),
            ("_PERSONA", _PERSONA),
            ("_TONE", _TONE),
            ("_CONSTRAINTS", _CONSTRAINTS),
            ("_LOCAL", _LOCAL),
            ("_CONTEXT", _CONTEXT),
            ("_TOOLS", _TOOLS),
            ("_REMINDERS", _REMINDERS),
        ]:
            assert len(section.strip()) > 0, f"{name} is empty"

    def test_system_prompt_contains_all_sections(self):
        for section in [_ROLE, _PERSONA, _TONE, _CONSTRAINTS, _LOCAL, _CONTEXT, _TOOLS, _REMINDERS]:
            assert section in SYSTEM_PROMPT

    def test_system_prompt_not_empty(self):
        assert len(SYSTEM_PROMPT) > 500

    def test_role_mentions_safia(self):
        assert "SAFIA" in _ROLE

    def test_role_mentions_language_rule(self):
        assert "LANGUAGE" in _ROLE
        assert "reply in the same language" in _ROLE.lower()

    def test_persona_mentions_woman(self):
        assert "young woman" in _PERSONA.lower()

    def test_persona_mentions_emoji(self):
        assert "emoji" in _PERSONA.lower()

    def test_tone_mentions_telegram_format(self):
        assert "Telegram" in _TONE

    def test_tone_mentions_tool_bridging(self):
        assert "Tool result bridging" in _TONE

    def test_context_mentions_proactive(self):
        assert "PROACTIVE" in _CONTEXT

    def test_context_mentions_snapshot(self):
        assert "snapshot" in _CONTEXT.lower()

    def test_tools_mentions_synchronization(self):
        assert "Synchronization is critical" in _TOOLS

    def test_tools_mentions_asset_record(self):
        assert "asset_record" in _TOOLS

    def test_reminders_mentions_reminder_create(self):
        assert "reminder_create" in _REMINDERS

    def test_reminders_mentions_max_10(self):
        assert "max 10" in _REMINDERS.lower() or "maksimal 10" in _REMINDERS.lower()

    def test_local_mentions_rp_format(self):
        assert "Rp 1.500.000" in _LOCAL

    def test_local_mentions_expense_categories(self):
        assert "Makanan" in _LOCAL
        assert "Transportasi" in _LOCAL
