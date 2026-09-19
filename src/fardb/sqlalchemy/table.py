"""ORM 声明式表基类，提供 uid 生成、字典转换与 upsert 等通用能力。"""

from __future__ import annotations

from datetime import datetime
from hashlib import md5

from farcache import disk_cache
from farlog import getLogger
from sqlalchemy import String, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from fardb.sqlalchemy.base import TableOperationError

logger = getLogger("fardb")


class BaseTable(DeclarativeBase):
    """通用 ORM 表基类。

    子类需实现 `_get_uid`、`_to_dict`、`_child` 三个方法，分别提供
    唯一性来源字段、导出字典的内容、以及自身模型类（用于构造查询）。
    """

    uid: Mapped[str] = mapped_column(
        String(128), primary_key=True, comment="唯一ID", unique=True
    )

    gmt_modified: Mapped[datetime] = mapped_column(
        comment="修改时间", default=datetime.now, onupdate=datetime.now
    )

    gmt_create: Mapped[datetime] = mapped_column(
        comment="创建时间", default=datetime.now
    )

    def _get_uid(self) -> str:
        """返回用于生成 `uid` 的原始字符串，由子类实现。"""
        raise NotImplementedError

    def _to_dict(self) -> dict:
        """返回该记录导出为字典的字段内容，由子类实现。"""
        raise NotImplementedError

    def _child(self):
        """返回子类自身的模型类，用于构造查询/更新语句，由子类实现。"""
        raise NotImplementedError

    def get_uid(self) -> str:
        """基于 `_get_uid()` 的返回值计算 MD5 作为唯一 ID。"""
        return md5(self._get_uid().encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        """导出记录字典，自动补齐 `uid` 并去掉值为 `None` 的字段。"""
        res = self._to_dict()
        res.update(
            {
                "uid": self.get_uid(),
            }
        )
        for key in list(res.keys()):
            if res[key] is None:
                res.pop(key)
        return res

    def exists(self, session: Session) -> bool:
        """判断当前 `uid` 对应的记录在数据库中是否已存在。"""
        sql = select(self._child()).where(self._child().uid == self.uid)
        return session.execute(sql).first() is not None

    def upsert(self, session: Session, update_data: bool = False) -> None:
        """插入不存在的记录，或在 `update_data=True` 时更新已存在的记录。

        参数:
            session: 当前数据库会话。
            update_data: 记录已存在时是否执行更新，默认 `False`。

        异常:
            TableOperationError: 数据库写入失败时抛出，原始异常通过
                `__cause__` 保留。
        """
        try:
            if not self.exists(session):
                logger.debug(f"uid={self.uid} not exists, insert it.")
                session.execute(insert(self._child()).values(**self.to_dict()))
            elif update_data:
                logger.debug(f"uid={self.uid} exists, update it.")
                session.execute(
                    update(self._child())
                    .where(self._child().uid == self.uid)
                    .values(**self.to_dict())
                )
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"uid={self.uid} upsert failed: {e}")
            raise TableOperationError(f"uid={self.uid} upsert failed: {e}") from e

    @staticmethod
    @disk_cache(cache_key="table", expire=600)
    def select_all(session: Session, table) -> list:
        """查询表内全部记录（结果按 `table` 参数缓存 600 秒）。"""
        return [resource for resource in session.execute(select(table)).scalars()]
