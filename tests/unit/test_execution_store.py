"""Unit tests for the execution metadata store."""

from genxai.core.execution import ExecutionStore


def test_execution_store_create_update():
    store = ExecutionStore()
    run_id = store.generate_run_id()
    record = store.create(run_id, workflow="wf", status="running")

    assert record.run_id == run_id
    assert record.status == "running"

    store.update(run_id, status="success", result={"ok": True}, completed=True)
    updated = store.get(run_id)

    assert updated is not None
    assert updated.status == "success"
    assert updated.result == {"ok": True}


def test_execution_store_sqlite_persistence(tmp_path):
    db_path = tmp_path / "exec.db"
    store = ExecutionStore(sql_url=f"sqlite:///{db_path}")
    run_id = store.generate_run_id()
    store.create(run_id, workflow="wf", status="running")
    store.update(run_id, status="success", result={"ok": True}, completed=True)

    fetched = store.get(run_id)
    assert fetched is not None
    assert fetched.status == "success"
    assert fetched.result == {"ok": True}