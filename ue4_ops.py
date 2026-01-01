#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UE4 MCP Tools for AskQ Sidecar
This module contains all Unreal Engine 4 related tools
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict

from .. import get_ue4_websocket_manager, register_tool

logger = logging.getLogger("mcp_ue4_tools")


def get_ue4_connection(session_id: str):
    """
    获取UE4 WebSocket连接

    Args:
        session_id: UE4会话ID

    Returns:
        WebSocket连接对象或None
    """
    manager = get_ue4_websocket_manager()
    if not manager:
        raise RuntimeError(
            "UE4 WebSocket manager not initialized. Call set_ue4_websocket_manager() first."
        )

    # 获取活动的UE4连接
    active_connections = getattr(manager, "active_connections", {})
    if session_id in active_connections:
        return active_connections[session_id]

    # 如果没有指定session_id，尝试获取第一个连接
    if not session_id and active_connections:
        return next(iter(active_connections.values()))

    return None


async def _send_ue4_command(connection: Any, command: Dict[str, Any]) -> None:
    """Send a command to UE4 over the active websocket connection."""
    if hasattr(connection, "send_json"):
        await connection.send_json(command)
        return

    if hasattr(connection, "send"):
        await connection.send(json.dumps(command, ensure_ascii=False))
        return

    ws = getattr(connection, "ws", None)
    if ws is not None and hasattr(ws, "send"):
        await ws.send(json.dumps(command, ensure_ascii=False))
        return

    raise RuntimeError("UE4 connection object does not support send_json/send")


@register_tool(name="move_actor", description="移动UE4中的Actor")
async def move_actor(
    session_id: str = "",
    actor_name: str = "",
    location: Dict[str, float] = None,
    rotation: Dict[str, float] = None,
    scale: Dict[str, float] = None,
) -> str:
    """
    移动UE4中的Actor

    Args:
        session_id: UE4会话ID（如果为空，使用第一个可用连接）
        actor_name: Actor名称
        location: 位置坐标 {x: float, y: float, z: float}
        rotation: 旋转角度 {pitch: float, yaw: float, roll: float}
        scale: 缩放比例 {x: float, y: float, z: float}

    Returns:
        JSON字符串，包含操作结果
    """
    try:
        if not actor_name:
            raise ValueError("Actor name is required")

        connection = get_ue4_connection(session_id)
        if not connection:
            raise RuntimeError(f"No active UE4 connection found for session_id: {session_id}")

        request_id = f"move_actor_{int(datetime.now().timestamp() * 1000)}"

        command = {
            "action": "move_actor",
            "request_id": request_id,
            "payload": {
                "actor_name": actor_name,
                "location": location or {},
                "rotation": rotation or {},
                "scale": scale or {},
            },
        }

        await _send_ue4_command(connection, command)

        result = {
            "success": True,
            "action": "move_actor",
            "status": "command_sent",
            "request_id": request_id,
            "session_id": session_id or "default",
            "actor_name": actor_name,
            "location": location,
            "rotation": rotation,
            "scale": scale,
            "message": f"Move actor '{actor_name}' command sent to UE4",
            "timestamp": datetime.now().isoformat(),
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        error_result = {
            "success": False,
            "action": "move_actor",
            "session_id": session_id or "default",
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.now().isoformat(),
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


@register_tool(name="get_selected_actors", description="获取UE4中选中的Actors列表")
async def get_selected_actors(session_id: str = "") -> str:
    """
    获取UE4中选中的Actors列表

    Args:
        session_id: UE4会话ID（如果为空，使用第一个可用连接）

    Returns:
        JSON字符串，包含选中的Actors列表
    """
    try:
        connection = get_ue4_connection(session_id)
        if not connection:
            raise RuntimeError(f"No active UE4 connection found for session_id: {session_id}")

        request_id = f"get_selected_actors_{int(datetime.now().timestamp() * 1000)}"

        command = {"action": "get_selected_actors", "request_id": request_id, "payload": {}}

        await _send_ue4_command(connection, command)

        result = {
            "success": True,
            "action": "get_selected_actors",
            "status": "command_sent",
            "request_id": request_id,
            "session_id": session_id or "default",
            "message": "Get selected actors command sent to UE4 (await UE4 response)",
            "timestamp": datetime.now().isoformat(),
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        error_result = {
            "success": False,
            "action": "get_selected_actors",
            "session_id": session_id or "default",
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.now().isoformat(),
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


@register_tool(name="execute_ue4_command", description="执行自定义UE4命令")
async def execute_ue4_command(
    session_id: str = "", command_name: str = "", parameters: Dict[str, Any] = None
) -> str:
    """
    执行自定义UE4命令

    Args:
        session_id: UE4会话ID（如果为空，使用第一个可用连接）
        command_name: 命令名称
        parameters: 命令参数

    Returns:
        JSON字符串，包含命令执行结果
    """
    try:
        if not command_name:
            raise ValueError("Command name is required")

        connection = get_ue4_connection(session_id)
        if not connection:
            raise RuntimeError(f"No active UE4 connection found for session_id: {session_id}")

        request_id = f"execute_ue4_command_{int(datetime.now().timestamp() * 1000)}"

        command = {"action": command_name, "request_id": request_id, "payload": parameters or {}}

        await _send_ue4_command(connection, command)

        result = {
            "success": True,
            "action": "execute_ue4_command",
            "status": "command_sent",
            "request_id": request_id,
            "session_id": session_id or "default",
            "command_name": command_name,
            "parameters": parameters or {},
            "message": f"Command '{command_name}' sent to UE4",
            "timestamp": datetime.now().isoformat(),
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        error_result = {
            "success": False,
            "action": "execute_ue4_command",
            "session_id": session_id or "default",
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.now().isoformat(),
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


# ==================== ReAct Loop Tools for UE4 Communication ====================


@register_tool(name="ask_ue4_user", description="向UE4用户提问获取更多信息")
async def ask_ue4_user(question: str) -> str:
    """
    当AI需要从用户获取信息时，通过此工具向UE4客户端询问问题。
    这通常用于当AI需要更多信息来创建UAsset时，如颜色、大小、路径等参数。

    这个工具不是由服务器直接执行的，而是由sidecar_proxy.py中的ReAct Loop拦截，
    通过WebSocket将问题发送给UE4客户端，然后等待用户输入。

    Args:
        question: 要询问用户的问题

    Returns:
        占位符响应，实际结果由ReAct Loop从UE4获取后返回给AI
    """
    return json.dumps(
        {
            "success": True,
            "action": "ask_ue4_user",
            "status": "awaiting_user_input",
            "question": question,
            "message": "This tool call will be intercepted by the ReAct Loop. The sidecar will ask the user and return the answer to the AI.",
            "timestamp": datetime.now().isoformat(),
        },
        ensure_ascii=False,
        indent=2,
    )


@register_tool(name="generate_uasset_python", description="生成并执行UE4 Python脚本来创建Asset")
async def generate_uasset_python(script_content: str) -> str:
    """
    当所有参数齐备后，使用此工具将Python代码发送给UE4执行以创建Asset。
    这通常用于在UE4中执行Python脚本来创建uasset文件。

    这个工具不是由服务器直接执行的，而是由sidecar_proxy.py中的ReAct Loop拦截，
    通过WebSocket将Python脚本发送给UE4客户端执行，然后返回执行结果。

    Args:
        script_content: 要执行的Python脚本内容，用于在UE4中创建uasset

    Returns:
        占位符响应，实际结果由ReAct Loop从UE4获取后返回给AI
    """
    return json.dumps(
        {
            "success": True,
            "action": "generate_uasset_python",
            "status": "awaiting_ue4_execution",
            "script_length": len(script_content),
            "message": "This tool call will be intercepted by the ReAct Loop. The sidecar will send the script to UE4 and return the execution result to the AI.",
            "timestamp": datetime.now().isoformat(),
        },
        ensure_ascii=False,
        indent=2,
    )


# ==================== Client-Side Execution Tools ====================


@register_tool(name="read_local_code", description="读取本地代码文件以了解逻辑或API定义")
async def read_local_code(file_path: str) -> str:
    """
    读取本地代码文件以了解逻辑或API定义。
    当需要查看类或函数的实现细节时使用此工具。

    此工具不是由服务器直接执行的，而是由sidecar_proxy.py中的ReAct Loop拦截并处理，
    因为API服务器无法直接访问本地文件系统。

    Args:
        file_path: 源文件（例如.h、.cpp、.cs、.py等）的绝对或相对路径

    Returns:
        占位符响应，实际的文件内容由sidecar_proxy.py中的ReAct Loop获取后返回给AI
    """
    return json.dumps(
        {
            "success": True,
            "action": "read_local_code",
            "status": "awaiting_local_execution",
            "file_path": file_path,
            "message": "This tool call will be intercepted by the ReAct Loop. The sidecar will read the file locally and return its contents to the AI.",
            "timestamp": datetime.now().isoformat(),
        },
        ensure_ascii=False,
        indent=2,
    )


@register_tool(name="inspect_blueprint", description="检查Unreal Engine蓝图资产")
async def inspect_blueprint(asset_path: str) -> str:
    """
    检查Unreal Engine蓝图资产。
    这将检检索蓝图的文本表示（T3D）或变量列表。

    此工具不是由服务器直接执行的，而是由sidecar_proxy.py中的ReAct Loop拦截，
    通过WebSocket将请求发送给UE4客户端，获取蓝图信息后返回给AI。

    Args:
        asset_path: UE4资产路径（例如：/Game/Blueprints/BP_MyCharacter）

    Returns:
        占位符响应，实际的蓝图信息由sidecar_proxy.py通过UE4客户端获取后返回给AI
    """
    return json.dumps(
        {
            "success": True,
            "action": "inspect_blueprint",
            "status": "awaiting_ue4_execution",
            "asset_path": asset_path,
            "message": "This tool call will be intercepted by the ReAct Loop. The sidecar will request blueprint info from UE4 and return the result to the AI.",
            "timestamp": datetime.now().isoformat(),
        },
        ensure_ascii=False,
        indent=2,
    )


__all__ = [
    "get_ue4_connection",
    "move_actor",
    "get_selected_actors",
    "execute_ue4_command",
    "ask_ue4_user",
    "generate_uasset_python",
    "read_local_code",
    "inspect_blueprint",
]
