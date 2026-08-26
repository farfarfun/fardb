import traceback
from datetime import datetime
from hashlib import md5

from nltlog import getLogger
from funutil.cache import disk_cache
from sqlalchemy import String, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

logger = getLogger("fundb")


class BaseTable(DeclarativeBase):
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
        raise NotImplementedError

    def _to_dict(self) -> dict:
        raise NotImplementedError

    def _child(self):
        raise NotImplementedError

    def get_uid(self):
        return md5(self._get_uid().encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
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

    def exists(self, session: Session):
        sql = select(self._child()).where(self._child().uid == self.uid)
        return session.execute(sql).first() is not None

    def upsert(self, session: Session, update_data=False):
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
        except Exception as e:
            logger.error(f"upsert error: {e}:{traceback.format_exc()}")

    @staticmethod
    @disk_cache(cache_key="table", expire=600)
    def select_all(session: Session, table):
        return [resource for resource in session.execute(select(table)).scalars()]
