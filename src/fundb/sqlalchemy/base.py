"""基于 SQLAlchemy Core 的通用表操作封装。"""

from __future__ import annotations

from typing import Any

import pandas as pd
from farlog import getLogger
from sqlalchemy import BIGINT, Engine, UniqueConstraint, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase, Session, mapped_column, sessionmaker
from sqlalchemy.sql import Insert

logger = getLogger("fundb")


class TableOperationError(RuntimeError):
    """表读写操作失败时抛出的领域异常，携带表名等上下文信息。"""


@compiles(Insert, "sqlite")
def sqlite_insert_ignore(insert, compiler, **kw):
    """SQLite 方言下把 INSERT 编译为 `INSERT OR IGNORE`。"""
    return compiler.visit_insert(insert.prefix_with("OR IGNORE"), **kw)


@compiles(Insert, "mysql")
def mysql_insert_ignore(insert, compiler, **kw):
    """MySQL 方言下把 INSERT 编译为 `INSERT IGNORE`。"""
    return compiler.visit_insert(insert.prefix_with("IGNORE"), **kw)


@compiles(Insert, "postgresql")
def postgresql_insert_ignore(insert, compiler, **kw):
    """PostgreSQL 方言下为 INSERT 追加 `ON CONFLICT DO NOTHING`。"""
    statement = compiler.visit_insert(insert, **kw)
    returning_position = statement.find("RETURNING")
    if returning_position >= 0:
        return (
            statement[:returning_position]
            + "ON CONFLICT DO NOTHING "
            + statement[returning_position:]
        )
    else:
        return statement + " ON CONFLICT DO NOTHING"


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类。"""


class TmpTable(Base):
    """`BaseTable` 在未显式指定表时使用的占位表。"""

    __tablename__ = "tmp_table"
    __table_args__ = (UniqueConstraint("id"),)
    id = mapped_column(BIGINT, comment="id", default="", primary_key=True)


class BaseTable:
    """对单张表的增删改查做轻量封装。

    参数:
        engine: SQLAlchemy `Engine`。
        table: 目标 ORM 表模型，默认 `TmpTable`。
    """

    def __init__(
        self, engine: Engine, table: type = TmpTable, *args: Any, **kwargs: Any
    ):
        self.table = table
        self.table_name = self.table.__tablename__
        self.engine: Engine = engine
        self.session = sessionmaker(self.engine)
        self.create()

    def create(self) -> None:
        """按当前表模型的元数据创建表（已存在则忽略）。"""
        self.table.metadata.create_all(self.engine)

    def execute(self, stmt):
        """在一个事务中执行任意 SQL 语句并返回结果。"""
        with self.engine.begin() as conn:
            return conn.execute(stmt)

    def select_all(self) -> pd.DataFrame:
        """查询整张表，返回 `pandas.DataFrame`。"""
        with self.engine.begin() as conn:
            return pd.read_sql_table(self.table_name, conn)

    def delete_all(self):
        """清空整张表。"""
        return self.execute(delete(self.table))

    def insert(self, values: dict | list[dict]) -> None:
        """批量插入记录。

        参数:
            values: 单条记录（dict）或记录列表。

        异常:
            TableOperationError: 数据库写入失败时抛出，原始异常通过
                `__cause__` 保留。
        """
        values = self.__check_values__(values)
        with Session(self.engine) as session:
            try:
                session.bulk_insert_mappings(self.table, values)
                session.commit()
            except SQLAlchemyError as ex:
                session.rollback()
                logger.error(f"table={self.table_name} insert failed: {ex}")
                raise TableOperationError(
                    f"table={self.table_name} insert failed: {ex}"
                ) from ex

    def update(self, values: dict | list[dict]) -> None:
        """批量更新记录。

        参数:
            values: 单条记录（dict）或记录列表。

        异常:
            TableOperationError: 数据库写入失败时抛出，原始异常通过
                `__cause__` 保留。
        """
        values = self.__check_values__(values)
        with Session(self.engine) as session:
            try:
                session.bulk_update_mappings(self.table, values)
                session.commit()
            except SQLAlchemyError as ex:
                session.rollback()
                logger.error(f"table={self.table_name} update failed: {ex}")
                raise TableOperationError(
                    f"table={self.table_name} update failed: {ex}"
                ) from ex

    def upsert(self, values: dict | list[dict]) -> None:
        """先插入再更新，实现简单的 upsert 语义。

        参数:
            values: 单条记录（dict）或记录列表。
        """
        values = self.__check_values__(values)
        self.insert(values)
        self.update(values)

    @staticmethod
    def __check_values__(values: dict | list[dict]) -> list[dict]:
        if isinstance(values, dict):
            return [values]
        else:
            return values
