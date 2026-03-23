"""
飞书项目 Open API 插件认证
==========================
使用 plugin_id + plugin_secret 自动获取 virtual_plugin_token，
带缓存和自动续期。
"""
import time
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

OPEN_API_BASE = "https://project.feishu.cn/open_api"

_cached_token: Optional[str] = None
_token_expire_at: float = 0

_cached_x_token: Optional[str] = None
_x_token_set_at: float = 0
X_TOKEN_TTL = 3600 * 23  # x-token 一般有效期约 24h，保守 23h


async def get_plugin_token(plugin_id: str, plugin_secret: str) -> str:
    """获取 virtual_plugin_token（type=1，开发调试用），自动缓存。"""
    global _cached_token, _token_expire_at

    if _cached_token and time.time() < _token_expire_at - 60:
        return _cached_token

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{OPEN_API_BASE}/authen/plugin_token",
            json={
                "plugin_id": plugin_id,
                "plugin_secret": plugin_secret,
                "type": 1,
            },
        )
        data = resp.json()

    err = data.get("error", {})
    if err.get("code", -1) != 0:
        raise RuntimeError(f"获取 plugin_token 失败: {err.get('msg', data)}")

    token_data = data["data"]
    _cached_token = token_data["token"]
    _token_expire_at = time.time() + token_data["expire_time"]
    logger.info(f"plugin_token 已刷新, expire_in={token_data['expire_time']}s")
    return _cached_token


async def open_api_post(path: str, body: dict, plugin_id: str, plugin_secret: str, user_key: str) -> dict:
    """调用飞书项目 Open API (POST)"""
    token = await get_plugin_token(plugin_id, plugin_secret)
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{OPEN_API_BASE}/{path}",
            json=body,
            headers={
                "Content-Type": "application/json",
                "X-PLUGIN-TOKEN": token,
                "X-USER-KEY": user_key,
            },
        )
        return resp.json()


async def open_api_get(path: str, plugin_id: str, plugin_secret: str, user_key: str) -> dict:
    """调用飞书项目 Open API (GET)"""
    token = await get_plugin_token(plugin_id, plugin_secret)
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{OPEN_API_BASE}/{path}",
            headers={
                "X-PLUGIN-TOKEN": token,
                "X-USER-KEY": user_key,
            },
        )
        return resp.json()


def set_cached_x_token(token: str) -> None:
    """缓存用户提供的 x-token"""
    global _cached_x_token, _x_token_set_at
    _cached_x_token = token
    _x_token_set_at = time.time()
    logger.info("x-token 已缓存")


def get_cached_x_token() -> Optional[str]:
    """获取缓存的 x-token，过期返回 None"""
    if _cached_x_token and (time.time() - _x_token_set_at) < X_TOKEN_TTL:
        return _cached_x_token
    return None
