"""fardb 的轻量冒烟测试。

这些测试确认公开 API 可以导入并完成基本调用。真实网络调用（JSONStorage）通过
unittest.mock 模拟；SQLAlchemy 辅助函数使用本地临时 SQLite 内存数据库，不访问
外部数据库或网络。
"""

import hashlib
from unittest.mock import MagicMock, patch


def test_import_fardb():
    import fardb  # noqa: F401


def test_import_fardb_json():
    from fardb.json import JSONStorage

    assert callable(JSONStorage)


def test_import_fardb_sqlalchemy():
    from fardb.sqlalchemy import (
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
    """SQLite 内存数据库是真实但完全本地、临时的数据库，可直接访问。"""
    from sqlalchemy import text

    from fardb.sqlalchemy import create_engine_sqlite

    engine = create_engine_sqlite(":memory:")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_create_engine_caches_by_uri():
    from fardb.sqlalchemy.engine import create_engine

    e1 = create_engine("sqlite:///:memory:cache-smoke-test", cache=True)
    e2 = create_engine("sqlite:///:memory:cache-smoke-test", cache=True)
    assert e1 is e2

    e3 = create_engine("sqlite:///:memory:cache-smoke-test", cache=False)
    assert e3 is not e1


def test_create_engine_mysql_builds_expected_url(monkeypatch):
    """模拟底层创建调用，验证 MySQL 配置而不导入驱动或连接真实数据库。"""
    monkeypatch.setenv("FARDB_MYSQL_PASSWORD", "mypass")
    with patch("fardb.sqlalchemy.engine.create_engine2") as mock_create:
        mock_create.return_value = MagicMock()
        from fardb.sqlalchemy import create_engine_mysql

        create_engine_mysql("myhost", "myuser", "mydb", port=3307)

    called_url = mock_create.call_args[0][0]
    assert called_url.drivername == "mysql+pymysql"
    assert called_url.username == "myuser"
    assert called_url.password == "mypass"
    assert called_url.host == "myhost"
    assert called_url.port == 3307
    assert called_url.database == "mydb"
    assert called_url.query == {"charset": "utf8"}
    assert "mypass" not in str(called_url)


def test_create_engine_mysql_requires_password_environment_variable(monkeypatch):
    """未配置密码环境变量时，MySQL 入口应清楚地拒绝创建连接。"""
    import pytest

    from fardb.sqlalchemy import create_engine_mysql

    monkeypatch.delenv("FARDB_MYSQL_PASSWORD", raising=False)
    with pytest.raises(ValueError, match="FARDB_MYSQL_PASSWORD"):
        create_engine_mysql("myhost", "myuser")


def test_basetable_crud_with_sqlite_memory():
    """在真实本地 SQLite 内存数据库上测试 BaseTable 的基本 CRUD 辅助函数。"""
    from sqlalchemy import BIGINT, String
    from sqlalchemy.orm import mapped_column

    from fardb.sqlalchemy import Base, BaseTable, create_engine_sqlite

    class SmokeTable(Base):
        __tablename__ = "smoke_table"
        id = mapped_column(BIGINT, primary_key=True)
        name = mapped_column(String(64))

    # SQLAlchemy/SQLite 仅将精确的 ":memory:" 识别为临时内存数据库；带后缀的值
    # 会变成磁盘文件，因此这里复用完全相同的字面量。
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
    """BaseTable 导入时会初始化磁盘缓存目录，测试先切换到临时目录避免留下文件。"""
    monkeypatch.chdir(tmp_path)

    from sqlalchemy import String
    from sqlalchemy.orm import Mapped, mapped_column

    from fardb.sqlalchemy.table import BaseTable as OrmBaseTable

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
    from fardb.json import JSONStorage

    storage = JSONStorage()
    assert storage.base_url == "https://json.extendsclass.com"


def test_jsonstorage_request_mocks_network():
    """JSONStorage.request() 会执行 HTTP GET，模拟请求以避免依赖网络。"""
    from fardb.json import JSONStorage

    storage = JSONStorage()
    fake_response = MagicMock()
    fake_response.json.return_value = {"ok": True}

    with patch(
        "fardb.json.jsonextendsclass.requests.get", return_value=fake_response
    ) as mock_get:
        result = storage.request("bin123", security_key="secret")

    assert result == {"ok": True}
    mock_get.assert_called_once_with(
        "https://json.extendsclass.com/bin/bin123",
        headers={"Security-key": "secret"},
        timeout=10.0,
    )
    fake_response.raise_for_status.assert_called_once_with()


def test_jsonstorage_request_without_security_key():
    """security_key 是可选参数：未提供时应发送 header 值为 None（边界路径）。"""
    from fardb.json import JSONStorage

    storage = JSONStorage()
    fake_response = MagicMock()
    fake_response.json.return_value = {"ok": True}

    with patch(
        "fardb.json.jsonextendsclass.requests.get", return_value=fake_response
    ) as mock_get:
        storage.request("bin123")

    mock_get.assert_called_once_with(
        "https://json.extendsclass.com/bin/bin123",
        headers={"Security-key": None},
        timeout=10.0,
    )


def test_jsonstorage_update_calls_put_with_serialized_body():
    from fardb.json import JSONStorage

    storage = JSONStorage()
    fake_response = MagicMock()
    fake_response.json.return_value = {"updated": True}

    with patch(
        "fardb.json.jsonextendsclass.requests.put", return_value=fake_response
    ) as mock_put:
        result = storage.update("bin123", {"a": 1}, security_key="secret")

    assert result == {"updated": True}
    mock_put.assert_called_once_with(
        "https://json.extendsclass.com/bin/bin123",
        headers={"Security-key": "secret"},
        data='{"a": 1}',
        timeout=10.0,
    )


def test_jsonstorage_delete_calls_delete():
    from fardb.json import JSONStorage

    storage = JSONStorage()
    fake_response = MagicMock()
    fake_response.json.return_value = {"deleted": True}

    with patch(
        "fardb.json.jsonextendsclass.requests.delete", return_value=fake_response
    ) as mock_delete:
        result = storage.delete("bin123", security_key="secret")

    assert result == {"deleted": True}
    mock_delete.assert_called_once_with(
        "https://json.extendsclass.com/bin/bin123",
        headers={"Security-key": "secret"},
        timeout=10.0,
    )


def test_jsonstorage_create_calls_post_with_expected_headers():
    from fardb.json import JSONStorage

    storage = JSONStorage()
    fake_response = MagicMock()
    fake_response.json.return_value = {"bin": "new-bin-id"}

    with patch(
        "fardb.json.jsonextendsclass.requests.post", return_value=fake_response
    ) as mock_post:
        result = storage.create(
            "api-key", {"a": 1}, security_key="secret", private="true"
        )

    assert result == {"bin": "new-bin-id"}
    mock_post.assert_called_once_with(
        "https://json.extendsclass.com/bin",
        headers={"Api-key": "api-key", "Security-key": "secret", "Private": "true"},
        data='{"a": 1}',
        timeout=10.0,
    )


def test_jsonstorage_all_bins_calls_get():
    from fardb.json import JSONStorage

    storage = JSONStorage()
    fake_response = MagicMock()
    fake_response.json.return_value = {"bins": []}

    with patch(
        "fardb.json.jsonextendsclass.requests.get", return_value=fake_response
    ) as mock_get:
        result = storage.all_bins("api-key")

    assert result == {"bins": []}
    mock_get.assert_called_once_with(
        "https://json.extendsclass.com/bins",
        headers={"Api-key": "api-key"},
        timeout=10.0,
    )


def test_jsonstorage_request_wraps_network_errors_with_context():
    """网络层异常应包装为带请求上下文的领域异常。"""
    import pytest
    import requests

    from fardb.json import JSONStorage, JSONStorageError

    storage = JSONStorage()

    with (
        patch(
            "fardb.json.jsonextendsclass.requests.get",
            side_effect=requests.ConnectionError("boom"),
        ),
        pytest.raises(JSONStorageError) as exc_info,
    ):
        storage.request("bin123")

    assert "GET" in str(exc_info.value)
    assert "bin_id=bin123" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, requests.ConnectionError)


def test_jsonstorage_request_wraps_http_errors_without_secret():
    import pytest
    import requests

    from fardb.json import JSONStorage, JSONStorageError

    storage = JSONStorage()
    fake_response = MagicMock()
    fake_response.raise_for_status.side_effect = requests.HTTPError("403 forbidden")

    with (
        patch("fardb.json.jsonextendsclass.requests.get", return_value=fake_response),
        pytest.raises(JSONStorageError) as exc_info,
    ):
        storage.request("bin123", security_key="do-not-log-this")

    assert "https://json.extendsclass.com/bin/bin123" in str(exc_info.value)
    assert "do-not-log-this" not in str(exc_info.value)


def test_basetable_insert_raises_domain_error_on_failure():
    """insert() 在数据库写入失败时应抛出 TableOperationError，而不是吞掉异常。"""
    import pytest
    from sqlalchemy import BIGINT
    from sqlalchemy.orm import mapped_column

    from fardb.sqlalchemy import Base, BaseTable, create_engine_sqlite
    from fardb.sqlalchemy.base import TableOperationError

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

    from fardb.sqlalchemy import create_engine_sqlite
    from fardb.sqlalchemy.base import TableOperationError
    from fardb.sqlalchemy.table import BaseTable as OrmBaseTable

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


def test_orm_basetable_upsert_and_select_all_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    from sqlalchemy import String
    from sqlalchemy.orm import Mapped, Session, mapped_column

    from fardb.sqlalchemy import create_engine_sqlite
    from fardb.sqlalchemy.table import BaseTable as OrmBaseTable

    class UpsertTable(OrmBaseTable):
        __tablename__ = "upsert_table"
        source: Mapped[str] = mapped_column(String(64), default="")
        name: Mapped[str] = mapped_column(String(64), default="")

        def _get_uid(self) -> str:
            return self.source

        def _to_dict(self) -> dict:
            return {"source": self.source, "name": self.name}

        def _child(self) -> type["UpsertTable"]:
            return UpsertTable

    # ORM 模型通常定义在模块级；为测试模型提供相同的稳定身份，以便缓存序列化结果。
    UpsertTable.__qualname__ = "UpsertTable"
    globals()["UpsertTable"] = UpsertTable

    engine = create_engine_sqlite(":memory:")
    UpsertTable.metadata.create_all(engine)

    row = UpsertTable(source="same", name="before")
    row.uid = row.get_uid()
    with Session(engine) as session:
        row.upsert(session)
        session.commit()
        assert [
            item.name for item in OrmBaseTable.select_all(session, UpsertTable)
        ] == ["before"]

        unchanged = UpsertTable(source="same", name="ignored")
        unchanged.uid = row.uid
        unchanged.upsert(session)
        session.commit()
        assert session.get(UpsertTable, row.uid).name == "before"

        changed = UpsertTable(source="same", name="after")
        changed.uid = row.uid
        changed.upsert(session, update_data=True)
        session.commit()
        session.expire_all()
        assert session.get(UpsertTable, row.uid).name == "after"

    OrmBaseTable.select_all.cache_clear()
    OrmBaseTable.select_all.cache_close()
    globals().pop("UpsertTable", None)


def test_select_all_cache_is_isolated_per_table(tmp_path, monkeypatch):
    """`select_all` 的缓存键必须包含 table，不同表之间不能串用缓存结果。

    `disk_cache(cache_key="table")` 里的 `"table"` 是被纳入缓存键的**参数名**
    （farcache 的 `cache_key` 语义），不是一个固定的字面量键；本用例把这一点钉住，
    防止后续改成真正的固定键而让两张表互相读到对方的结果。
    """
    monkeypatch.chdir(tmp_path)

    from sqlalchemy import String
    from sqlalchemy.orm import Mapped, Session, mapped_column

    from fardb.sqlalchemy import create_engine_sqlite
    from fardb.sqlalchemy.table import BaseTable as OrmBaseTable

    class CacheLeftTable(OrmBaseTable):
        __tablename__ = "cache_left_table"
        name: Mapped[str] = mapped_column(String(64), default="")

        def _get_uid(self) -> str:
            return self.name

        def _to_dict(self) -> dict:
            return {"name": self.name}

        def _child(self) -> type["CacheLeftTable"]:
            return CacheLeftTable

    class CacheRightTable(OrmBaseTable):
        __tablename__ = "cache_right_table"
        name: Mapped[str] = mapped_column(String(64), default="")

        def _get_uid(self) -> str:
            return self.name

        def _to_dict(self) -> dict:
            return {"name": self.name}

        def _child(self) -> type["CacheRightTable"]:
            return CacheRightTable

    # 缓存结果会被 pickle，模型类需要能按限定名找回；模块级模型天然满足。
    for model in (CacheLeftTable, CacheRightTable):
        model.__qualname__ = model.__name__
        globals()[model.__name__] = model

    engine = create_engine_sqlite(":memory:")
    CacheLeftTable.metadata.create_all(engine)

    try:
        with Session(engine) as session:
            assert OrmBaseTable.select_all.cache_key(
                session, CacheLeftTable
            ) != OrmBaseTable.select_all.cache_key(session, CacheRightTable)

            left = CacheLeftTable(name="left-row")
            left.uid = left.get_uid()
            left.upsert(session)
            right = CacheRightTable(name="right-row")
            right.uid = right.get_uid()
            right.upsert(session)
            session.commit()

            # 先查左表填充缓存，再查右表：右表不能命中左表的缓存。
            assert [
                item.name for item in OrmBaseTable.select_all(session, CacheLeftTable)
            ] == ["left-row"]
            assert [
                item.name for item in OrmBaseTable.select_all(session, CacheRightTable)
            ] == ["right-row"]
            # 回头再查左表，命中缓存后结果仍然是左表自己的数据。
            assert [
                item.name for item in OrmBaseTable.select_all(session, CacheLeftTable)
            ] == ["left-row"]
    finally:
        OrmBaseTable.select_all.cache_clear()
        OrmBaseTable.select_all.cache_close()
        for model in (CacheLeftTable, CacheRightTable):
            globals().pop(model.__name__, None)
