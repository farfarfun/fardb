# Changelog

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
