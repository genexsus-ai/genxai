"""Metrics export entrypoint."""


def get_prometheus_metrics() -> bytes:
    return b"# metrics unavailable\n"


def export_metrics() -> bytes:
    return get_prometheus_metrics()