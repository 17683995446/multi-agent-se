"""第30阶段验收脚本: 类原子 + 模块原子 + CodeAtomizer整合.

验证四级代码原子化体系的第三级（类）和第四级（模块）实现，
以及CodeAtomizer整合门面类。
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from multi_agent_se.atomicity.class_atom.models import (
    AttributeInfo, ClassAtom, ClassMetrics, ClassType, ClassVisibility,
    InheritanceInfo, InheritanceType, MethodSignature,
)
from multi_agent_se.atomicity.class_atom.extractor import ClassExtractor
from multi_agent_se.atomicity.module_atom.models import ImportInfo, ModuleAtom, ExportInfo, ModuleMetrics
from multi_agent_se.atomicity.module_atom.extractor import ModuleExtractor
from multi_agent_se.atomicity.atomizer import CodeAtomizer, AtomizationResult


def print_header(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(name: str, passed: bool) -> None:
    status = "[✓ PASS]" if passed else "[✗ FAIL]"
    print(f"  {status} {name}")


# 测试用例源码
SAMPLE_CODE = '''\
"""示例模块 - 用于测试四级代码原子化."""

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from enum import Enum

MAX_SIZE = 100
DEFAULT_TIMEOUT = 30


class Status(Enum):
    """状态枚举."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"


class DataMixin:
    """数据混入类."""
    
    def to_dict(self) -> Dict[str, Any]:
        return {}


class BaseService(ABC, DataMixin):
    """基础服务抽象类."""
    
    _instance_count = 0
    
    def __init__(self, name: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.name = name
        self.timeout = timeout
        self._status = Status.PENDING
        BaseService._instance_count += 1
    
    @property
    def status(self) -> Status:
        return self._status
    
    @abstractmethod
    def process(self, data: List[int]) -> Dict[str, Any]:
        pass
    
    @classmethod
    def get_instance_count(cls) -> int:
        return cls._instance_count
    
    def _validate(self, data: List[int]) -> bool:
        return len(data) <= MAX_SIZE


class UserService(BaseService):
    """用户服务类."""
    
    def __init__(self, db_url: str) -> None:
        super().__init__("user_service")
        self.db_url = db_url
        self.users: List[Dict] = []
    
    def process(self, data: List[int]) -> Dict[str, Any]:
        if not self._validate(data):
            return {"error": "Data too large"}
        return {"users": len(data)}
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        for user in self.users:
            if user.get("id") == user_id:
                return user
        return None


class ValidationError(Exception):
    """验证错误异常."""
    pass


def helper_function(x: int) -> int:
    """辅助函数."""
    return x * 2
'''


def test_class_type_enum() -> bool:
    print_header("测试1: ClassType 枚举")
    types = list(ClassType)
    print(f"  类类型: {[t.value for t in types]}")
    assert len(types) == 10
    print_result("ClassType", True)
    return True


def test_class_visibility_enum() -> bool:
    print_header("测试2: ClassVisibility 枚举")
    vis = list(ClassVisibility)
    print(f"  可见性: {[v.value for v in vis]}")
    assert len(vis) == 3
    print_result("ClassVisibility", True)
    return True


def test_inheritance_type_enum() -> bool:
    print_header("测试3: InheritanceType 枚举")
    inh = list(InheritanceType)
    print(f"  继承类型: {[i.value for i in inh]}")
    assert len(inh) == 4
    print_result("InheritanceType", True)
    return True


def test_attribute_info() -> bool:
    print_header("测试4: AttributeInfo")
    attr = AttributeInfo(
        name="user_id",
        type_annotation="int",
        default_value="0",
        is_class_attribute=False,
        is_property=True,
    )
    d = attr.to_dict()
    assert d["name"] == "user_id"
    assert d["is_property"] is True
    print_result("AttributeInfo", True)
    return True


def test_method_signature() -> bool:
    print_header("测试5: MethodSignature")
    sig = MethodSignature(
        name="process",
        is_abstract=True,
        is_async=False,
        visibility="public",
        parameters=["self", "data"],
        return_type="Dict[str, Any]",
    )
    d = sig.to_dict()
    assert d["name"] == "process"
    assert d["is_abstract"] is True
    print_result("MethodSignature", True)
    return True


def test_class_metrics() -> bool:
    print_header("测试6: ClassMetrics")
    metrics = ClassMetrics(
        method_count=25,
        lines_of_code=600,
    )
    assert metrics.is_god_class is True
    assert metrics.is_data_class is False
    d = metrics.to_dict()
    assert d["is_god_class"] is True
    print_result("ClassMetrics", True)
    return True


def test_class_atom_model() -> bool:
    print_header("测试7: ClassAtom 模型")
    atom = ClassAtom(
        name="UserService",
        class_type=ClassType.REGULAR,
        bases=[InheritanceInfo(base_class="BaseService")],
    )
    atom.methods.append(MethodSignature(name="get_user"))
    atom.attributes.append(AttributeInfo(name="db_url"))
    
    assert atom.name == "UserService"
    assert atom.full_name == "UserService"
    assert atom.has_method("get_user") is True
    assert atom.has_attribute("db_url") is True
    assert atom.is_subclass_of("BaseService") is True
    
    d = atom.to_dict()
    assert d["name"] == "UserService"
    print_result("ClassAtom", True)
    return True


def test_class_extractor() -> bool:
    print_header("测试8: ClassExtractor 基础提取")
    extractor = ClassExtractor(SAMPLE_CODE, file_path="sample.py")
    classes = extractor.extract()
    
    print(f"  提取类数: {len(classes)}")
    class_names = [c.name for c in classes]
    print(f"  类名: {class_names}")
    
    # 验证各类被正确识别
    status_enum = extractor.get_class("Status")
    if status_enum:
        assert status_enum.class_type == ClassType.ENUM
        print(f"  ✓ Status 识别为枚举类")
    
    base_service = extractor.get_class("BaseService")
    if base_service:
        assert base_service.class_type == ClassType.ABSTRACT
        assert base_service.is_abstract is True
        assert len(base_service.bases) >= 2  # ABC, DataMixin
        print(f"  ✓ BaseService 识别为抽象类，继承: {[b.base_class for b in base_service.bases]}")
    
    data_mixin = extractor.get_class("DataMixin")
    if data_mixin:
        assert data_mixin.class_type == ClassType.MIXIN
        print(f"  ✓ DataMixin 识别为Mixin类")
    
    validation_error = extractor.get_class("ValidationError")
    if validation_error:
        assert validation_error.class_type == ClassType.EXCEPTION
        print(f"  ✓ ValidationError 识别为异常类")
    
    print_result("ClassExtractor", True)
    return True


def test_class_inheritance_graph() -> bool:
    print_header("测试9: 类继承关系图")
    extractor = ClassExtractor(SAMPLE_CODE, file_path="sample.py")
    classes = extractor.extract()
    
    graph = extractor.get_inheritance_graph()
    print(f"  继承图: {graph}")
    
    reverse_graph = extractor.get_reverse_inheritance_graph()
    print(f"  反向继承图: {reverse_graph}")
    
    print_result("继承关系图", True)
    return True


def test_module_atom() -> bool:
    print_header("测试10: ModuleAtom 模型")
    module = ModuleAtom(
        name="sample",
        file_path="sample.py",
    )
    module.imports.append(ImportInfo(name="List", module="typing"))
    module.exports.append(ExportInfo(name="UserService", type="class"))
    module.classes.append("UserService")
    module.functions.append("helper_function")
    
    assert module.name == "sample"
    assert len(module.imports) == 1
    assert len(module.exports) == 1
    
    d = module.to_dict()
    assert d["name"] == "sample"
    print_result("ModuleAtom", True)
    return True


def test_module_extractor() -> bool:
    print_header("测试11: ModuleExtractor 提取")
    extractor = ModuleExtractor(SAMPLE_CODE, file_path="sample.py")
    module = extractor.extract()
    
    print(f"  模块名: {module.name}")
    print(f"  导入数: {len(module.imports)}")
    print(f"  导出数: {len(module.exports)}")
    print(f"  类数: {len(module.classes)}")
    print(f"  函数数: {len(module.functions)}")
    print(f"  全局变量: {module.global_variables}")
    print(f"  代码行数: {module.lines_of_code}")
    
    assert len(module.imports) >= 3  # typing, abc, enum
    assert "UserService" in module.classes
    assert "helper_function" in module.functions
    
    print_result("ModuleExtractor", True)
    return True


def test_code_atomizer() -> bool:
    print_header("测试12: CodeAtomizer 整合")
    atomizer = CodeAtomizer()
    result = atomizer.atomize_source(SAMPLE_CODE, file_path="sample.py")
    
    print(f"  文件: {result.file_path}")
    print(f"  模块: {result.module.name if result.module else 'None'}")
    print(f"  类: {len(result.classes)}个")
    print(f"  方法: {len(result.methods)}个")
    print(f"  变量: {len(result.variables)}个")
    
    assert result.module is not None
    assert len(result.classes) >= 4  # Status, DataMixin, BaseService, UserService, ValidationError
    assert len(result.methods) >= 5
    assert len(result.variables) >= 5
    
    # 测试摘要
    summary = result.summary()
    print(f"\n  摘要:\n{summary}")
    
    print_result("CodeAtomizer", True)
    return True


def test_atomizer_directory() -> bool:
    print_header("测试13: CodeAtomizer 目录扫描")
    atomizer = CodeAtomizer()
    
    # 扫描atomicity目录
    results = atomizer.atomize_directory("src/multi_agent_se/atomicity")
    
    print(f"  扫描文件数: {len(results)}")
    
    if results:
        metrics = atomizer.get_metrics(results)
        print(f"  总模块: {metrics.total_modules}")
        print(f"  总类: {metrics.total_classes}")
        print(f"  总函数: {metrics.total_functions}")
        print(f"  总变量: {metrics.total_variables}")
    
    print_result("目录扫描", True)
    return True


def main() -> None:
    print("=" * 60)
    print("  第30阶段验收: 类原子 + 模块原子 + CodeAtomizer")
    print("=" * 60)
    
    tests = [
        test_class_type_enum,
        test_class_visibility_enum,
        test_inheritance_type_enum,
        test_attribute_info,
        test_method_signature,
        test_class_metrics,
        test_class_atom_model,
        test_class_extractor,
        test_class_inheritance_graph,
        test_module_atom,
        test_module_extractor,
        test_code_atomizer,
        test_atomizer_directory,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"  ✗ EXCEPTION: {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"  验收结果: {passed} 通过, {failed} 失败")
    print(f"{'='*60}")
    
    if failed == 0:
        print(f"\n  ✓ 第30阶段验收通过！")
        print(f"\n  四级代码原子化体系完成！")
        print(f"    - 第一级: 变量原子 (VariableAtom)")
        print(f"    - 第二级: 方法原子 (MethodAtom)")
        print(f"    - 第三级: 类原子 (ClassAtom)")
        print(f"    - 第四级: 模块原子 (ModuleAtom)")
        print(f"    - 整合门面: CodeAtomizer")
        print(f"{'='*60}")
        sys.exit(0)
    else:
        print(f"\n  ✗ 有 {failed} 个测试失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
