# 多Agent软件工程系统 (Multi-Agent SE)

> 基于第一性原理 + 开源复用的轻量化多Agent软件工程系统

## 🎯 核心设计理念

### 第一性原理（6大公理）
1. **任务可分性公理**：复杂任务可拆解至不可再分原子动作
2. **依赖单向性公理**：整体架构与代码结构保持有向无环DAG
3. **信息最小熵公理**：消除隐式状态、隐式逻辑，信息全显式可追溯
4. **职责正交公理**：Agent职责无重叠、无空缺，分工互补无冲突
5. **状态分离公理**：业务、任务、系统三层状态隔离管控
6. **成本最小公理**：按需选用组件，剔除冗余能力，精简整体架构

### 开源复用原则
- ✅ **完全直接复用**：AutoGen、LangGraph、MetaGPT、Tree-sitter、Ruff、Pytest
- ✅ **轻量封装适配**：正交Agent职责绑定、四级原子化规则、工程流程拓扑
- ❌ **绝不重复开发**：通信内核、状态机引擎、语法解析器、算法数学逻辑

## 📁 项目结构（四级原子化）

```
multi_agent_se/
├── src/multi_agent_se/              # 主代码目录
│   ├── core/                        # 核心底座（阶段1-10）
│   │   ├── config/                  # 配置管理
│   │   ├── logging/                 # 日志管理
│   │   ├── exceptions/              # 异常处理
│   │   ├── paths/                   # 路径管理
│   │   ├── config.py                # 全局配置
│   │   └── dependency_graph.py      # 单向依赖图（DAG）
│   │
│   ├── agents/                      # 8大Agent实现（阶段31-40）
│   │   ├── controller/              # 总控Agent
│   │   ├── requirement/             # 需求拆解Agent
│   │   ├── architect/               # 架构Agent
│   │   ├── developer/               # 开发Agent
│   │   ├── bugfix/                  # 缺陷排查Agent
│   │   ├── reviewer/                # 评审Agent
│   │   ├── tester/                  # 测试Agent
│   │   └── documenter/              # 文档Agent
│   │
│   ├── atomicity/                   # 四级代码原子化（阶段21-30）
│   │   ├── variable/                # 变量原子
│   │   ├── method/                  # 方法原子
│   │   ├── class_atom/              # 类原子
│   │   └── module_atom/             # 模块原子
│   │
│   ├── collaboration/               # 核心协作算法（阶段41-50）
│   │   ├── scheduler/               # 调度器
│   │   ├── dispatcher/              # 分发器
│   │   ├── negotiator/              # 协商器
│   │   └── algorithm/               # 协作算法
│   │
│   ├── pipeline/                    # 工程流水线（阶段51-60）
│   │   ├── stages/                  # 流水线阶段
│   │   ├── branches/                # 流水线分支
│   │   └── workflow/                # 工作流
│   │
│   ├── quality/                     # 质量与安全（阶段71-80）
│   │   ├── linter/                  # 代码检查
│   │   ├── security/                # 安全扫描
│   │   ├── coverage/                # 覆盖率分析
│   │   └── metrics/                 # 质量指标
│   │
│   └── utils/                       # 工具函数
│       ├── helpers/                 # 辅助函数
│       ├── validators/              # 验证器
│       └── converters/              # 转换器
│
├── tests/                           # 测试目录
│   ├── unit/                        # 单元测试
│   │   ├── core/
│   │   ├── agents/
│   │   ├── atomicity/
│   │   ├── collaboration/
│   │   ├── pipeline/
│   │   └── quality/
│   └── integration/                 # 集成测试
│       ├── pipeline/
│       └── agents/
│
├── config/                          # 配置文件
│   ├── agents/                      # Agent配置
│   ├── atomicity/                   # 原子化规则配置
│   ├── pipeline/                    # 流水线配置
│   └── quality/                     # 质量门禁配置
│
├── docs/                            # 文档
│   ├── architecture/                # 架构文档
│   ├── agents/                      # Agent文档
│   ├── api/                         # API文档
│   └── guides/                      # 使用指南
│
├── scripts/                         # 脚本工具
│   ├── setup/                       # 安装脚本
│   ├── verify/                      # 验收脚本
│   └── deploy/                      # 部署脚本
│
├── requirements.txt                 # 依赖锁定
└── pyproject.toml                   # 项目配置
```

## 🔄 单向依赖关系（DAG）

遵循第一性原理的**依赖单向性公理**，系统采用四层架构：

```
输入收敛层 (Layer 3)
      ↓
调度中枢层 (Layer 2)
      ↓
智能协作层 (Layer 1)
      ↓
原子执行层 (Layer 0)
```

**依赖规则**：
- 上层可依赖下层
- 下层不可依赖上层
- 同层模块不可相互依赖
- 整体形成有向无环图（DAG）

## 🚀 快速开始

### 环境要求
- Python 3.10+
- pip 25+

### 安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\\Scripts\\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 开发模式安装
pip install -e ".[dev]"
```

### 验证安装

```bash
# 运行验收脚本
python scripts/verify_phase1.py
python scripts/verify_phase2.py
```

## 📊 100阶段实施计划

| 阶段组 | 范围 | 核心目标 | 状态 |
|--------|------|----------|------|
| 第一组 | 1-10 | 环境与底座搭建 | ✅ 1-2完成 |
| 第二组 | 11-20 | 架构层约束落地 | ⏳ 待开始 |
| 第三组 | 21-30 | 四级代码原子化体系 | ⏳ 待开始 |
| 第四组 | 31-40 | 8大Agent基础实例化 | ⏳ 待开始 |
| 第五组 | 41-50 | 核心协作算法落地 | ⏳ 待开始 |
| 第六组 | 51-60 | 标准工程流水线闭环 | ⏳ 待开始 |
| 第七组 | 61-70 | 专项工程能力落地 | ⏳ 待开始 |
| 第八组 | 71-80 | 质量与安全体系 | ⏳ 待开始 |
| 第九组 | 81-90 | 自动化&智能化增强 | ⏳ 待开始 |
| 第十组 | 91-100 | 上线、稳定、自进化 | ⏳ 待开始 |

## 🔧 技术栈

### 核心开源组件
- **调度引擎**：LangGraph
- **多智能体交互**：AutoGen
- **工程流程模板**：MetaGPT
- **代码处理**：Tree-sitter + AST工具 + Ruff
- **测试组件**：Pytest
- **图算法**：NetworkX

## 📜 许可证

MIT License
