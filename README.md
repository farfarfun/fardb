# fundb

`fundb` 是一个轻量的数据库访问工具库，基于 SQLAlchemy 封装了常用的表 CRUD / upsert 操作，
并附带一个 [extendsclass.com JSON Storage](https://extendsclass.com/json-storage.html) 的简易客户端。

## 安装

> ⚠️ PyPI 上的 `fundb` 这个名字已被无关第三方项目占用（[Madhava-mng/FunDB](https://github.com/Madhava-mng/FunDB)），
> **不要** `pip install fundb`，本仓库真正的发布名是 `fundb-tau`。

```bash
pip install fundb-tau
```

## 快速上手

```python
from sqlalchemy import BIGINT, String
from sqlalchemy.orm import mapped_column

from fundb.sqlalchemy import Base, BaseTable, create_engine_sqlite


class UserTable(Base):
    __tablename__ = "user"
    id = mapped_column(BIGINT, primary_key=True)
    name = mapped_column(String(64))


engine = create_engine_sqlite(":memory:")
table = BaseTable(engine, table=UserTable)

table.insert({"id": 1, "name": "alice"})
df = table.select_all()
print(df)
```

## 关于 farfarfun

[farfarfun](https://github.com/farfarfun) 是一个专注于实用工具库的开源组织，
涵盖云存储、数据处理、AI、多媒体与开发工具链等方向。

- 🏠 组织主页：<https://github.com/farfarfun>
- 📦 PyPI：<https://pypi.org/user/niuliangtao/>
- 📧 联系：farfarfun@qq.com

本项目基于 [MIT](LICENSE) 协议开源。
