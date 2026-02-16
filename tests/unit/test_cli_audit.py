"""CLI tests for audit commands."""

import json

from click.testing import CliRunner

from cli.commands.audit import audit
from genxai_enterprise.security.audit import get_audit_log, AuditEvent


def test_cli_audit_list_export_clear(tmp_path):
    log = get_audit_log()
    log.record(
        AuditEvent(
            action="tool.execute",
            actor_id="alice",
            resource_id="tool:x",
            status="success",
        )
    )

    runner = CliRunner()
    result = runner.invoke(audit, ["list", "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload[0]["action"] == "tool.execute"

    result = runner.invoke(audit, ["list", "--format", "csv"])
    assert result.exit_code == 0

    export_path = tmp_path / "audit.json"
    result = runner.invoke(audit, ["export", "--output", str(export_path)])
    assert result.exit_code == 0
    assert export_path.exists()

    csv_path = tmp_path / "audit.csv"
    result = runner.invoke(
        audit,
        ["export", "--output", str(csv_path), "--format", "csv"],
    )
    assert result.exit_code == 0
    assert csv_path.exists()

    result = runner.invoke(audit, ["clear"])
    assert result.exit_code == 0

    result = runner.invoke(audit, ["compact"])
    assert result.exit_code == 0