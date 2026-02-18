"""Unit tests for shared typed artifact schema."""

from genxai.core.artifacts import (
    Artifact,
    CommandOutputArtifactPayload,
    DiagnosticsArtifactPayload,
    DiffArtifactPayload,
    PlanSummaryArtifactPayload,
)


def test_diff_artifact_payload_roundtrip() -> None:
    artifact = Artifact(
        kind="diff",
        title="Updated module",
        payload=DiffArtifactPayload(
            file_path="src/module.py",
            before="print('old')\n",
            after="print('new')\n",
            patch="--- a/src/module.py\n+++ b/src/module.py\n@@ -1,1 +1,1 @@\n-print('old')\n+print('new')\n",
        ),
    )

    assert artifact.id.startswith("artifact_")
    assert artifact.payload is not None
    assert artifact.payload.type == "diff"
    assert artifact.payload.file_path == "src/module.py"


def test_command_output_artifact_payload_roundtrip() -> None:
    artifact = Artifact(
        kind="command_output",
        title="Pytest result",
        payload=CommandOutputArtifactPayload(
            command="python -m pytest -q",
            argv=["python", "-m", "pytest", "-q"],
            exit_code=0,
            stdout="2 passed",
            stderr="",
        ),
    )

    assert artifact.payload is not None
    assert artifact.payload.type == "command_output"
    assert artifact.payload.exit_code == 0


def test_plan_summary_and_diagnostics_payloads() -> None:
    plan = Artifact(
        kind="plan_summary",
        title="Execution plan",
        payload=PlanSummaryArtifactPayload(
            objective="Add tests",
            steps=["Inspect endpoints", "Add tests", "Run suite"],
            notes="Prioritize smoke tests first",
        ),
    )
    diag = Artifact(
        kind="diagnostics",
        title="Blocked command",
        payload=DiagnosticsArtifactPayload(
            level="error",
            code="policy.blocked_command",
            message="Command blocked by policy",
            details={"command": "rm -rf /"},
        ),
    )

    assert plan.payload is not None
    assert plan.payload.type == "plan_summary"
    assert plan.payload.steps[0] == "Inspect endpoints"

    assert diag.payload is not None
    assert diag.payload.type == "diagnostics"
    assert diag.payload.level == "error"
