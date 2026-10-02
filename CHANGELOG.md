# Changelog

## [1.4.4]

### 修复

- `JSONStorage` 的 5 个 HTTP 调用补齐 10 秒超时与 `raise_for_status()`，失败时
  抛出带请求方法、URL 与资源标识的 `JSONStorageError`。此前没有超时，服务端不
  响应时调用方会无限期挂起；且 4xx/5xx 的响应体会被当成正常结果返回。已发布的
  1.4.3 仍带此缺陷。
- 上一版 CHANGELOG 把这些改动记在 `[1.4.3]` 下，但它们是 1.4.3 发布之后才提交
  的，已发布的 1.4.3 并不包含，现更正到本版本。

### 变更

- 补齐 SQLAlchemy 公开 API 的类型标注（`ruff check --select ANN` 下 `src/` 已无
  缺失标注，仅剩 `Any` 相关的 ANN401）。
- 新增 ORM 正常路径测试（`upsert` 插入 / 已存在不覆盖 / `update_data=True` 更新、
  `select_all`）以及 `select_all` 的跨表缓存隔离测试。
- 提交 `uv.lock`，确保依赖解析可复现。
- `dev` 依赖组补上 `ruff`，使 §7 要求的 lint/format 在干净克隆中可直接执行。
- 仓库已更名为 `farfarfun/fardb`，仓库 description 与 homepage 同步指向 `fardb`。
- README 去掉改名历史说明，只描述当前状态。

## [1.4.3]

### 变更

- 仅递增版本号，代码与 1.4.2 完全相同。

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
