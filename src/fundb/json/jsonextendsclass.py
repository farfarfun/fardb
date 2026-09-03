"""extendsclass.com JSON Storage 服务的轻量客户端。

接口文档：https://extendsclass.com/json-storage.openapi.json
"""

from __future__ import annotations

import json
from typing import Any

import requests


class JSONStorage:
    """extendsclass.com JSON Storage 服务客户端。

    该服务提供以 `bin_id` 为标识的免费 JSON 存储桶，支持读取、更新、
    删除、创建以及列出某个 api_key 下的全部存储桶。
    """

    def __init__(self) -> None:
        """初始化客户端，固定使用官方服务地址。"""
        self.base_url = "https://json.extendsclass.com"

    def request(self, bin_id: str, security_key: str | None = None) -> Any:
        """读取指定存储桶的内容。

        参数:
            bin_id: 存储桶 ID。
            security_key: 可选的安全密钥，存储桶设置了密钥时必须提供。

        返回:
            服务端返回的 JSON 内容（已解析为 Python 对象）。
        """
        url = f"{self.base_url}/bin/{bin_id}"
        headers = {"Security-key": security_key}
        response = requests.get(url, headers=headers)
        return response.json()

    def update(self, bin_id: str, data: Any, security_key: str | None = None) -> Any:
        """覆盖更新指定存储桶的内容。

        参数:
            bin_id: 存储桶 ID。
            data: 新的内容，会被序列化为 JSON 后提交。
            security_key: 可选的安全密钥。

        返回:
            服务端返回的 JSON 内容（已解析为 Python 对象）。
        """
        url = f"{self.base_url}/bin/{bin_id}"
        headers = {"Security-key": security_key}
        response = requests.put(url, headers=headers, data=json.dumps(data))
        return response.json()

    def delete(self, bin_id: str, security_key: str | None = None) -> Any:
        """删除指定存储桶。

        参数:
            bin_id: 存储桶 ID。
            security_key: 可选的安全密钥。

        返回:
            服务端返回的 JSON 内容（已解析为 Python 对象）。
        """
        url = f"{self.base_url}/bin/{bin_id}"
        headers = {"Security-key": security_key}
        response = requests.delete(url, headers=headers)
        return response.json()

    def create(
        self,
        api_key: str,
        data: Any,
        security_key: str | None = None,
        private: str = "false",
    ) -> Any:
        """创建一个新的存储桶。

        参数:
            api_key: 账号级别的 API key，用于关联存储桶到某个账号。
            data: 存储桶的初始内容，会被序列化为 JSON 后提交。
            security_key: 可选的安全密钥，设置后读写该存储桶需携带该密钥。
            private: 是否创建为私有存储桶，取值 `"true"`/`"false"`，默认 `"false"`。

        返回:
            服务端返回的 JSON 内容（含新建存储桶的 `bin_id`）。
        """
        url = f"{self.base_url}/bin"
        headers = {
            "Api-key": api_key,
            "Security-key": security_key,
            "Private": private,
        }
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response.json()

    def all_bins(self, api_key: str) -> Any:
        """列出某个 api_key 下的全部存储桶。

        参数:
            api_key: 账号级别的 API key。

        返回:
            服务端返回的 JSON 内容（存储桶列表）。
        """
        url = f"{self.base_url}/bins"
        headers = {
            "Api-key": api_key,
        }
        response = requests.get(url, headers=headers)
        return response.json()
