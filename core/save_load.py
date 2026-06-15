# -*- coding: utf-8 -*-
"""
core/save_load.py - 存档与读档模块

提供基于 JSON 格式的本地文件存档/读档功能，支持：
- 复杂数据结构的序列化与反序列化
- 原子性写入（防止写入过程中断导致文件损坏）
- 数据完整性验证（checksum + schema 校验）
- 完善的错误处理（文件权限、解析错误、文件不存在等）
- 自定义文件路径和文件名

公共 API:
    saveData(filePath, data, pretty_print=True) -> SaveResult
    loadData(filePath, validator=None) -> LoadResult
    get_save_file_info(filePath) -> SaveFileInfo
    list_save_files(directory, extension='.sav.json') -> List[str]
"""

import os
import sys
import json
import hashlib
import tempfile
import shutil
import time
import uuid
import types
from typing import Any, Optional, Dict, List, Union, Callable
from dataclasses import dataclass, field, asdict


SAVE_FORMAT_VERSION = "1.0"
DEFAULT_CHECKSUM_ALGORITHM = "sha256"

_CHECKSUM_DUMP_KWARGS: Dict[str, Any] = {
    "ensure_ascii": False,
    "sort_keys": True,
    "separators": (",", ":"),
    "cls": None,
}


def _preprocess_for_json(obj: Any) -> Any:
    """
    递归预处理对象，把 json 模块默认不会调用 encoder 的内置类型（tuple）
    以及其他特殊类型转换为带 __type__ 标记的 dict，以便后续正确序列化。

    注意：set/frozenset/bytes/complex/uuid/datetime 等会在 _JSONEncoder.default
    中处理，因为它们本就不是 json 原生支持的，会触发 default 调用。
    只有 tuple 是 json 原生支持（被当作 list 处理），所以需要在此预处理。
    """
    if isinstance(obj, tuple):
        return {"__type__": "tuple", "data": [_preprocess_for_json(x) for x in obj]}
    if isinstance(obj, dict):
        return {k: _preprocess_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_preprocess_for_json(x) for x in obj]
    return obj


def _canonical_data_bytes(data: Any, encoding: str = "utf-8") -> bytes:
    """
    将 data 转换为用于校验和计算的规范化 JSON bytes。
    保存和加载时都必须使用相同的规范化参数，保证 checksum 一致。
    """
    return json.dumps(data, **_CHECKSUM_DUMP_KWARGS).encode(encoding)


class SaveLoadError(Exception):
    """存档/读档操作的基类异常。"""
    pass


class FileNotFoundError(SaveLoadError):
    """目标存档文件不存在。"""
    pass


class FilePermissionError(SaveLoadError):
    """文件权限不足，无法读取或写入。"""
    pass


class InvalidFormatError(SaveLoadError):
    """存档文件格式错误或损坏。"""
    pass


class ChecksumMismatchError(SaveLoadError):
    """存档文件校验和不匹配，数据可能已损坏。"""
    pass


class VersionMismatchError(SaveLoadError):
    """存档格式版本不兼容。"""
    pass


class DataValidationError(SaveLoadError):
    """用户自定义数据验证失败。"""
    pass


class SerializationError(SaveLoadError):
    """数据序列化（转换为 JSON）失败。"""
    pass


@dataclass
class SaveResult:
    """saveData 的返回结果。"""
    success: bool
    file_path: str
    file_size: int = 0
    checksum: str = ""
    error: Optional[SaveLoadError] = None
    elapsed_ms: float = 0.0

    def __bool__(self) -> bool:
        return self.success


@dataclass
class LoadResult:
    """loadData 的返回结果。"""
    success: bool
    data: Any = None
    file_path: str = ""
    metadata: Optional[Dict[str, Any]] = None
    checksum_verified: bool = False
    error: Optional[SaveLoadError] = None
    elapsed_ms: float = 0.0

    def __bool__(self) -> bool:
        return self.success


@dataclass
class SaveFileInfo:
    """存档文件元信息。"""
    file_path: str
    exists: bool
    file_size: int = 0
    created_at: float = 0.0
    modified_at: float = 0.0
    format_version: str = ""
    saved_at: float = 0.0
    checksum: str = ""
    user_data_preview: Optional[Dict[str, Any]] = None


class _JSONEncoder(json.JSONEncoder):
    """
    自定义 JSON 编码器，支持更多 Python 内置类型：
    - set/frozenset -> {"__type__": "set", "data": [...]}
    - tuple -> {"__type__": "tuple", "data": [...]}
    - bytes/bytearray -> {"__type__": "bytes", "data": "...base64..."}
    - complex -> {"__type__": "complex", "real": x, "imag": y}
    - datetime (imported lazily) -> {"__type__": "datetime", "iso": "..."}
    - uuid -> {"__type__": "uuid", "hex": "..."}
    - 任何实现了 to_dict() 或 __dict__ 的对象
    """

    def default(self, obj: Any) -> Any:
        try:
            return super().default(obj)
        except TypeError:
            pass

        if isinstance(obj, (set, frozenset)):
            return {"__type__": "set", "data": list(obj)}

        if isinstance(obj, tuple):
            return {"__type__": "tuple", "data": list(obj)}

        if isinstance(obj, (bytes, bytearray)):
            import base64
            return {
                "__type__": "bytes",
                "data": base64.b64encode(bytes(obj)).decode("ascii"),
            }

        if isinstance(obj, complex):
            return {"__type__": "complex", "real": obj.real, "imag": obj.imag}

        if isinstance(obj, uuid.UUID):
            return {"__type__": "uuid", "hex": obj.hex}

        try:
            from datetime import datetime, date
            if isinstance(obj, (datetime, date)):
                return {"__type__": type(obj).__name__, "iso": obj.isoformat()}
        except ImportError:
            pass

        if isinstance(
            obj,
            (
                types.FunctionType,
                types.MethodType,
                types.LambdaType,
                types.ModuleType,
                type,
                types.GeneratorType,
                types.CoroutineType,
                types.AsyncGeneratorType,
            ),
        ):
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

        if hasattr(obj, "to_dict") and callable(obj.to_dict):
            try:
                return {"__type__": "object", "class": obj.__class__.__name__, "data": obj.to_dict()}
            except Exception:
                pass

        if hasattr(obj, "__dict__"):
            try:
                return {"__type__": "object", "class": obj.__class__.__name__, "data": vars(obj)}
            except Exception:
                pass

        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _json_object_hook(dct: Dict[str, Any]) -> Any:
    """自定义 JSON 对象反序列化钩子，还原特殊类型。"""
    if "__type__" not in dct:
        return dct

    t = dct["__type__"]

    if t == "set":
        return set(dct.get("data", []))

    if t == "tuple":
        return tuple(dct.get("data", []))

    if t == "bytes":
        import base64
        try:
            return base64.b64decode(dct["data"].encode("ascii"))
        except Exception as e:
            raise ValueError(f"Failed to decode bytes: {e}")

    if t == "complex":
        return complex(dct["real"], dct["imag"])

    if t == "uuid":
        return uuid.UUID(hex=dct["hex"])

    if t in ("datetime", "date"):
        from datetime import datetime, date
        try:
            if t == "datetime":
                return datetime.fromisoformat(dct["iso"])
            return date.fromisoformat(dct["iso"])
        except Exception as e:
            raise ValueError(f"Failed to parse {t}: {e}")

    if t == "object":
        return dct.get("data", dct)

    return dct


def _compute_checksum(data_bytes: bytes, algorithm: str = DEFAULT_CHECKSUM_ALGORITHM) -> str:
    """计算数据的校验和。"""
    h = hashlib.new(algorithm)
    h.update(data_bytes)
    return h.hexdigest()


def _ensure_directory(file_path: str) -> None:
    """确保文件所在目录存在，必要时创建目录。"""
    directory = os.path.dirname(os.path.abspath(file_path))
    if directory and not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as e:
            raise FilePermissionError(
                f"无法创建目录 '{directory}': {e.strerror if hasattr(e, 'strerror') else str(e)}"
            )


def _validate_save_container(container: Dict[str, Any]) -> None:
    """验证存档容器结构是否完整。"""
    required_fields = ("format_version", "saved_at", "checksum", "algorithm", "data")
    for field in required_fields:
        if field not in container:
            raise InvalidFormatError(f"存档文件缺少必需字段: '{field}'")

    if not isinstance(container["format_version"], str):
        raise InvalidFormatError("'format_version' 必须是字符串")

    if not isinstance(container["checksum"], str):
        raise InvalidFormatError("'checksum' 必须是字符串")

    if not isinstance(container["algorithm"], str):
        raise InvalidFormatError("'algorithm' 必须是字符串")

    if not isinstance(container["saved_at"], (int, float)):
        raise InvalidFormatError("'saved_at' 必须是数字")


def _check_version_compatibility(file_version: str) -> None:
    """检查存档格式版本兼容性。当前策略：主版本号必须匹配。"""
    try:
        f_major = file_version.split(".")[0]
        c_major = SAVE_FORMAT_VERSION.split(".")[0]
        if f_major != c_major:
            raise VersionMismatchError(
                f"存档格式版本不兼容: 文件版本 {file_version}, "
                f"当前支持版本 {SAVE_FORMAT_VERSION}"
            )
    except (AttributeError, IndexError):
        raise VersionMismatchError(f"无效的版本号格式: {file_version}")


def saveData(
    filePath: str,
    data: Any,
    pretty_print: bool = True,
    encoding: str = "utf-8",
    algorithm: str = DEFAULT_CHECKSUM_ALGORITHM,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> SaveResult:
    """
    将数据以 JSON 格式原子性地写入存档文件。

    Args:
        filePath: 目标存档文件的路径（绝对或相对路径，支持自定义目录和文件名）
        data: 需要存档的任意可序列化数据
        pretty_print: 是否以美化格式输出 JSON（更易读，默认为 True）
        encoding: 文件编码，默认 utf-8
        algorithm: 校验和算法名（如 sha256, md5, sha1）
        extra_metadata: 附加元数据字典，会被写入存档的 metadata 字段

    Returns:
        SaveResult 结果对象，包含 success、file_path、file_size、checksum、error 等字段

    Raises:
        不会主动抛出异常，所有错误都封装在 SaveResult.error 中
    """
    start_time = time.perf_counter()
    abs_path = os.path.abspath(filePath)

    try:
        processed_data = _preprocess_for_json(data)
        serialized_bytes = json.dumps(
            processed_data,
            cls=_JSONEncoder,
            ensure_ascii=False,
            indent=2 if pretty_print else None,
            separators=None if pretty_print else (",", ":"),
            sort_keys=False,
        ).encode(encoding)
    except (TypeError, ValueError, UnicodeEncodeError) as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return SaveResult(
            success=False,
            file_path=abs_path,
            error=SerializationError(f"数据序列化失败: {e}"),
            elapsed_ms=elapsed,
        )

    container: Dict[str, Any] = {
        "format_version": SAVE_FORMAT_VERSION,
        "saved_at": time.time(),
        "algorithm": algorithm,
        "checksum": "",
        "metadata": {
            "file_name": os.path.basename(abs_path),
            "encoding": encoding,
            "python_version": sys.version,
            "platform": sys.platform,
        },
        "data": None,
    }

    if extra_metadata:
        try:
            container["metadata"]["extra"] = json.loads(
                json.dumps(extra_metadata, cls=_JSONEncoder, ensure_ascii=False)
            )
        except Exception:
            container["metadata"]["extra_raw"] = str(extra_metadata)

    try:
        container["data"] = json.loads(serialized_bytes.decode(encoding))
    except json.JSONDecodeError as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return SaveResult(
            success=False,
            file_path=abs_path,
            error=SerializationError(f"序列化数据内部验证失败: {e}"),
            elapsed_ms=elapsed,
        )

    try:
        canonical_bytes = _canonical_data_bytes(container["data"], encoding)
        checksum = _compute_checksum(canonical_bytes, algorithm)
        container["checksum"] = checksum
    except (ValueError, TypeError, UnicodeEncodeError) as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return SaveResult(
            success=False,
            file_path=abs_path,
            error=SaveLoadError(f"计算校验和失败: {e}"),
            elapsed_ms=elapsed,
        )

    final_json_bytes = json.dumps(
        container,
        cls=_JSONEncoder,
        ensure_ascii=False,
        indent=2 if pretty_print else None,
        separators=None if pretty_print else (",", ":"),
    ).encode(encoding)

    try:
        _ensure_directory(abs_path)
    except SaveLoadError as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return SaveResult(success=False, file_path=abs_path, error=e, elapsed_ms=elapsed)

    file_dir = os.path.dirname(abs_path) or "."
    file_base = os.path.basename(abs_path)

    try:
        fd, tmp_path = tempfile.mkstemp(
            prefix=f".{file_base}.",
            suffix=".tmp",
            dir=file_dir,
        )
    except OSError as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return SaveResult(
            success=False,
            file_path=abs_path,
            error=FilePermissionError(f"创建临时文件失败: {e.strerror if hasattr(e, 'strerror') else str(e)}"),
            elapsed_ms=elapsed,
        )

    try:
        try:
            with os.fdopen(fd, "wb") as tmp_file:
                tmp_file.write(final_json_bytes)
                tmp_file.flush()
                try:
                    os.fsync(tmp_file.fileno())
                except (OSError, AttributeError):
                    pass
        except OSError as e:
            raise FilePermissionError(
                f"写入临时文件失败: {e.strerror if hasattr(e, 'strerror') else str(e)}"
            )

        try:
            if os.name == "nt" and os.path.exists(abs_path):
                try:
                    os.remove(abs_path)
                except OSError:
                    pass
            shutil.move(tmp_path, abs_path)
        except OSError as e:
            raise FilePermissionError(
                f"替换目标文件失败: {e.strerror if hasattr(e, 'strerror') else str(e)}"
            )

    except SaveLoadError as e:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
        elapsed = (time.perf_counter() - start_time) * 1000
        return SaveResult(success=False, file_path=abs_path, error=e, elapsed_ms=elapsed)

    try:
        file_size = os.path.getsize(abs_path)
    except OSError:
        file_size = len(final_json_bytes)

    elapsed = (time.perf_counter() - start_time) * 1000
    return SaveResult(
        success=True,
        file_path=abs_path,
        file_size=file_size,
        checksum=checksum,
        elapsed_ms=elapsed,
    )


def loadData(
    filePath: str,
    validator: Optional[Callable[[Any], bool]] = None,
    encoding: str = "utf-8",
    verify_checksum: bool = True,
) -> LoadResult:
    """
    从存档文件加载并验证数据。

    Args:
        filePath: 存档文件路径（绝对或相对路径）
        validator: 可选的自定义数据验证函数，签名为 validator(data) -> bool；
                   返回 False 或抛出异常将导致 DataValidationError
        encoding: 文件编码，默认 utf-8
        verify_checksum: 是否启用校验和验证（默认为 True，关闭可加快加载速度）

    Returns:
        LoadResult 结果对象，包含 success、data、metadata、checksum_verified、error 等字段

    Raises:
        不会主动抛出异常，所有错误都封装在 LoadResult.error 中
    """
    start_time = time.perf_counter()
    abs_path = os.path.abspath(filePath)

    if not os.path.exists(abs_path):
        elapsed = (time.perf_counter() - start_time) * 1000
        return LoadResult(
            success=False,
            file_path=abs_path,
            error=FileNotFoundError(f"存档文件不存在: {abs_path}"),
            elapsed_ms=elapsed,
        )

    if not os.path.isfile(abs_path):
        elapsed = (time.perf_counter() - start_time) * 1000
        return LoadResult(
            success=False,
            file_path=abs_path,
            error=FileNotFoundError(f"路径不是文件: {abs_path}"),
            elapsed_ms=elapsed,
        )

    try:
        with open(abs_path, "rb") as f:
            raw_bytes = f.read()
    except PermissionError as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return LoadResult(
            success=False,
            file_path=abs_path,
            error=FilePermissionError(f"无法读取文件，权限不足: {e.strerror if hasattr(e, 'strerror') else str(e)}"),
            elapsed_ms=elapsed,
        )
    except OSError as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return LoadResult(
            success=False,
            file_path=abs_path,
            error=FilePermissionError(f"读取文件失败: {e.strerror if hasattr(e, 'strerror') else str(e)}"),
            elapsed_ms=elapsed,
        )

    try:
        raw_text = raw_bytes.decode(encoding)
    except UnicodeDecodeError as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return LoadResult(
            success=False,
            file_path=abs_path,
            error=InvalidFormatError(f"文件编码错误（期望 {encoding}）: {e}"),
            elapsed_ms=elapsed,
        )

    try:
        container_raw = json.loads(raw_text)
    except json.JSONDecodeError as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return LoadResult(
            success=False,
            file_path=abs_path,
            error=InvalidFormatError(f"JSON 解析失败，文件可能损坏: {e.msg} (行 {e.lineno}, 列 {e.colno})"),
            elapsed_ms=elapsed,
        )

    if not isinstance(container_raw, dict):
        elapsed = (time.perf_counter() - start_time) * 1000
        return LoadResult(
            success=False,
            file_path=abs_path,
            error=InvalidFormatError("存档文件根节点必须是 JSON 对象"),
            elapsed_ms=elapsed,
        )

    try:
        _validate_save_container(container_raw)
    except SaveLoadError as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return LoadResult(success=False, file_path=abs_path, error=e, elapsed_ms=elapsed)

    try:
        _check_version_compatibility(container_raw["format_version"])
    except SaveLoadError as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return LoadResult(success=False, file_path=abs_path, error=e, elapsed_ms=elapsed)

    checksum_ok = False
    if verify_checksum:
        algorithm = container_raw["algorithm"]
        stored_checksum = container_raw["checksum"]
        try:
            canonical_bytes = _canonical_data_bytes(container_raw["data"], encoding)
            actual_checksum = _compute_checksum(canonical_bytes, algorithm)
            if actual_checksum.lower() != stored_checksum.lower():
                elapsed = (time.perf_counter() - start_time) * 1000
                return LoadResult(
                    success=False,
                    file_path=abs_path,
                    error=ChecksumMismatchError(
                        f"校验和验证失败: 期望 {stored_checksum}, 实际 {actual_checksum}"
                    ),
                    elapsed_ms=elapsed,
                )
            checksum_ok = True
        except SaveLoadError as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            return LoadResult(success=False, file_path=abs_path, error=e, elapsed_ms=elapsed)
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            return LoadResult(
                success=False,
                file_path=abs_path,
                error=SaveLoadError(f"校验和计算过程出错: {e}"),
                elapsed_ms=elapsed,
            )

    try:
        container = json.loads(raw_text, object_hook=_json_object_hook)
    except json.JSONDecodeError as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return LoadResult(
            success=False,
            file_path=abs_path,
            error=InvalidFormatError(f"类型还原阶段 JSON 解析失败: {e.msg}"),
            elapsed_ms=elapsed,
        )

    user_data = container.get("data")
    metadata = {
        "format_version": container_raw["format_version"],
        "saved_at": container_raw["saved_at"],
        "algorithm": container_raw["algorithm"],
        "checksum": container_raw["checksum"],
        **container.get("metadata", {}),
    }

    if validator is not None:
        try:
            valid = validator(user_data)
            if not valid:
                elapsed = (time.perf_counter() - start_time) * 1000
                return LoadResult(
                    success=False,
                    file_path=abs_path,
                    metadata=metadata,
                    checksum_verified=checksum_ok,
                    error=DataValidationError("自定义数据验证函数返回 False"),
                    elapsed_ms=elapsed,
                )
        except SaveLoadError as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            return LoadResult(
                success=False,
                file_path=abs_path,
                metadata=metadata,
                checksum_verified=checksum_ok,
                error=e,
                elapsed_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            return LoadResult(
                success=False,
                file_path=abs_path,
                metadata=metadata,
                checksum_verified=checksum_ok,
                error=DataValidationError(f"自定义数据验证函数抛出异常: {e}"),
                elapsed_ms=elapsed,
            )

    elapsed = (time.perf_counter() - start_time) * 1000
    return LoadResult(
        success=True,
        data=user_data,
        file_path=abs_path,
        metadata=metadata,
        checksum_verified=checksum_ok,
        elapsed_ms=elapsed,
    )


def get_save_file_info(filePath: str, encoding: str = "utf-8") -> SaveFileInfo:
    """
    获取存档文件的元信息（不完整加载用户数据），用于存档列表展示。

    Args:
        filePath: 存档文件路径
        encoding: 文件编码

    Returns:
        SaveFileInfo 对象；若文件不存在或损坏，对应字段会留空但不会抛异常
    """
    abs_path = os.path.abspath(filePath)
    exists = os.path.isfile(abs_path)
    info = SaveFileInfo(file_path=abs_path, exists=exists)

    if not exists:
        return info

    try:
        stat = os.stat(abs_path)
        info.file_size = stat.st_size
        info.created_at = stat.st_ctime
        info.modified_at = stat.st_mtime
    except OSError:
        pass

    try:
        with open(abs_path, "r", encoding=encoding) as f:
            container = json.load(f)
        if isinstance(container, dict):
            info.format_version = container.get("format_version", "")
            info.saved_at = container.get("saved_at", 0)
            info.checksum = container.get("checksum", "")
            data = container.get("data")
            if isinstance(data, dict):
                preview = {}
                for k, v in list(data.items())[:10]:
                    if isinstance(v, (str, int, float, bool, type(None))):
                        preview[k] = v
                    elif isinstance(v, (list, tuple)):
                        preview[k] = f"<list[{len(v)}]>"
                    elif isinstance(v, dict):
                        preview[k] = f"<dict[{len(v)}]>"
                    else:
                        preview[k] = f"<{type(v).__name__}>"
                info.user_data_preview = preview
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        pass

    return info


def list_save_files(
    directory: str,
    extension: Union[str, List[str]] = ".sav.json",
    recursive: bool = False,
) -> List[str]:
    """
    列出指定目录下的存档文件。

    Args:
        directory: 目标目录
        extension: 文件扩展名（字符串或字符串列表），如 '.sav.json' 或 ['.sav.json', '.json']
        recursive: 是否递归子目录

    Returns:
        匹配的存档文件绝对路径列表（按修改时间倒序排列，最新的在前）
    """
    if isinstance(extension, str):
        extensions = (extension.lower(),)
    else:
        extensions = tuple(e.lower() for e in extension)

    directory = os.path.abspath(directory)
    results: List[str] = []

    if not os.path.isdir(directory):
        return results

    def _walk(dir_path: str):
        try:
            with os.scandir(dir_path) as it:
                for entry in it:
                    try:
                        if entry.is_file(follow_symlinks=False):
                            name_lower = entry.name.lower()
                            if any(name_lower.endswith(ext) for ext in extensions):
                                results.append(entry.path)
                        elif recursive and entry.is_dir(follow_symlinks=False):
                            _walk(entry.path)
                    except OSError:
                        continue
        except OSError:
            return

    _walk(directory)

    def _mtime(path: str) -> float:
        try:
            return os.path.getmtime(path)
        except OSError:
            return 0.0

    results.sort(key=_mtime, reverse=True)
    return results


__all__ = [
    "saveData",
    "loadData",
    "get_save_file_info",
    "list_save_files",
    "SaveResult",
    "LoadResult",
    "SaveFileInfo",
    "SaveLoadError",
    "FileNotFoundError",
    "FilePermissionError",
    "InvalidFormatError",
    "ChecksumMismatchError",
    "VersionMismatchError",
    "DataValidationError",
    "SerializationError",
    "SAVE_FORMAT_VERSION",
    "DEFAULT_CHECKSUM_ALGORITHM",
]
