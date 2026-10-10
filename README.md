# fardb

`fardb` 是一个轻量的数据库访问工具库，基于 SQLAlchemy 封装了常用的表 CRUD / upsert 操作，
并附带一个 [extendsclass.com JSON Storage](https://extendsclass.com/json-storage.html) 的简易客户端。

## 安装

```bash
pip install fardb
```

使用 MySQL 时，请安装对应的可选依赖，并通过环境变量提供密码：

```bash
pip install "fardb[mysql]"
export FARDB_MYSQL_PASSWORD='your-password'
```

## 快速上手

```python
from sqlalchemy import BIGINT, String
from sqlalchemy.orm import mapped_column

from fardb.sqlalchemy import Base, BaseTable, create_engine_sqlite


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

## 发布

开发环境安装依赖后，在项目根目录使用组织的 `funbuild` 完成版本递增、构建、安装校验和发布：

```bash
pip install "funbuild>=1.6.97"
funbuild build
```

`funbuild build` 会依次执行版本递增、构建、安装校验、发布、提交、推送和打标签。发布前请确认工作区干净、远程分支可拉取，并已配置发布凭据；仅需本地构建和安装校验时使用：

```bash
funbuild install
```

---

## 关于 farfarfun

[farfarfun](https://github.com/farfarfun) 是一个专注于实用工具库的开源组织，
涵盖云存储、数据处理、AI、多媒体与开发工具链等方向。

- 🏠 组织主页：<https://github.com/farfarfun>
- 📦 PyPI：<https://pypi.org/user/niuliangtao/>
- 📧 联系：farfarfun@qq.com

本项目基于 [MIT](LICENSE) 协议开源。
