"""变量原子模块 - 阶段29.

第一级代码原子化：变量原子（Variable Atom）

提供：
- VariableAtom: 变量原子数据模型
- VariableExtractor: 变量提取器
- VariableScope: 变量作用域枚举
- VariableMutability: 变量可变性枚举
- CodeLocation: 代码位置
- VariableReference: 变量引用记录
"""

from multi_agent_se.atomicity.variable.models import (
    CodeLocation,
    VariableAtom,
    VariableMutability,
    VariableReference,
    VariableScope,
)
from multi_agent_se.atomicity.variable.extractor import VariableExtractor

__all__ = [
    # 模型
    "VariableAtom",
    "VariableScope",
    "VariableMutability",
    "CodeLocation",
    "VariableReference",
    # 提取器
    "VariableExtractor",
]
