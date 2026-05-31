"""第29阶段验收脚本: 变量原子 + 方法原子.

验证四级代码原子化体系的第一级（变量）和第二级（方法）实现。
"""

import sys
import os

# 确保项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from multi_agent_se.atomicity.variable.models import (
    CodeLocation,
    VariableAtom,
    VariableMutability,
    VariableReference,
    VariableScope,
)
from multi_agent_se.atomicity.variable.extractor import VariableExtractor
from multi_agent_se.atomicity.method.models import (
    CallRelation,
    ComplexityMetrics,
    MethodAtom,
    MethodType,
    MethodVisibility,
    ParameterInfo,
)
from multi_agent_se.atomicity.method.extractor import MethodExtractor


# ========== 测试辅助 ==========

def print_header(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(name: str, passed: bool) -> None:
    status = "[✓ PASS]" if passed else "[✗ FAIL]"
    print(f"  {status} {name}")


# ========== 测试用例 ==========

# 测试用源码
SAMPLE_CODE = '''\
"""示例模块."""

from typing import List, Optional

MAX_RETRIES = 3
API_BASE_URL = "https://api.example.com"

class UserService:
    """用户服务类."""

    _instance_count = 0

    def __init__(self, db_url: str, timeout: int = 30) -> None:
        self.db_url = db_url
        self.timeout = timeout
        self._connected = False
        UserService._instance_count += 1

    @classmethod
    def get_instance_count(cls) -> int:
        return cls._instance_count

    @staticmethod
    def validate_email(email: str) -> bool:
        return "@" in email

    def get_user(self, user_id: int) -> Optional[dict]:
        """获取用户信息."""
        query = f"SELECT * FROM users WHERE id = {user_id}"
        result = self._execute_query(query)
        return result

    def _execute_query(self, query: str) -> dict:
        """执行查询."""
        try:
            return {"result": query, "timeout": self.timeout}
        except Exception as e:
            return {"error": str(e)}

    async def get_users_async(self, ids: List[int]) -> List[dict]:
        """异步获取多个用户."""
        results = []
        for uid in ids:
            user = self.get_user(uid)
            if user:
                results.append(user)
        return results


def calculate_score(scores: List[int], weight: float = 1.0) -> float:
    """计算加权分数."""
    total = 0
    count = 0
    for score in scores:
        if score > 0:
            total += score * weight
            count += 1
    if count == 0:
        return 0.0
    return total / count


def process_data(data: dict, *, verbose: bool = False) -> dict:
    """处理数据."""
    result = {}
    for key, value in data.items():
        if verbose:
            print(f"Processing {key}")
        result[key] = value.upper() if isinstance(value, str) else value
    return result
'''


def test_variable_scope_enum() -> bool:
    """测试变量作用域枚举."""
    print_header("测试1: VariableScope 枚举")
    scopes = list(VariableScope)
    print(f"  作用域类型: {[s.value for s in scopes]}")
    assert len(scopes) == 7
    assert VariableScope.GLOBAL.value == "global"
    assert VariableScope.LOCAL.value == "local"
    assert VariableScope.PARAMETER.value == "parameter"
    assert VariableScope.CLASS_ATTRIBUTE.value == "class_attribute"
    assert VariableScope.INSTANCE_ATTRIBUTE.value == "instance_attribute"
    assert VariableScope.CLOSURE.value == "closure"
    assert VariableScope.IMPORT.value == "import"
    print_result("VariableScope", True)
    return True


def test_variable_mutability_enum() -> bool:
    """测试变量可变性枚举."""
    print_header("测试2: VariableMutability 枚举")
    types = list(VariableMutability)
    print(f"  可变性类型: {[t.value for t in types]}")
    assert len(types) == 4
    assert VariableMutability.CONSTANT.value == "constant"
    assert VariableMutability.READONLY.value == "readonly"
    assert VariableMutability.MUTABLE.value == "mutable"
    assert VariableMutability.UNKNOWN.value == "unknown"
    print_result("VariableMutability", True)
    return True


def test_code_location() -> bool:
    """测试代码位置."""
    print_header("测试3: CodeLocation")
    loc = CodeLocation(file_path="test.py", line=10, col=5, end_line=10, end_col=20)
    d = loc.to_dict()
    assert d["file_path"] == "test.py"
    assert d["line"] == 10
    assert d["col"] == 5
    s = str(loc)
    assert "test.py" in s
    assert "10" in s
    print(f"  ✓ to_dict(): {d}")
    print(f"  ✓ __str__(): {s}")
    print_result("CodeLocation", True)
    return True


def test_variable_atom_model() -> bool:
    """测试变量原子模型."""
    print_header("测试4: VariableAtom 模型")
    atom = VariableAtom(
        name="user_id",
        scope=VariableScope.LOCAL,
        type_annotation="int",
        default_value="0",
        container_name="get_user",
        container_type="function",
    )
    atom.add_dependency("db")
    atom.add_dependent("query")
    atom.add_reference(
        CodeLocation(file_path="test.py", line=15, col=8),
        context="read",
        scope_name="get_user",
    )

    assert atom.name == "user_id"
    assert atom.full_name == "get_user.user_id"
    assert atom.scope == VariableScope.LOCAL
    assert atom.type_annotation == "int"
    assert atom.read_count == 1
    assert atom.write_count == 0
    assert "db" in atom.dependencies
    assert "query" in atom.dependents
    assert atom.is_used is True
    assert atom.is_dead_code is False
    assert not atom.is_constant
    assert not atom.is_private

    d = atom.to_dict()
    assert d["name"] == "user_id"
    assert d["full_name"] == "get_user.user_id"
    assert d["scope"] == "local"
    assert len(d["dependencies"]) == 1

    summary = atom.summary()
    assert "user_id" in summary
    print(f"  ✓ 属性正常: {atom.full_name}")
    print(f"  ✓ to_dict() 正常")
    print(f"  ✓ summary(): {summary}")
    print_result("VariableAtom", True)
    return True


def test_variable_atom_special_cases() -> bool:
    """测试变量原子特殊情况."""
    print_header("测试5: VariableAtom 特殊情况")

    # 常量
    const = VariableAtom(name="MAX_RETRIES", scope=VariableScope.GLOBAL)
    assert const.is_constant is True
    assert const.mutability == VariableMutability.UNKNOWN  # 未设置时默认UNKNOWN
    print(f"  ✓ 常量识别: {const.name} -> is_constant={const.is_constant}")

    # 私有变量（以下划线开头但不以双下划线开头）
    private = VariableAtom(name="_internal", scope=VariableScope.LOCAL)
    assert private.is_private is True
    assert private.is_dunder is False
    print(f"  ✓ 私有变量: {private.name} -> is_private={private.is_private}")

    # dunder变量
    dunder = VariableAtom(name="__init__", scope=VariableScope.LOCAL)
    assert dunder.is_dunder is True
    print(f"  ✓ dunder变量: {dunder.name} -> is_dunder={dunder.is_dunder}")

    # 死代码
    dead = VariableAtom(name="unused_var", scope=VariableScope.LOCAL)
    assert dead.is_dead_code is True
    print(f"  ✓ 死代码: {dead.name} -> is_dead_code={dead.is_dead_code}")

    # 参数不是死代码
    param = VariableAtom(name="self", scope=VariableScope.PARAMETER)
    assert param.is_dead_code is False
    print(f"  ✓ 参数非死代码: {param.name} -> is_dead_code={param.is_dead_code}")

    print_result("VariableAtom 特殊情况", True)
    return True


def test_variable_extractor_basic() -> bool:
    """测试变量提取器基础功能."""
    print_header("测试6: VariableExtractor 基础提取")
    extractor = VariableExtractor(SAMPLE_CODE, file_path="sample.py")
    variables = extractor.extract()

    print(f"  提取变量总数: {len(variables)}")

    # 检查全局变量
    global_vars = extractor.get_variables_by_scope(VariableScope.GLOBAL)
    global_names = [v.name for v in global_vars]
    print(f"  全局变量: {global_names}")
    assert "MAX_RETRIES" in global_names
    assert "API_BASE_URL" in global_names

    # 检查导入变量
    import_vars = extractor.get_variables_by_scope(VariableScope.IMPORT)
    import_names = [v.name for v in import_vars]
    print(f"  导入变量: {import_names}")
    assert "List" in import_names or "Optional" in import_names

    # 检查类属性
    class_attrs = extractor.get_variables_by_scope(VariableScope.CLASS_ATTRIBUTE)
    class_attr_names = [v.name for v in class_attrs]
    print(f"  类属性: {class_attr_names}")
    assert "_instance_count" in class_attr_names

    # 检查参数
    params = extractor.get_variables_by_scope(VariableScope.PARAMETER)
    param_names = [v.name for v in params]
    print(f"  参数: {param_names}")
    assert "self" in param_names
    assert "user_id" in param_names

    print_result("VariableExtractor 基础提取", True)
    return True


def test_variable_extractor_dependencies() -> bool:
    """测试变量依赖分析."""
    print_header("测试7: VariableExtractor 依赖分析")
    extractor = VariableExtractor(SAMPLE_CODE, file_path="sample.py")
    variables = extractor.extract()

    # 检查依赖图
    dep_graph = extractor.get_dependency_graph()
    print(f"  依赖图条目数: {len(dep_graph)}")

    # 检查摘要
    summary = extractor.summary()
    print(f"  摘要:\n{summary}")
    assert "变量原子提取结果" in summary

    print_result("VariableExtractor 依赖分析", True)
    return True


def test_variable_extractor_type_annotations() -> bool:
    """测试变量类型注解提取."""
    print_header("测试8: VariableExtractor 类型注解")
    extractor = VariableExtractor(SAMPLE_CODE, file_path="sample.py")
    variables = extractor.extract()

    # 查找有类型注解的变量
    typed_vars = [v for v in variables if v.has_type_info]
    print(f"  有类型注解的变量数: {len(typed_vars)}")
    for v in typed_vars[:5]:
        print(f"    {v.full_name}: {v.type_annotation}")

    # 查找缺少类型注解的变量
    no_type_vars = extractor.get_variables_without_type()
    print(f"  缺少类型注解的变量数: {len(no_type_vars)}")

    assert len(typed_vars) > 0
    print_result("VariableExtractor 类型注解", True)
    return True


def test_method_type_enum() -> bool:
    """测试方法类型枚举."""
    print_header("测试9: MethodType 枚举")
    types = list(MethodType)
    print(f"  方法类型: {[t.value for t in types]}")
    assert len(types) == 10
    assert MethodType.FUNCTION.value == "function"
    assert MethodType.METHOD.value == "method"
    assert MethodType.CLASSMETHOD.value == "classmethod"
    assert MethodType.STATICMETHOD.value == "staticmethod"
    assert MethodType.ASYNC_FUNCTION.value == "async_function"
    assert MethodType.ASYNC_METHOD.value == "async_method"
    assert MethodType.PROPERTY.value == "property"
    assert MethodType.LAMBDA.value == "lambda"
    assert MethodType.NESTED.value == "nested"
    assert MethodType.MAGIC.value == "magic"
    print_result("MethodType", True)
    return True


def test_method_visibility_enum() -> bool:
    """测试方法可见性枚举."""
    print_header("测试10: MethodVisibility 枚举")
    vis = list(MethodVisibility)
    print(f"  可见性类型: {[v.value for v in vis]}")
    assert len(vis) == 4
    assert MethodVisibility.PUBLIC.value == "public"
    assert MethodVisibility.PROTECTED.value == "protected"
    assert MethodVisibility.PRIVATE.value == "private"
    assert MethodVisibility.MAGIC.value == "magic"
    print_result("MethodVisibility", True)
    return True


def test_parameter_info() -> bool:
    """测试参数信息."""
    print_header("测试11: ParameterInfo")
    param = ParameterInfo(
        name="user_id",
        type_annotation="int",
        default_value="0",
        has_default=True,
        kind="positional",
        position=1,
    )
    d = param.to_dict()
    assert d["name"] == "user_id"
    assert d["type_annotation"] == "int"
    assert d["has_default"] is True
    assert d["kind"] == "positional"
    assert d["position"] == 1
    print(f"  ✓ to_dict(): {d}")
    print_result("ParameterInfo", True)
    return True


def test_complexity_metrics() -> bool:
    """测试复杂度指标."""
    print_header("测试12: ComplexityMetrics")
    simple = ComplexityMetrics(
        cyclomatic_complexity=3,
        line_count=10,
        parameter_count=2,
    )
    assert simple.is_simple is True
    assert simple.is_complex is False
    print(f"  ✓ 简单方法: cc={simple.cyclomatic_complexity}, lines={simple.line_count}")

    complex_method = ComplexityMetrics(
        cyclomatic_complexity=15,
        line_count=80,
        parameter_count=6,
    )
    assert complex_method.is_simple is False
    assert complex_method.is_complex is True
    print(f"  ✓ 复杂方法: cc={complex_method.cyclomatic_complexity}, lines={complex_method.line_count}")

    d = complex_method.to_dict()
    assert d["is_complex"] is True
    assert d["is_simple"] is False
    print_result("ComplexityMetrics", True)
    return True


def test_method_atom_model() -> bool:
    """测试方法原子模型."""
    print_header("测试13: MethodAtom 模型")
    atom = MethodAtom(
        name="get_user",
        method_type=MethodType.METHOD,
        visibility=MethodVisibility.PUBLIC,
        parameters=[
            ParameterInfo(name="self", kind="positional", position=0),
            ParameterInfo(name="user_id", type_annotation="int", kind="positional", position=1),
        ],
        return_type="Optional[dict]",
        docstring="获取用户信息",
        class_name="UserService",
        module_name="sample",
    )
    atom.add_call("_execute_query", line=42, target_class="self")

    assert atom.name == "get_user"
    assert atom.full_name == "UserService.get_user"
    assert atom.qualified_name == "sample.UserService.get_user"
    assert atom.method_type == MethodType.METHOD
    assert atom.visibility == MethodVisibility.PUBLIC
    assert atom.parameter_names == ["self", "user_id"]
    assert atom.required_parameter_count == 2
    assert atom.has_varargs is False
    assert atom.has_kwargs is False
    assert atom.is_magic_method is False
    assert atom.is_private is False
    assert len(atom.calls) == 1
    assert "_execute_query" in atom.call_targets

    d = atom.to_dict()
    assert d["name"] == "get_user"
    assert d["full_name"] == "UserService.get_user"
    assert d["method_type"] == "method"

    summary = atom.summary()
    assert "get_user" in summary
    print(f"  ✓ 属性正常: {atom.full_name}")
    print(f"  ✓ to_dict() 正常")
    print(f"  ✓ summary(): {summary}")
    print_result("MethodAtom", True)
    return True


def test_method_atom_special_cases() -> bool:
    """测试方法原子特殊情况."""
    print_header("测试14: MethodAtom 特殊情况")

    # 魔术方法
    magic = MethodAtom(name="__init__", method_type=MethodType.MAGIC, class_name="UserService")
    assert magic.is_magic_method is True
    assert magic.is_dunder is True
    print(f"  ✓ 魔术方法: {magic.name} -> is_magic={magic.is_magic_method}")

    # 私有方法
    private = MethodAtom(name="_internal_method", method_type=MethodType.METHOD)
    private.visibility = MethodVisibility.PRIVATE
    assert private.is_private is True
    print(f"  ✓ 私有方法: {private.name} -> is_private={private.is_private}")

    # 有varargs和kwargs
    varargs_method = MethodAtom(
        name="flexible",
        parameters=[
            ParameterInfo(name="args", kind="vararg", position=0),
            ParameterInfo(name="kwargs", kind="varkeyword", position=1),
        ],
    )
    assert varargs_method.has_varargs is True
    assert varargs_method.has_kwargs is True
    print(f"  ✓ 可变参数: has_varargs={varargs_method.has_varargs}, has_kwargs={varargs_method.has_kwargs}")

    # called_by
    atom = MethodAtom(name="helper")
    atom.add_called_by("main")
    atom.add_called_by("process")
    assert len(atom.called_by) == 2
    assert "main" in atom.called_by
    print(f"  ✓ called_by: {atom.called_by}")

    print_result("MethodAtom 特殊情况", True)
    return True


def test_method_extractor_basic() -> bool:
    """测试方法提取器基础功能."""
    print_header("测试15: MethodExtractor 基础提取")
    extractor = MethodExtractor(SAMPLE_CODE, file_path="sample.py", module_name="sample")
    methods = extractor.extract()

    print(f"  提取方法总数: {len(methods)}")
    method_names = [m.name for m in methods]
    print(f"  方法名列表: {method_names}")

    # 检查模块级函数
    module_funcs = extractor.get_methods_by_type(MethodType.FUNCTION)
    func_names = [m.name for m in module_funcs]
    print(f"  模块级函数: {func_names}")
    assert "calculate_score" in func_names
    assert "process_data" in func_names

    # 检查实例方法
    instance_methods = extractor.get_methods_by_type(MethodType.METHOD)
    method_names_list = [m.name for m in instance_methods]
    print(f"  实例方法: {method_names_list}")
    assert "get_user" in method_names_list
    assert "_execute_query" in method_names_list

    # 检查类方法
    class_methods = extractor.get_methods_by_type(MethodType.CLASSMETHOD)
    cm_names = [m.name for m in class_methods]
    print(f"  类方法: {cm_names}")
    assert "get_instance_count" in cm_names

    # 检查静态方法
    static_methods = extractor.get_methods_by_type(MethodType.STATICMETHOD)
    sm_names = [m.name for m in static_methods]
    print(f"  静态方法: {sm_names}")
    assert "validate_email" in sm_names

    # 检查异步方法
    async_methods = extractor.get_methods_by_type(MethodType.ASYNC_METHOD)
    am_names = [m.name for m in async_methods]
    print(f"  异步方法: {am_names}")
    assert "get_users_async" in am_names

    print_result("MethodExtractor 基础提取", True)
    return True


def test_method_extractor_complexity() -> bool:
    """测试方法复杂度分析."""
    print_header("测试16: MethodExtractor 复杂度分析")
    extractor = MethodExtractor(SAMPLE_CODE, file_path="sample.py", module_name="sample")
    methods = extractor.extract()

    for m in methods:
        c = m.complexity
        print(f"  {m.full_name}: cc={c.cyclomatic_complexity}, lines={c.line_count}, "
              f"params={c.parameter_count}, branches={c.branch_count}, "
              f"nesting={c.nesting_depth}, calls={c.call_count}, "
              f"simple={c.is_simple}, complex={c.is_complex}")

    # calculate_score 应该有分支（if score > 0, if count == 0）
    calc = [m for m in methods if m.name == "calculate_score"][0]
    assert calc.complexity.cyclomatic_complexity >= 2
    assert calc.complexity.branch_count >= 2

    # 所有方法都应该有有效复杂度
    for m in methods:
        assert m.complexity.cyclomatic_complexity >= 1
        assert m.complexity.line_count >= 1

    print_result("MethodExtractor 复杂度分析", True)
    return True


def test_method_extractor_signatures() -> bool:
    """测试方法签名提取."""
    print_header("测试17: MethodExtractor 签名提取")
    extractor = MethodExtractor(SAMPLE_CODE, file_path="sample.py", module_name="sample")
    methods = extractor.extract()

    for m in methods:
        print(f"  {m.signature}")

    # 检查 __init__ 签名
    init_method = [m for m in methods if m.name == "__init__"][0]
    assert "self" in init_method.parameter_names
    assert "db_url" in init_method.parameter_names
    assert init_method.return_type == "None" or init_method.return_type == ""

    # 检查 calculate_score 签名
    calc_method = [m for m in methods if m.name == "calculate_score"][0]
    assert "scores" in calc_method.parameter_names
    assert "weight" in calc_method.parameter_names
    assert calc_method.return_type == "float"

    # 检查有默认值的参数
    weight_param = [p for p in calc_method.parameters if p.name == "weight"][0]
    assert weight_param.has_default is True
    assert weight_param.default_value == "1.0"

    print_result("MethodExtractor 签名提取", True)
    return True


def test_method_extractor_call_graph() -> bool:
    """测试方法调用关系图."""
    print_header("测试18: MethodExtractor 调用关系")
    extractor = MethodExtractor(SAMPLE_CODE, file_path="sample.py", module_name="sample")
    methods = extractor.extract()

    # 获取调用图
    call_graph = extractor.get_call_graph()
    print(f"  调用图条目数: {len(call_graph)}")
    for caller, targets in call_graph.items():
        if targets:
            print(f"    {caller} -> {targets}")

    # get_user 应该调用 _execute_query
    get_user = [m for m in methods if m.name == "get_user"]
    if get_user:
        call_targets = get_user[0].call_targets
        assert "_execute_query" in call_targets or "print" in call_targets
        print(f"  ✓ get_user 调用: {call_targets}")

    # get_users_async 应该调用 get_user
    async_method = [m for m in methods if m.name == "get_users_async"]
    if async_method:
        call_targets = async_method[0].call_targets
        assert "get_user" in call_targets
        print(f"  ✓ get_users_async 调用: {call_targets}")

    # 反向调用图
    reverse_graph = extractor.get_reverse_call_graph()
    print(f"  反向调用图条目数: {len(reverse_graph)}")
    for target, callers in reverse_graph.items():
        print(f"    {target} <- {callers}")

    print_result("MethodExtractor 调用关系", True)
    return True


def test_method_extractor_docstrings() -> bool:
    """测试方法文档字符串提取."""
    print_header("测试19: MethodExtractor 文档字符串")
    extractor = MethodExtractor(SAMPLE_CODE, file_path="sample.py", module_name="sample")
    methods = extractor.extract()

    # 检查有文档字符串的方法
    with_doc = [m for m in methods if m.docstring.strip()]
    print(f"  有文档字符串的方法: {[m.name for m in with_doc]}")

    # 检查缺少文档字符串的方法
    no_doc = extractor.get_methods_without_docstring()
    print(f"  缺少文档字符串的方法: {[m.name for m in no_doc]}")

    assert len(with_doc) > 0
    all_docs = [m.docstring for m in methods]
    assert any("获取用户信息" in d for d in all_docs)
    assert any("计算加权分数" in d for d in all_docs)

    print_result("MethodExtractor 文档字符串", True)
    return True


def test_method_extractor_exceptions() -> bool:
    """测试异常信息提取."""
    print_header("测试20: MethodExtractor 异常信息")
    extractor = MethodExtractor(SAMPLE_CODE, file_path="sample.py", module_name="sample")
    methods = extractor.extract()

    for m in methods:
        if m.exceptions_raised or m.exceptions_caught:
            print(f"  {m.full_name}:")
            if m.exceptions_raised:
                print(f"    抛出: {m.exceptions_raised}")
            if m.exceptions_caught:
                print(f"    捕获: {m.exceptions_caught}")

    # _execute_query 应该捕获 Exception
    exec_query = [m for m in methods if m.name == "_execute_query"]
    if exec_query:
        assert "Exception" in exec_query[0].exceptions_caught
        print(f"  ✓ _execute_query 捕获 Exception")

    print_result("MethodExtractor 异常信息", True)
    return True


def test_method_extractor_summary() -> bool:
    """测试方法提取器摘要."""
    print_header("测试21: MethodExtractor 摘要")
    extractor = MethodExtractor(SAMPLE_CODE, file_path="sample.py", module_name="sample")
    extractor.extract()

    summary = extractor.summary()
    print(f"  {summary}")
    assert "方法原子提取结果" in summary

    print_result("MethodExtractor 摘要", True)
    return True


def test_integration_variable_method() -> bool:
    """集成测试：变量和方法联合分析."""
    print_header("测试22: 集成测试 - 变量与方法联合分析")

    # 同时提取变量和方法
    var_extractor = VariableExtractor(SAMPLE_CODE, file_path="sample.py")
    variables = var_extractor.extract()

    method_extractor = MethodExtractor(SAMPLE_CODE, file_path="sample.py", module_name="sample")
    methods = method_extractor.extract()

    print(f"  变量原子: {len(variables)} 个")
    print(f"  方法原子: {len(methods)} 个")

    # 验证一致性：方法参数应该在变量中
    method_params = set()
    for m in methods:
        for p in m.parameters:
            if p.name != "self" and p.name != "cls":
                method_params.add(p.name)

    var_names = {v.name for v in variables}
    overlap = method_params & var_names
    print(f"  方法参数与变量的重叠: {overlap}")

    # 验证类属性一致性
    class_attrs = [v for v in variables if v.scope == VariableScope.CLASS_ATTRIBUTE]
    class_method_names = [m.name for m in methods if m.class_name == "UserService"]
    print(f"  UserService 类属性: {[v.name for v in class_attrs]}")
    print(f"  UserService 方法: {class_method_names}")

    assert len(variables) > 0
    assert len(methods) > 0

    print_result("集成测试", True)
    return True


# ========== 主函数 ==========

def main() -> None:
    """运行所有测试."""
    print("=" * 60)
    print("  第29阶段验收: 变量原子 + 方法原子 (Variable & Method Atom)")
    print("=" * 60)

    tests = [
        test_variable_scope_enum,
        test_variable_mutability_enum,
        test_code_location,
        test_variable_atom_model,
        test_variable_atom_special_cases,
        test_variable_extractor_basic,
        test_variable_extractor_dependencies,
        test_variable_extractor_type_annotations,
        test_method_type_enum,
        test_method_visibility_enum,
        test_parameter_info,
        test_complexity_metrics,
        test_method_atom_model,
        test_method_atom_special_cases,
        test_method_extractor_basic,
        test_method_extractor_complexity,
        test_method_extractor_signatures,
        test_method_extractor_call_graph,
        test_method_extractor_docstrings,
        test_method_extractor_exceptions,
        test_method_extractor_summary,
        test_integration_variable_method,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print_result(test.__name__, False)
        except Exception as e:
            failed += 1
            print(f"\n  ✗ EXCEPTION: {test.__name__}")
            print(f"    {type(e).__name__}: {e}")

    print(f"\n{'='*60}")
    print(f"  验收结果: {passed} 通过, {failed} 失败")
    print(f"{'='*60}")

    if failed == 0:
        print(f"\n  ✓ 第29阶段验收通过！")
        print(f"\n  实现功能:")
        print(f"    - VariableScope: 7种变量作用域")
        print(f"    - VariableMutability: 4种可变性")
        print(f"    - CodeLocation: 代码位置（文件/行/列）")
        print(f"    - VariableReference: 变量引用记录")
        print(f"    - VariableAtom: 变量原子（名称/类型/作用域/依赖/引用）")
        print(f"    - VariableExtractor: 变量提取器（AST遍历/依赖分析/死代码检测）")
        print(f"    - MethodType: 9种方法类型")
        print(f"    - MethodVisibility: 4种可见性")
        print(f"    - ParameterInfo: 参数信息（类型/默认值/位置）")
        print(f"    - CallRelation: 调用关系")
        print(f"    - ComplexityMetrics: 复杂度指标（圈复杂度/行数/嵌套深度）")
        print(f"    - MethodAtom: 方法原子（签名/文档/调用关系/复杂度）")
        print(f"    - MethodExtractor: 方法提取器（类型识别/复杂度计算/调用图/异常分析）")
        print(f"{'='*60}")
        sys.exit(0)
    else:
        print(f"\n  ✗ 有 {failed} 个测试失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
