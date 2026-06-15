# -*- coding: utf-8 -*-
"""
tests/test_save_load.py - 存档与读档模块测试

覆盖以下功能:
- 基本 saveData/loadData 流程
- 复杂数据类型序列化 (set, tuple, bytes, complex, datetime, uuid)
- 原子性写入验证
- 校验和验证 (正常 + 篡改后失败)
- 版本兼容性检查
- 自定义数据验证器
- 错误处理: 文件不存在、格式错误、权限不足、序列化失败
- get_save_file_info 存档信息查询
- list_save_files 存档列表扫描
- 从 core 包顶层导入 API 的可用性
"""

import os
import json
import uuid
import time
import shutil
import pytest
from datetime import datetime, date

from core.save_load import (
    saveData,
    loadData,
    get_save_file_info,
    list_save_files,
    SaveResult,
    LoadResult,
    SaveFileInfo,
    SaveLoadError,
    FileNotFoundError,
    FilePermissionError,
    InvalidFormatError,
    ChecksumMismatchError,
    VersionMismatchError,
    DataValidationError,
    SerializationError,
    SAVE_FORMAT_VERSION,
)


def _make_game_like_data():
    """构造一组模拟游戏存档数据。"""
    return {
        "player": {
            "x": 150.5,
            "y": 420.0,
            "hp": 85,
            "max_hp": 100,
            "coins": 42,
            "facing": 1,
            "inventory": ["sword", "shield", "potion x3"],
            "unlocked_abilities": {"double_jump", "dash"},
        },
        "current_level": 2,
        "progress": {
            "completed_levels": (0, 1),
            "collectibles_found": {
                "level_0": [1, 3, 5],
                "level_1": [0, 2],
            },
        },
        "settings": {
            "bgm_volume": 0.6,
            "sfx_volume": 0.8,
            "fullscreen": False,
        },
        "saved_at_iso": datetime(2025, 1, 15, 10, 30, 0),
        "playtime_seconds": 3612,
        "session_id": uuid.UUID("12345678-1234-5678-1234-567812345678"),
    }


class TestSaveLoadBasic:
    """基本保存与加载流程测试。"""

    def test_save_and_load_roundtrip(self, tmp_path):
        """保存后再加载，数据完全一致。"""
        data = _make_game_like_data()
        path = tmp_path / "slot1.sav.json"

        save_res = saveData(str(path), data)
        assert save_res.success is True
        assert save_res.checksum != ""
        assert save_res.file_size > 0
        assert os.path.exists(path)

        load_res = loadData(str(path))
        assert load_res.success is True
        assert load_res.checksum_verified is True
        assert load_res.metadata is not None
        assert load_res.metadata["format_version"] == SAVE_FORMAT_VERSION

        loaded = load_res.data
        assert loaded["player"]["x"] == data["player"]["x"]
        assert loaded["player"]["hp"] == 85
        assert loaded["current_level"] == 2
        assert loaded["progress"]["completed_levels"] == (0, 1)
        assert loaded["settings"]["bgm_volume"] == pytest.approx(0.6)
        assert loaded["player"]["unlocked_abilities"] == {"double_jump", "dash"}
        assert loaded["session_id"] == data["session_id"]

    def test_save_create_nested_directory(self, tmp_path):
        """保存时自动创建不存在的嵌套目录。"""
        path = tmp_path / "a" / "b" / "c" / "deep_save.sav.json"
        data = {"nested": True}
        res = saveData(str(path), data)
        assert res.success is True
        assert os.path.isfile(path)

    def test_save_extra_metadata(self, tmp_path):
        """附加元数据应出现在加载结果中。"""
        path = tmp_path / "meta.sav.json"
        data = {"hello": "world"}
        save_res = saveData(
            str(path),
            data,
            extra_metadata={"slot_name": "主存档", "player_name": "小明"},
        )
        assert save_res.success
        load_res = loadData(str(path))
        assert load_res.success
        extra = load_res.metadata.get("extra", {})
        assert extra["slot_name"] == "主存档"
        assert extra["player_name"] == "小明"

    def test_save_result_bool_evaluation(self, tmp_path):
        """SaveResult / LoadResult 的 __bool__ 反映 success。"""
        ok = saveData(str(tmp_path / "a.sav.json"), {"x": 1})
        assert bool(ok) is True
        not_ok = loadData(str(tmp_path / "not_exists.sav.json"))
        assert bool(not_ok) is False

    def test_load_without_checksum_verify(self, tmp_path):
        """关闭校验和验证时仍能加载数据。"""
        path = tmp_path / "nocheck.sav.json"
        data = {"v": 123}
        saveData(str(path), data)
        load_res = loadData(str(path), verify_checksum=False)
        assert load_res.success is True
        assert load_res.checksum_verified is False
        assert load_res.data["v"] == 123


class TestSerializationTypes:
    """复杂数据类型序列化 / 反序列化测试。"""

    def test_set_and_frozenset(self, tmp_path):
        path = tmp_path / "types.sav.json"
        data = {"s": {1, 2, 3}, "fs": frozenset({"a", "b"})}
        saveData(str(path), data)
        res = loadData(str(path))
        assert res.success
        assert res.data["s"] == {1, 2, 3}
        assert res.data["fs"] == frozenset({"a", "b"})

    def test_tuple_preserved(self, tmp_path):
        path = tmp_path / "tup.sav.json"
        data = {"coords": (10, 20, 30)}
        saveData(str(path), data)
        res = loadData(str(path))
        assert res.success
        assert res.data["coords"] == (10, 20, 30)
        assert isinstance(res.data["coords"], tuple)

    def test_bytes_roundtrip(self, tmp_path):
        path = tmp_path / "b.sav.json"
        raw = bytes([0, 1, 2, 255, 128])
        saveData(str(path), {"blob": raw})
        res = loadData(str(path))
        assert res.success
        assert res.data["blob"] == raw

    def test_complex_number(self, tmp_path):
        path = tmp_path / "c.sav.json"
        saveData(str(path), {"z": complex(3, 4)})
        res = loadData(str(path))
        assert res.success
        assert res.data["z"] == complex(3, 4)

    def test_datetime_and_date(self, tmp_path):
        path = tmp_path / "dt.sav.json"
        dt = datetime(2025, 6, 1, 12, 0, 0)
        d = date(2025, 12, 25)
        saveData(str(path), {"dt": dt, "d": d})
        res = loadData(str(path))
        assert res.success
        assert res.data["dt"] == dt
        assert res.data["d"] == d

    def test_uuid_roundtrip(self, tmp_path):
        path = tmp_path / "uid.sav.json"
        u = uuid.uuid4()
        saveData(str(path), {"id": u})
        res = loadData(str(path))
        assert res.success
        assert res.data["id"] == u

    def test_object_with_to_dict(self, tmp_path):
        """实现了 to_dict 方法的对象能被序列化并还原为 dict。"""
        class PlayerStats:
            def __init__(self, hp, coins):
                self.hp = hp
                self.coins = coins
            def to_dict(self):
                return {"hp": self.hp, "coins": self.coins}

        path = tmp_path / "obj.sav.json"
        saveData(str(path), {"stats": PlayerStats(50, 99)})
        res = loadData(str(path))
        assert res.success
        assert res.data["stats"] == {"hp": 50, "coins": 99}


class TestAtomicWrite:
    """原子写入完整性验证。"""

    def test_existing_file_is_replaced_cleanly(self, tmp_path):
        """多次写入覆盖原文件，不会留下临时文件。"""
        path = tmp_path / "overwrite.sav.json"
        saveData(str(path), {"v": 1})
        saveData(str(path), {"v": 2, "more": "data"})
        res = loadData(str(path))
        assert res.success and res.data["v"] == 2

        leftover = list(tmp_path.glob("*.tmp"))
        assert leftover == []

    def test_does_not_leave_tmp_on_failure(self, tmp_path, monkeypatch):
        """序列化失败时不生成目标文件。"""
        path = tmp_path / "fail.sav.json"
        bad_data = {"x": lambda: 42}
        res = saveData(str(path), bad_data)
        assert res.success is False
        assert not os.path.exists(path)
        leftover = list(tmp_path.glob("*.tmp"))
        assert leftover == []


class TestValidation:
    """校验和、版本、自定义验证器测试。"""

    def test_checksum_catches_manual_tampering(self, tmp_path):
        """手动修改 data 字段内容，校验和应失败。"""
        path = tmp_path / "tampered.sav.json"
        saveData(str(path), {"coins": 100})
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        content = content.replace('"coins": 100', '"coins": 999999')
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        res = loadData(str(path))
        assert res.success is False
        assert isinstance(res.error, ChecksumMismatchError)

    def test_version_mismatch_rejected(self, tmp_path):
        """主版本号不匹配时拒绝加载。"""
        path = tmp_path / "old_version.sav.json"
        container = {
            "format_version": "999.0",
            "saved_at": time.time(),
            "algorithm": "sha256",
            "checksum": "abc",
            "data": {"x": 1},
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(container, f)
        res = loadData(str(path), verify_checksum=False)
        assert res.success is False
        assert isinstance(res.error, VersionMismatchError)

    def test_custom_validator_pass(self, tmp_path):
        """自定义验证器返回 True 时正常加载。"""
        path = tmp_path / "v.sav.json"
        saveData(str(path), {"hp": 80, "max_hp": 100})
        res = loadData(
            str(path),
            validator=lambda d: isinstance(d, dict) and "hp" in d,
        )
        assert res.success is True
        assert res.data["hp"] == 80

    def test_custom_validator_reject_false(self, tmp_path):
        """自定义验证器返回 False 时得到 DataValidationError。"""
        path = tmp_path / "v.sav.json"
        saveData(str(path), {"hp": 150, "max_hp": 100})
        res = loadData(
            str(path),
            validator=lambda d: d["hp"] <= d["max_hp"],
        )
        assert res.success is False
        assert isinstance(res.error, DataValidationError)

    def test_custom_validator_exception_caught(self, tmp_path):
        """自定义验证器抛出异常时同样被封装为 DataValidationError。"""
        path = tmp_path / "v.sav.json"
        saveData(str(path), {"x": 1})
        def boom(_d):
            raise RuntimeError("boom")
        res = loadData(str(path), validator=boom)
        assert res.success is False
        assert isinstance(res.error, DataValidationError)
        assert "boom" in str(res.error)


class TestErrorHandling:
    """错误处理与边界情况测试。"""

    def test_file_not_found(self, tmp_path):
        res = loadData(str(tmp_path / "no_file.sav.json"))
        assert res.success is False
        assert isinstance(res.error, FileNotFoundError)

    def test_invalid_json_content(self, tmp_path):
        """加载损坏的（非 JSON）内容。"""
        path = tmp_path / "broken.sav.json"
        path.write_text("{ not json at all ;;;", encoding="utf-8")
        res = loadData(str(path))
        assert res.success is False
        assert isinstance(res.error, InvalidFormatError)

    def test_json_root_not_dict(self, tmp_path):
        """JSON 根节点非对象（数组）。"""
        path = tmp_path / "root.sav.json"
        path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        res = loadData(str(path))
        assert res.success is False
        assert isinstance(res.error, InvalidFormatError)

    def test_missing_required_fields(self, tmp_path):
        """容器缺少必需字段时报 InvalidFormatError。"""
        path = tmp_path / "miss.sav.json"
        path.write_text(json.dumps({"only": "data"}), encoding="utf-8")
        res = loadData(str(path), verify_checksum=False)
        assert res.success is False
        assert isinstance(res.error, InvalidFormatError)

    def test_serialization_failure_for_unsupported_type(self, tmp_path):
        """无法序列化的类型应返回 SerializationError。"""
        path = tmp_path / "ser.sav.json"
        res = saveData(str(path), {"fn": open})
        assert res.success is False
        assert isinstance(res.error, SerializationError)

    def test_encoding_mismatch(self, tmp_path):
        """用非 utf-8 保存的文件被当作 utf-8 加载时会报错。"""
        path = tmp_path / "enc.sav.json"
        saveData(str(path), {"msg": "你好"}, encoding="utf-16")
        res = loadData(str(path), encoding="utf-8")
        assert res.success is False
        assert isinstance(res.error, (InvalidFormatError,))


class TestHelpers:
    """get_save_file_info 与 list_save_files 辅助函数测试。"""

    def test_get_save_file_info_exists(self, tmp_path):
        path = tmp_path / "info.sav.json"
        saveData(str(path), {"coins": 7, "hp": 100})
        info = get_save_file_info(str(path))
        assert isinstance(info, SaveFileInfo)
        assert info.exists is True
        assert info.file_size > 0
        assert info.format_version == SAVE_FORMAT_VERSION
        assert info.checksum != ""
        assert info.user_data_preview is not None
        assert info.user_data_preview["coins"] == 7

    def test_get_save_file_info_not_exists(self, tmp_path):
        info = get_save_file_info(str(tmp_path / "nope.sav.json"))
        assert info.exists is False
        assert info.file_size == 0
        assert info.user_data_preview is None

    def test_list_save_files_single_extension(self, tmp_path):
        (tmp_path / "a.sav.json").write_text("{}", encoding="utf-8")
        (tmp_path / "b.sav.json").write_text("{}", encoding="utf-8")
        (tmp_path / "c.txt").write_text("{}", encoding="utf-8")
        found = list_save_files(str(tmp_path), extension=".sav.json")
        assert len(found) == 2
        assert all(f.endswith(".sav.json") for f in found)

    def test_list_save_files_multi_extensions(self, tmp_path):
        (tmp_path / "a.sav.json").write_text("{}")
        (tmp_path / "b.json").write_text("{}")
        (tmp_path / "c.txt").write_text("{}")
        found = list_save_files(str(tmp_path), extension=[".sav.json", ".json"])
        assert len(found) == 2

    def test_list_save_files_recursive(self, tmp_path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (tmp_path / "top.sav.json").write_text("{}")
        (sub / "deep.sav.json").write_text("{}")
        flat = list_save_files(str(tmp_path), recursive=False)
        deep = list_save_files(str(tmp_path), recursive=True)
        assert len(flat) == 1
        assert len(deep) == 2

    def test_list_save_files_sorted_by_mtime(self, tmp_path):
        """最新修改的文件排在列表前面。"""
        p1 = tmp_path / "old.sav.json"
        p2 = tmp_path / "new.sav.json"
        t1 = time.time() - 1000
        t2 = time.time()
        p1.write_text("{}")
        p2.write_text("{}")
        os.utime(p1, (t1, t1))
        os.utime(p2, (t2, t2))
        found = list_save_files(str(tmp_path))
        assert found[0].endswith("new.sav.json")
        assert found[1].endswith("old.sav.json")


class TestTopLevelImport:
    """从 core 包顶层导入的公共 API 可用性。"""

    def test_import_from_core_package(self):
        """确保 core/__init__.py 正确导出所有 API。"""
        from core import (
            saveData as sd,
            loadData as ld,
            get_save_file_info as gfi,
            list_save_files as lsf,
            SaveResult as SR,
            LoadResult as LR,
            SaveFileInfo as SFI,
            SaveLoadError as SLE,
            FileNotFoundError as FNF,
            FilePermissionError as FPE,
            InvalidFormatError as IFE,
            ChecksumMismatchError as CME,
            VersionMismatchError as VME,
            DataValidationError as DVE,
            SerializationError as SE,
        )
        assert callable(sd) and callable(ld) and callable(gfi) and callable(lsf)
        for cls in (SLE, FNF, FPE, IFE, CME, VME, DVE, SE):
            assert issubclass(cls, Exception)

    def test_save_via_core_import_roundtrip(self, tmp_path):
        """使用顶层导入的 saveData/loadData 执行完整流程。"""
        from core import saveData, loadData
        path = str(tmp_path / "core_api.sav.json")
        data = {"message": "来自顶层导入"}
        assert saveData(path, data).success
        res = loadData(path)
        assert res.success
        assert res.data["message"] == "来自顶层导入"
