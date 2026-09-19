"""SQLAlchemy engine 创建与复用的轻量封装。"""

from __future__ import annotations

from sqlalchemy import Engine
from sqlalchemy import create_engine as create_engine2

engine_map: dict[str, Engine] = {}


def create_engine(uri: str, cache: bool = True, *args, **kwargs) -> Engine:
    """创建（或复用）一个 SQLAlchemy `Engine`。

    参数:
        uri: 数据库连接串。
        cache: 是否按 `uri` 复用已创建的 engine，默认 `True`。

    返回:
        对应 `uri` 的 `Engine` 实例。
    """
    global engine_map
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
    host: str, user: str, password: str, db_name: str = "", port: int = 3306
) -> Engine:
    """创建 MySQL（pymysql 驱动）engine。

    参数:
        host: 数据库主机地址。
        user: 用户名。
        password: 密码。
        db_name: 数据库名，默认为空。
        port: 端口号，默认 3306。

    返回:
        对应的 `Engine` 实例。
    """
    return create_engine(
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}?charset=utf8"
    )
