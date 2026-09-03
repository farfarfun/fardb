"""Lightweight smoke tests for fundb.

These tests confirm the public API can be imported and exercised at a basic
level. Real network calls (JSONStorage) are mocked with unittest.mock.
sqlite in-memory engines are used for the sqlalchemy helpers because they
are real but fully local/ephemeral - no external DB or network is touched.
"""

import hashlib
from unittest.mock import MagicMock, patch


def test_import_fundb():
    import fundb  # noqa: F401


def test_import_fundb_json():
    from fundb.json import JSONStorage

    assert callable(JSONStorage)


def test_import_fundb_sqlalchemy():
    from fundb.sqlalchemy import (
        Base,
        BaseTable,
        create_engine,
        create_engine_mysql,
        create_engine_sqlite,
    )

    assert callable(Base)
    assert callable(BaseTable)
    assert callable(create_engine)
    assert callable(create_engine_mysql)
    assert callable(create_engine_sqlite)


def test_create_engine_sqlite_memory_real_connection():
    """sqlite in-memory is a real but fully local/ephemeral DB, safe to hit directly."""
    from sqlalchemy import text

    from fundb.sqlalchemy import create_engine_sqlite

    engine = create_engine_sqlite(":memory:")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_create_engine_caches_by_uri():
    from fundb.sqlalchemy.engine import create_engine

    e1 = create_engine("sqlite:///:memory:cache-smoke-test", cache=True)
    e2 = create_engine("sqlite:///:memory:cache-smoke-test", cache=True)
    assert e1 is e2

    e3 = create_engine("sqlite:///:memory:cache-smoke-test", cache=False)
    assert e3 is not e1


def test_create_engine_mysql_builds_expected_uri():
    """pymysql is not installed/required for this smoke suite, so mock the
    underlying sqlalchemy.create_engine call to avoid a real driver import."""
    with patch("fundb.sqlalchemy.engine.create_engine2") as mock_create:
        mock_create.return_value = MagicMock()
        from fundb.sqlalchemy import create_engine_mysql

        create_engine_mysql("myhost", "myuser", "mypass", "mydb", port=3307)

    called_uri = mock_create.call_args[0][0]
    assert called_uri == "mysql+pymysql://myuser:mypass@myhost:3307/mydb?charset=utf8"


def test_basetable_crud_with_sqlite_memory():
    """fundb.sqlalchemy.BaseTable wraps simple CRUD helpers; exercise them
    against a real local sqlite in-memory engine (no external DB involved)."""
    from sqlalchemy import BIGINT, String
    from sqlalchemy.orm import mapped_column

    from fundb.sqlalchemy import Base, BaseTable, create_engine_sqlite

    class SmokeTable(Base):
        __tablename__ = "smoke_table"
        id = mapped_column(BIGINT, primary_key=True)
        name = mapped_column(String(64))

    # ":memory:" is the one literal sqlalchemy/sqlite treats as an ephemeral
    # in-memory DB; anything else (e.g. ":memory:some-suffix") is a real file
    # on disk, so reuse the exact same literal here.
    engine = create_engine_sqlite(":memory:")
    table = BaseTable(engine, table=SmokeTable)

    table.insert({"id": 1, "name": "alice"})
    df = table.select_all()
    assert len(df) == 1
    assert df.iloc[0]["name"] == "alice"

    table.update({"id": 1, "name": "bob"})
    df = table.select_all()
    assert df.iloc[0]["name"] == "bob"

    table.delete_all()
    df = table.select_all()
    assert len(df) == 0


def test_orm_basetable_get_uid_and_to_dict(tmp_path, monkeypatch):
    """fundb.sqlalchemy.table.BaseTable is a DeclarativeBase mixin. Importing
    it eagerly initializes an on-disk cache directory (funutil.cache.disk_cache
    runs at class-definition time) as a side effect, so chdir into a tmp dir
    first to avoid leaving .disk_cache artifacts in the repo."""
    monkeypatch.chdir(tmp_path)

    from sqlalchemy import String
    from sqlalchemy.orm import Mapped, mapped_column

    from fundb.sqlalchemy.table import BaseTable as OrmBaseTable

    class SmokeOrmTable(OrmBaseTable):
        __tablename__ = "smoke_orm_table"
        name: Mapped[str] = mapped_column(String(64), default="")

        def _get_uid(self):
            return self.name

        def _to_dict(self):
            return {"name": self.name}

        def _child(self):
            return SmokeOrmTable

    row = SmokeOrmTable(name="hello")
    row.uid = row.get_uid()
    assert row.uid == hashlib.md5(b"hello").hexdigest()
    assert row.to_dict()["name"] == "hello"


def test_jsonstorage_construction():
    from fundb.json import JSONStorage

    storage = JSONStorage()
    assert storage.base_url == "https://json.extendsclass.com"


def test_jsonstorage_request_mocks_network():
    """JSONStorage.request() does a real HTTP GET; mock requests.get so this
    smoke test doesn't depend on network access."""
    from fundb.json import JSONStorage

    storage = JSONStorage()
    fake_response = MagicMock()
    fake_response.json.return_value = {"ok": True}

    with patch(
        "fundb.json.jsonextendsclass.requests.get", return_value=fake_response
    ) as mock_get:
        result = storage.request("bin123", security_key="secret")

    assert result == {"ok": True}
    mock_get.assert_called_once_with(
        "https://json.extendsclass.com/bin/bin123",
        headers={"Security-key": "secret"},
    )


def test_jsonstorage_request_without_security_key():
    """security_key 是可选参数：未提供时应发送 header 值为 None（边界路径）。"""
    from fundb.json import JSONStorage

    storage = JSONStorage()
    fake_response = MagicMock()
    fake_response.json.return_value = {"ok": True}

    with patch(
        "fundb.json.jsonextendsclass.requests.get", return_value=fake_response
    ) as mock_get:
        storage.request("bin123")

    mock_get.assert_called_once_with(
        "https://json.extendsclass.com/bin/bin123",
        headers={"Security-key": None},
    )


def test_jsonstorage_update_calls_put_with_serialized_body():
    from fundb.json import JSONStorage

    storage = JSONStorage()
    fake_response = MagicMock()
    fake_response.json.return_value = {"updated": True}

    with patch(
        "fundb.json.jsonextendsclass.requests.put", return_value=fake_response
    ) as mock_put:
        result = storage.update("bin123", {"a": 1}, security_key="secret")

    assert result == {"updated": True}
    mock_put.assert_called_once_with(
        "https://json.extendsclass.com/bin/bin123",
        headers={"Security-key": "secret"},
        data='{"a": 1}',
    )


def test_jsonstorage_delete_calls_delete():
    from fundb.json import JSONStorage

    storage = JSONStorage()
    fake_response = MagicMock()
    fake_response.json.return_value = {"deleted": True}

    with patch(
        "fundb.json.jsonextendsclass.requests.delete", return_value=fake_response
    ) as mock_delete:
        result = storage.delete("bin123", security_key="secret")

    assert result == {"deleted": True}
    mock_delete.assert_called_once_with(
        "https://json.extendsclass.com/bin/bin123",
        headers={"Security-key": "secret"},
    )


def test_jsonstorage_create_calls_post_with_expected_headers():
    from fundb.json import JSONStorage

    storage = JSONStorage()
    fake_response = MagicMock()
    fake_response.json.return_value = {"bin": "new-bin-id"}

    with patch(
        "fundb.json.jsonextendsclass.requests.post", return_value=fake_response
    ) as mock_post:
        result = storage.create(
            "api-key", {"a": 1}, security_key="secret", private="true"
        )

    assert result == {"bin": "new-bin-id"}
    mock_post.assert_called_once_with(
        "https://json.extendsclass.com/bin",
        headers={"Api-key": "api-key", "Security-key": "secret", "Private": "true"},
        data='{"a": 1}',
    )


def test_jsonstorage_all_bins_calls_get():
    from fundb.json import JSONStorage

    storage = JSONStorage()
    fake_response = MagicMock()
    fake_response.json.return_value = {"bins": []}

    with patch(
        "fundb.json.jsonextendsclass.requests.get", return_value=fake_response
    ) as mock_get:
        result = storage.all_bins("api-key")

    assert result == {"bins": []}
    mock_get.assert_called_once_with(
        "https://json.extendsclass.com/bins",
        headers={"Api-key": "api-key"},
    )


def test_jsonstorage_request_propagates_network_errors():
    """网络层异常（边界路径）应原样向调用方传播，而不是被静默吞掉。"""
    import pytest
    import requests

    from fundb.json import JSONStorage

    storage = JSONStorage()

    with (
        patch(
            "fundb.json.jsonextendsclass.requests.get",
            side_effect=requests.ConnectionError("boom"),
        ),
        pytest.raises(requests.ConnectionError),
    ):
        storage.request("bin123")


def test_basetable_insert_raises_domain_error_on_failure():
    """insert() 在数据库写入失败时应抛出 TableOperationError，而不是吞掉异常。"""
    import pytest
    from sqlalchemy import BIGINT
    from sqlalchemy.orm import mapped_column

    from fundb.sqlalchemy import Base, BaseTable, create_engine_sqlite
    from fundb.sqlalchemy.base import TableOperationError

    class FailTable(Base):
        __tablename__ = "fail_table"
        id = mapped_column(BIGINT, primary_key=True)

    engine = create_engine_sqlite(":memory:")
    table = BaseTable(engine, table=FailTable)
    # 人为制造一个真实的数据库层错误：先把刚建好的表删掉，再写入。
    FailTable.metadata.drop_all(engine)

    with pytest.raises(TableOperationError):
        table.insert({"id": 1})


def test_orm_basetable_upsert_raises_domain_error_on_failure(tmp_path, monkeypatch):
    """table.py 中 BaseTable.upsert 失败时应抛出 TableOperationError。"""
    import pytest

    monkeypatch.chdir(tmp_path)

    from sqlalchemy import String
    from sqlalchemy.orm import Mapped, Session, mapped_column

    from fundb.sqlalchemy import create_engine_sqlite
    from fundb.sqlalchemy.base import TableOperationError
    from fundb.sqlalchemy.table import BaseTable as OrmBaseTable

    class SmokeOrmTable2(OrmBaseTable):
        __tablename__ = "smoke_orm_table_2"
        name: Mapped[str] = mapped_column(String(64), default="")

        def _get_uid(self):
            return self.name

        def _to_dict(self):
            # 故意返回一个表里不存在的列，触发真实的 SQLAlchemy 报错，
            # 用来验证 upsert() 会把它包装为 TableOperationError 而不是吞掉。
            return {"name": self.name, "not_a_real_column": "x"}

        def _child(self):
            return SmokeOrmTable2

    engine = create_engine_sqlite(":memory:")
    SmokeOrmTable2.metadata.create_all(engine)

    row = SmokeOrmTable2(name="hello")
    row.uid = row.get_uid()

    with Session(engine) as session, pytest.raises(TableOperationError):
        row.upsert(session)
