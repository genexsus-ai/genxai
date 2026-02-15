def get_prometheus_metrics() -> bytes:
    return b"# metrics unavailable\n"


def record_workflow_execution(*_args, **_kwargs) -> None:
    return None


def export_metrics() -> bytes:
    return get_prometheus_metrics()


def record_planning_run(duration: float, status: str = "success") -> None:
    record_workflow_execution("travel_planning", duration, status)
