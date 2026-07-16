import importlib
import os
import sqlite3

import pytest


os.environ.setdefault("GOOGLE_API_KEY", "test-key")


@pytest.fixture
def app_module():
    module = importlib.import_module("appnew")
    return importlib.reload(module)


def test_extract_sql_from_text_removes_sql_fences(app_module):
    text = "Here is the query:\n```sql\nSELECT * FROM CUSTOMERS;\n```"
    assert app_module.extract_sql_from_text(text) == "SELECT * FROM CUSTOMERS;"


def test_query_type_helpers_detect_sql_and_dml(app_module):
    assert app_module.is_sql_query("SELECT * FROM CUSTOMERS;")
    assert app_module.is_sql_query("WITH cte AS (SELECT 1) SELECT * FROM cte;")
    assert app_module.is_dml_query("UPDATE CUSTOMERS SET ORDER_STATUS = 'done' WHERE ORDER_ID = 1;")
    assert not app_module.is_sql_query("I cannot understand that")
    assert not app_module.is_dml_query("SELECT * FROM CUSTOMERS;")


def test_clean_summary_text_removes_markdown(app_module):
    text = "### Summary\nThis is a **great** result."
    assert app_module.clean_summary_text(text) == "Summary\nThis is a great result."


def test_infer_target_table_prefers_shipments_for_shipment_requests(app_module):
    assert app_module.infer_target_table("show me shipment info") == "SHIPMENTS"
    assert app_module.infer_target_table("show line item details") == "ORDER_ITEMS"
    assert app_module.infer_target_table("show customer orders") == "CUSTOMERS"
    assert app_module.infer_target_table("show table size for customers") == "STATS"
    assert app_module.infer_target_table("show indexes on customers") == "USER_INDEXES"
    assert app_module.infer_target_table("show table metadata for shipments") == "USER_TABLES"


def test_read_sql_query_returns_rows_from_sqlite(tmp_path, app_module):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO demo (name) VALUES ('Alice')")
    conn.commit()
    conn.close()

    rows = app_module.read_sql_query("SELECT * FROM demo", str(db_path))
    assert rows == [(1, "Alice")]


def test_dml_sql_query_updates_rows(tmp_path, app_module):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO demo (name) VALUES ('Alice')")
    conn.commit()
    conn.close()

    result = app_module.DML_sql_query("UPDATE demo SET name = 'Bob' WHERE id = 1", str(db_path))
    assert result == "Operation success"

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT name FROM demo WHERE id = 1").fetchone()
    conn.close()
    assert row == ("Bob",)


def test_get_gemini_res_uses_client(monkeypatch, app_module):
    class FakeResponse:
        text = "```sql\nSELECT 42;\n```"

    class FakeModels:
        def generate_content(self, model, contents, config):
            return FakeResponse()

    class FakeClient:
        def __init__(self, api_key):
            self.models = FakeModels()

    monkeypatch.setattr(app_module, "get_client", lambda: FakeClient("test-key"))
    monkeypatch.setattr(app_module.types.Part, "from_text", staticmethod(lambda text: text))
    monkeypatch.setattr(app_module.types, "GenerateContentConfig", lambda **kwargs: kwargs)

    sql = app_module.get_gemini_res("show me the answer")
    assert sql == "SELECT 42;"
