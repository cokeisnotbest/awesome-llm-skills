# File Operations Module for AskQ Sidecar
# This module contains all file system related tools

import os
import json
import mimetypes
import base64
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from .. import register_tool
from ..config import get_project_root, get_safe_path, validate_file_access, validate_directory_access

logger = logging.getLogger(__name__)

# 注意：get_safe_path 函数已从 config.py 导入，这里不需要重复定义


@register_tool(name="list_directory", description="列出目录内容")
async def list_directory(
    path: str = "",
    file_extensions: Optional[List[str]] = None,
) -> str:
    """
    列出目录内容

    Args:
        path: 要浏览的路径（相对路径或绝对路径），默认为空表示项目根目录
        file_extensions: 要筛选的文件扩展名列表，如：['.cpp', '.h', '.uasset', '.umap']

    Returns:
        JSON字符串，包含目录信息
    """
    try:
        safe_path = get_safe_path(path)

        # 检查路径是否存在且是一个目录
        if not safe_path.exists():
            raise FileNotFoundError(f"Path not found: {safe_path}")
        if not safe_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {safe_path}")

        # 获取相对路径
        try:
            relative_path = str(safe_path.relative_to(get_project_root()))
        except ValueError:
            relative_path = str(safe_path)

        files = []
        subdirectories = []

        for item in safe_path.iterdir():
            try:
                if item.is_dir():
                    subdirectories.append(item.name)
                else:
                    # 文件 - 检查扩展名过滤
                    if file_extensions:
                        file_ext = item.suffix.lower()
                        if not any(ext.lower() in file_ext for ext in file_extensions):
                            continue

                    # 获取文件信息
                    stat_info = item.stat()
                    mime_type, _ = mimetypes.guess_type(str(item))

                    file_info = {
                        "name": item.name,
                        "path": str(item),
                        "relative_path": str(item.relative_to(get_project_root()))
                        if get_project_root() in item.parents
                        else str(item),
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat_info.st_size if not item.is_dir() else None,
                        "modified_time": datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                        if not item.is_dir()
                        else None,
                        "mime_type": mime_type,
                        "extension": item.suffix.lower() if not item.is_dir() else None,
                        "line_count": None,
                    }
                    files.append(file_info)
            except (OSError, PermissionError) as e:
                logger.warning(f"Cannot access {item}: {e}")
                continue

        # 按名称排序
        files.sort(key=lambda x: x["name"])
        subdirectories.sort()

        result = {
            "success": True,
            "action": "list",
            "path": str(safe_path),
            "relative_path": relative_path,
            "files": files,
            "subdirectories": subdirectories,
            "total_files": len(files),
            "total_directories": len(subdirectories),
            "timestamp": datetime.now().isoformat(),
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.now().isoformat(),
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


@register_tool(name="read_file", description="读取文件内容")
async def read_file(path: str) -> str:
    """
    读取文件内容

    Args:
        path: 文件路径（相对路径或绝对路径）

    Returns:
        JSON字符串，包含文件内容和元数据
    """
    try:
        safe_path = get_safe_path(path)

        # 检查路径是否存在且是一个文件
        if not safe_path.exists():
            raise FileNotFoundError(f"File not found: {safe_path}")
        if not safe_path.is_file():
            raise ValueError(f"Path is not a file: {safe_path}")

        # 安全限制：最大10MB文件
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        file_size = safe_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            raise ValueError(
                f"File too large ({file_size} bytes). Maximum size is {MAX_FILE_SIZE} bytes."
            )

        # 获取文件信息
        stat_info = safe_path.stat()
        mime_type, encoding = mimetypes.guess_type(str(safe_path))

        # 获取相对路径
        try:
            relative_path = str(safe_path.relative_to(get_project_root()))
        except ValueError:
            relative_path = str(safe_path)

        # 判断是否是文本文件
        is_text = False
        if mime_type:
            is_text = mime_type.startswith("text/") or mime_type in [
                "application/json",
                "application/xml",
                "application/javascript",
                "application/x-python",
                "application/x-c++src",
            ]

        # 基于扩展名判断
        text_extensions = [
            ".txt",
            ".md",
            ".markdown",
            ".py",
            ".cpp",
            ".h",
            ".hpp",
            ".c",
            ".cc",
            ".java",
            ".cs",
            ".go",
            ".rs",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".html",
            ".htm",
            ".css",
            ".scss",
            ".less",
            ".xml",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",
            ".conf",
            ".php",
            ".rb",
            ".pl",
            ".pm",
            ".lua",
            ".sql",
            ".sh",
            ".bash",
            ".bat",
            ".cmd",
            ".ps1",
            ".asm",
            ".s",
            ".v",
            ".sv",
            ".vhd",
            ".vhdl",
            ".tex",
            ".rst",
            ".log",
            ".csv",
            ".tsv",
            ".proto",
            ".thrift",
            ".gradle",
            ".m",
            ".mm",
            ".swift",
            ".kt",
            ".kts",
            ".dart",
            ".elm",
            ".erl",
            ".ex",
            ".exs",
            ".fs",
            ".fsx",
            ".fsi",
            ".hs",
            ".lhs",
            ".ml",
            ".mli",
            ".nim",
            ".pas",
            ".pp",
            ".r",
            ".rmd",
            ".scala",
            ".vb",
            ".vbs",
            ".zig",
            ".uproject",
            ".uplugin",
            ".Build.cs",
            ".Target.cs",
        ]

        if safe_path.suffix.lower() in text_extensions:
            is_text = True

        # 读取文件内容
        content = ""
        line_count = 0
        content_encoding = "text"

        if is_text:
            # 读取文本文件
            try:
                with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    line_count = len(lines)
                    content = "".join(lines)
            except UnicodeDecodeError:
                # 如果UTF-8失败，尝试其他编码
                try:
                    with open(safe_path, "r", encoding="latin-1", errors="ignore") as f:
                        lines = f.readlines()
                        line_count = len(lines)
                        content = "".join(lines)
                except Exception:
                    # 如果还是失败，按二进制文件处理
                    is_text = False

        if not is_text:
            # 读取二进制文件并Base64编码
            with open(safe_path, "rb") as f:
                binary_data = f.read()
                content = base64.b64encode(binary_data).decode("utf-8")
                content_encoding = "base64"
                line_count = 0

        result = {
            "success": True,
            "action": "read",
            "path": str(safe_path),
            "relative_path": relative_path,
            "content": content,
            "encoding": content_encoding,
            "line_count": line_count,
            "size": file_size,
            "mime_type": mime_type or "application/octet-stream",
            "is_text": is_text,
            "timestamp": datetime.now().isoformat(),
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.now().isoformat(),
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


@register_tool(name="search_files", description="搜索文件")
async def search_files(
    path: str = "",
    search_term: str = "",
    file_extensions: Optional[List[str]] = None,
    recursive: bool = False,
    max_results: int = 50,
) -> str:
    """
    搜索文件

    Args:
        path: 搜索根目录路径
        search_term: 搜索关键字（文件名中包含）
        file_extensions: 文件扩展名过滤列表
        recursive: 是否递归搜索子目录
        max_results: 最大返回结果数

    Returns:
        JSON字符串，包含搜索结果
    """
    try:
        if not search_term:
            raise ValueError("Search term is required")

        safe_path = get_safe_path(path)

        # 检查路径是否存在
        if not safe_path.exists():
            raise FileNotFoundError(f"Path not found: {safe_path}")

        # 收集文件列表
        if safe_path.is_file():
            files_to_search = [safe_path]
        else:
            if recursive:
                files_to_search = list(safe_path.rglob("*.*"))
            else:
                files_to_search = list(safe_path.glob("*.*"))

        # 过滤掉目录和非普通文件
        files_to_search = [f for f in files_to_search if f.is_file()]

        # 应用扩展名过滤
        if file_extensions:
            files_to_search = [
                f
                for f in files_to_search
                if any(ext.lower() in f.suffix.lower() for ext in file_extensions)
            ]

        # 执行搜索
        matches = []
        search_term_lower = search_term.lower()

        for file_path in files_to_search:
            # 检查文件名是否匹配
            if search_term_lower in file_path.name.lower():
                stat_info = file_path.stat()
                mime_type, _ = mimetypes.guess_type(str(file_path))

                try:
                    relative_path = str(file_path.relative_to(get_project_root()))
                except ValueError:
                    relative_path = str(file_path)

                file_info = {
                    "name": file_path.name,
                    "path": str(file_path),
                    "relative_path": relative_path,
                    "type": "file",
                    "size": stat_info.st_size,
                    "modified_time": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    "mime_type": mime_type,
                    "extension": file_path.suffix.lower(),
                    "line_count": None,
                }
                matches.append(file_info)

            # 限制结果数量
            if len(matches) >= max_results:
                break

        # 按修改时间排序（最新优先）
        matches.sort(key=lambda x: x["modified_time"] or "", reverse=True)

        result = {
            "success": True,
            "action": "search",
            "search_term": search_term,
            "path": str(safe_path),
            "files": matches,
            "total_matches": len(matches),
            "max_results": max_results,
            "recursive": recursive,
            "timestamp": datetime.now().isoformat(),
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.now().isoformat(),
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


@register_tool(name="get_file_info", description="获取文件/目录详细信息")
async def get_file_info(path: str) -> str:
    """
    获取文件/目录详细信息

    Args:
        path: 文件或目录路径

    Returns:
        JSON字符串，包含文件/目录信息
    """
    try:
        safe_path = get_safe_path(path)

        # 检查路径是否存在
        if not safe_path.exists():
            raise FileNotFoundError(f"Path not found: {safe_path}")

        # 获取文件信息
        stat_info = safe_path.stat()
        mime_type, encoding = mimetypes.guess_type(str(safe_path))

        # 获取相对路径
        try:
            relative_path = str(safe_path.relative_to(get_project_root()))
        except ValueError:
            relative_path = str(safe_path)

        # 如果是文件，尝试获取行数
        line_count = None
        if safe_path.is_file():
            # 检查是否是文本文件
            is_text_file = False
            if mime_type:
                is_text_file = mime_type.startswith("text/") or mime_type in [
                    "application/json",
                    "application/xml",
                    "application/javascript",
                    "application/x-python",
                    "application/x-c++src",
                ]

            if is_text_file:
                try:
                    with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:
                        line_count = sum(1 for _ in f)
                except Exception:
                    line_count = None

        result = {
            "success": True,
            "action": "info",
            "path": str(safe_path),
            "relative_path": relative_path,
            "name": safe_path.name,
            "type": "directory" if safe_path.is_dir() else "file",
            "size": stat_info.st_size if safe_path.is_file() else None,
            "modified_time": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            "mime_type": mime_type,
            "extension": safe_path.suffix.lower() if safe_path.is_file() else None,
            "line_count": line_count,
            "timestamp": datetime.now().isoformat(),
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.now().isoformat(),
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)
