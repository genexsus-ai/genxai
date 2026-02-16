"""CLI tests for approval commands."""

from click.testing import CliRunner

from cli.commands.approval import approval
from genxai_enterprise.security.audit import get_approval_service


def test_cli_submit_and_approve():
    runner = CliRunner()
    result = runner.invoke(
        approval,
        ["submit", "--action", "tool.execute", "--resource", "tool:x", "--actor", "alice"],
    )
    assert result.exit_code == 0

    approvals = get_approval_service()._requests
    request_id = next(iter(approvals.keys()))

    result = runner.invoke(approval, ["approve", request_id])
    assert result.exit_code == 0

    result = runner.invoke(approval, ["clear"])
    assert result.exit_code == 0