"""SQLAlchemy engine 创建与复用的轻量封装。"""

from __future__ import annotations

import os
from typing import Any

from sqlalchemy import Engine
from sqlalchemy import create_engine as create_engine2
from sqlalchemy.engine import URL

engine_map: dict[str | URL, Engine] = {}


def create_engine(
    uri: str | URL, cache: bool = True, *args: Any, **kwargs: Any
) -> Engine:
    """创建（或复用）一个 SQLAlchemy `Engine`。

    参数:
        uri: 数据库连接串。
        cache: 是否按 `uri` 复用已创建的 engine，默认 `True`。

    返回:
        对应 `uri` 的 `Engine` 实例。
    """
    if cache:
        if uri not in engine_map:
            engine_map[uri] = create_engine2(uri)
        return engine_map[uri]
    return create_engine2(uri)


def create_engine_sqlite(db_path: str) -> Engine:
    """创建 SQLite engine。

    参数:
        db_path: SQLite 数据库文件路径，`:memory:` 表示内存数据库。

    返回:
        对应的 `Engine` 实例。
    """
    return create_engine(f"sqlite:///{db_path}")


def create_engine_mysql(
    host: str, user: str, db_name: str = "", port: int = 3306
) -> Engine:
    """创建 MySQL（pymysql 驱动）engine。

    参数:
        host: 数据库主机地址。
        user: 用户名。
        db_name: 数据库名，默认为空。
        port: 端口号，默认 3306。

    密码从环境变量 `FARDB_MYSQL_PASSWORD` 读取。

    返回:
        对应的 `Engine` 实例。
    """
    password = os.environ.get("FARDB_MYSQL_PASSWORD")
    if password is None:
        raise ValueError("未设置 MySQL 密码环境变量 FARDB_MYSQL_PASSWORD")

    return create_engine(
        URL.create(
            "mysql+pymysql",
            username=user,
            password=password,
            host=host,
            port=port,
            database=db_name,
            query={"charset": "utf8"},
        )
    )
