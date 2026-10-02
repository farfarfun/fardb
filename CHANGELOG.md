# Changelog

## [1.4.3]

### 修复

- JSON Storage 请求增加超时、HTTP 状态检查，并在失败时抛出包含请求方法、URL
  和资源标识的 `JSONStorageError`。
- 补齐 SQLAlchemy 公开 API 的类型标注和 ORM 正常路径测试。

### 变更

- 提交 `uv.lock`，确保依赖解析可复现。
- 项目发布名和源码包已由 `fundb` 改为 `fardb`；调用方需将
  `import fundb` 改为 `import fardb`。GitHub 仓库改名尚待仓库管理员完成。

## [1.4.0]

### 变更

- 项目更名：`fundb` → `fardb`。PyPI 上 `fundb` 与 `fundb-tau` 均已被占用/弃用，
  发布名与源码包名统一改为 `fardb`（`src/fundb` → `src/fardb`），
  `import fundb` 需改为 `import fardb`。
- 仓库地址迁移为 `farfarfun/fardb`。

## [1.3.20]

### 修复

- `insert()` / `update()` / `upsert()` 数据库写入失败时不再静默吞掉异常，改为
  抛出领域异常 `TableOperationError`（携带表名/uid 与原始异常上下文）。
- 缓存实现由 `funutil.cache.disk_cache` 迁移为组织内 `farcache.disk_cache`，
  移除对 `cachebox`/`diskcache` 的直接依赖。
- `pyproject.toml` 中 `[project.urls]` 的 `Repository`/`Releases` 修正为实际
  仓库地址 `farfarfun/fundb`。

### 变更

- `requires-python` 统一为 `>=3.10`，相关模块启用
  `from __future__ import annotations`，类型注解改为 3.10 新式写法
  （`X | Y`、`dict[...]`）。
- 公开类与方法补充中文 docstring。
- README 补充简介、安装说明、最小可运行示例及组织介绍区块。
