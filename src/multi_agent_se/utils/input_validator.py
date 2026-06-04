"""输入验证器 - 第45阶段.

为所有Agent提供统一的输入验证能力，遵循第一性原理：
- 原子性：每个验证规则独立
- 正交性：验证与业务逻辑分离
- 最小熵：统一错误格式
"""

from typing import Any, Dict, List, Optional, Tuple, Union


class ValidationError:
    """验证错误."""
    
    def __init__(self, field: str, expected: str, actual: Any) -> None:
        self.field = field
        self.expected = expected
        self.actual_type = type(actual).__name__ if actual is not None else "None"
        self.actual_value = str(actual)[:50] if actual is not None else "None"
    
    def __str__(self) -> str:
        return f"字段 '{self.field}' 期望类型 {self.expected}，实际为 {self.actual_type} (值: {self.actual_value})"


class InputValidator:
    """输入验证器.
    
    统一验证Agent输入数据，确保类型安全和边界正确。
    """
    
    @staticmethod
    def validate_dict(input_data: Any, field_name: str = "input_data") -> Tuple[bool, Optional[str]]:
        """验证输入是否为字典.
        
        Args:
            input_data: 待验证数据
            field_name: 字段名称（用于错误信息）
            
        Returns:
            (是否有效, 错误信息)
        """
        if not isinstance(input_data, dict):
            return False, f"{field_name} 必须是字典类型，实际为 {type(input_data).__name__}"
        return True, None
    
    @staticmethod
    def validate_string(value: Any, field_name: str, allow_none: bool = False) -> Tuple[bool, Optional[str]]:
        """验证字符串类型.
        
        Args:
            value: 待验证值
            field_name: 字段名称
            allow_none: 是否允许None
            
        Returns:
            (是否有效, 错误信息)
        """
        if value is None and allow_none:
            return True, None
        if not isinstance(value, str):
            return False, f"{field_name} 必须是字符串类型，实际为 {type(value).__name__}"
        return True, None
    
    @staticmethod
    def validate_list(value: Any, field_name: str, allow_empty: bool = True, allow_none: bool = False) -> Tuple[bool, Optional[str]]:
        """验证列表类型.
        
        Args:
            value: 待验证值
            field_name: 字段名称
            allow_empty: 是否允许空列表
            allow_none: 是否允许None
            
        Returns:
            (是否有效, 错误信息)
        """
        if value is None and allow_none:
            return True, None
        if not isinstance(value, list):
            return False, f"{field_name} 必须是列表类型，实际为 {type(value).__name__}"
        if not allow_empty and len(value) == 0:
            return False, f"{field_name} 不能为空列表"
        return True, None
    
    @staticmethod
    def validate_int(value: Any, field_name: str, min_value: Optional[int] = None, max_value: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """验证整数类型及范围.
        
        Args:
            value: 待验证值
            field_name: 字段名称
            min_value: 最小值
            max_value: 最大值
            
        Returns:
            (是否有效, 错误信息)
        """
        if not isinstance(value, int) or isinstance(value, bool):
            return False, f"{field_name} 必须是整数类型，实际为 {type(value).__name__}"
        if min_value is not None and value < min_value:
            return False, f"{field_name} 必须 >= {min_value}，实际为 {value}"
        if max_value is not None and value > max_value:
            return False, f"{field_name} 必须 <= {max_value}，实际为 {value}"
        return True, None
    
    @staticmethod
    def validate_enum(value: Any, field_name: str, allowed_values: List[str]) -> Tuple[bool, Optional[str]]:
        """验证枚举值.
        
        Args:
            value: 待验证值
            field_name: 字段名称
            allowed_values: 允许的值列表
            
        Returns:
            (是否有效, 错误信息)
        """
        if value not in allowed_values:
            return False, f"{field_name} 必须是 {allowed_values} 之一，实际为 '{value}'"
        return True, None
    
    @classmethod
    def validate_agent_input(
        cls,
        input_data: Any,
        required_fields: Optional[Dict[str, str]] = None,
        optional_fields: Optional[Dict[str, str]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """验证Agent输入数据.
        
        Args:
            input_data: 输入数据
            required_fields: 必填字段 {字段名: 类型}
            optional_fields: 可选字段 {字段名: 类型}
            
        Returns:
            (是否有效, 错误信息)
        """
        # 1. 验证顶层类型
        valid, error = cls.validate_dict(input_data)
        if not valid:
            return valid, error
        
        # 2. 验证必填字段
        if required_fields:
            for field_name, field_type in required_fields.items():
                if field_name not in input_data:
                    return False, f"缺少必填字段 '{field_name}'"
                
                value = input_data[field_name]
                type_validators = {
                    "str": cls.validate_string,
                    "list": cls.validate_list,
                    "int": cls.validate_int,
                    "dict": lambda v, fn: cls.validate_dict(v, fn),
                }
                
                validator = type_validators.get(field_type)
                if validator:
                    valid, error = validator(value, field_name)
                    if not valid:
                        return valid, error
        
        # 3. 验证可选字段（如果存在）
        if optional_fields:
            for field_name, field_type in optional_fields.items():
                if field_name in input_data and input_data[field_name] is not None:
                    value = input_data[field_name]
                    type_validators = {
                        "str": cls.validate_string,
                        "list": cls.validate_list,
                        "int": cls.validate_int,
                        "dict": lambda v, fn: cls.validate_dict(v, fn),
                    }
                    
                    validator = type_validators.get(field_type)
                    if validator:
                        valid, error = validator(value, field_name)
                        if not valid:
                            return valid, error
        
        return True, None
