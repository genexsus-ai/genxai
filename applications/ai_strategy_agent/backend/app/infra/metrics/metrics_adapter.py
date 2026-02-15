"""Metrics adapter."""


def record_workflow_execution(*_args, **_kwargs) -> None:
    return None

from app.application.services.brainstorm_service import MetricsRecorder


class MetricsRecorderAdapter(MetricsRecorder):
    """Adapter for app metrics recording."""

    def record(self, workflow_name: str, duration: float, status: str) -> None:
        record_workflow_execution(workflow_name, duration, status)