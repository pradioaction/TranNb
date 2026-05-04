# TransNb - 翻译笔记本

一个功能强大的桌面翻译和学习应用，基于 PyQt5 开发，集成 AI 翻译、Markdown 编辑、工作区管理和完整的单词背诵系统。

## 🌟 核心功能

### 📝 翻译编辑器

- **Markdown 单元格**：使用单元格组织内容，支持 Markdown 编辑和预览
- **智能段落分割**：导入文本文件时自动按段落分割
- **单个/批量翻译**：支持翻译当前选中单元格或所有单元格
- **编辑/阅读模式**：双击切换编辑和阅读模式
- **单元格折叠**：支持单元格、原文、译文分别折叠
- **快捷键支持**：Ctrl+Enter 翻译、Ctrl+N 新建等

### 🌐 AI 翻译服务

- **多种翻译提供者**：
  - Ollama 本地模型
  - 火山引擎方舟
  - OpenAI 兼容 API
  - 自定义配置的提供者
- **灵活的模型配置**：支持自定义模型、API 端点、超时设置
- **可自定义的提示词模板**：根据需求调整翻译提示词
- **热重载配置**：无需重启即可更新翻译提供者配置

### 📚 背诵模式 - 单词学习系统

- **艾宾浩斯遗忘曲线**：科学的复习间隔算法
- **词书管理**：导入、管理多本词书
- **每日学习计划**：自定义每日新学和复习单词数量
- **文章生成**：AI 生成包含今日单词的场景文章
- **单词检测**：自测功能，记录学习效果
- **学习进度追踪**：实时查看词书学习进度和统计
- **单词仓库：<https://github.com/KyleBing/english-vocabulary.git>**

### 🗂️ 工作区管理

- **文件浏览器**：树形结构浏览文件
- **工作区隔离**：每个工作区有独立的数据和配置
- **.transnb 格式**：专用的翻译笔记本文件格式
- **最近文件记录**：快速访问最近打开的文件

### 🎨 主题与界面

- **浅色/深色主题**：一键切换，保护视力
- **现代化界面**：简洁美观的 UI 设计
- **自适应布局**：窗口大小可调节，布局自适应
- **状态栏提示**：实时显示操作状态

## 🚀 快速开始

### 系统要求

- Python 3.14+
- Windows 操作系统

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行应用

```bash
python main.py
```

或在 Windows 上直接运行 `transnb.bat`

## 📖 使用指南

### 翻译模式

1. **新建文件**：点击菜单「文件 > 新建」或按 Ctrl+N
2. **导入文本**：点击「文件 > 导入文本」选择 .txt/.md/.html 文件
3. **编辑内容**：在单元格中输入或编辑文本
4. **翻译**：点击单元格左侧翻译按钮，或按 Ctrl+Enter
5. **保存**：按 Ctrl+S 保存为 .transnb 文件

### 背诵模式

1. **打开背诵模式**：点击菜单「背诵模式 > 打开背诵模式」或按 Ctrl+Shift+B
2. **导入词书**：点击导入按钮，选择 JSON 格式的词书
3. **选择词书**：从列表中选择要学习的词书
4. **设置每日计划**：在设置中调整每日新学和复习数量
5. **开始学习**：查看今日单词，生成文章或开始检测

### 配置翻译服务

1. **打开设置**：点击菜单「设置 > 打开设置」
2. **选择提供者**：在翻译设置中选择翻译提供者
3. **配置模型**：设置 API 密钥、模型名称、端点等
4. **测试连接**：点击测试按钮验证配置是否正确
5. **保存设置**：点击确定保存配置

## 📁 项目结构

```
transnb/
├── main.py                      # 应用入口
├── requirements.txt             # 依赖列表
├── settings.json                # 配置文件
├── README.md                    # 本文件
├── ARCHITECTURE.md              # 架构文档
├── API.md                       # API 文档
├── 单元格.md                    # 单元格文档
└── src/
    ├── ui/                      # 主窗口模块化设计
    │   ├── main_window.py       # 主窗口核心类
    │   ├── main_window_ui.py    # UI 初始化
    │   ├── main_window_actions.py  # 动作处理
    │   ├── main_window_menus.py    # 菜单管理
    │   ├── main_window_file_ops.py # 文件操作
    │   ├── main_window_recitation.py # 背诵模式集成
    │   └── main_window_workers.py   # 后台工作线程
    ├── cells/                   # 单元格模块（工厂模式）
    │   ├── widgets/             # 单元格 UI 组件
    │   ├── cell_factory.py      # 单元格工厂
    │   ├── cell_signal_manager.py # 信号管理器
    │   ├── cell_height_calculator.py # 高度计算器
    │   ├── cell_manager.py      # 单元格管理器
    │   └── markdown_cell.py     # Markdown 单元格
    ├── components/              # UI 组件
    │   └── settings_panels/     # 设置面板
    ├── translation/             # 翻译模块（策略模式）
    │   ├── providers/           # 翻译提供者
    │   │   ├── base.py          # 提供者基类
    │   │   ├── ollama.py        # Ollama 提供者
    │   │   ├── ark.py           # 火山引擎方舟提供者
    │   │   ├── openai_provider.py # OpenAI 兼容提供者
    │   │   ├── custom_factory.py # 自定义提供者工厂
    │   │   └── api_key_resolve.py # API 密钥解析
    │   ├── modes/               # 翻译模式
    │   └── translation_service.py # 翻译服务
    ├── workspace/               # 工作区模块
    ├── settingmanager/          # 设置管理（单例模式）
    ├── recitation/              # 背诵模式模块
    │   ├── dal/                 # 数据访问层（模块化）
    │   │   ├── book_dal.py      # 词书 DAL
    │   │   ├── word_dal.py      # 单词 DAL
    │   │   ├── user_study_dal.py # 用户学习记录 DAL
    │   │   └── stat_dal.py      # 统计 DAL
    │   ├── models.py            # 数据模型
    │   ├── ebbinghaus.py        # 艾宾浩斯算法
    │   ├── study_service.py     # 学习服务
    │   └── ui/                  # 背诵模式 UI
    └── utils/                   # 工具模块
```

## 🛠️ 技术栈

- **GUI 框架**：PyQt5
- **Markdown 渲染**：markdown 库
- **HTTP 请求**：httpx
- **数据格式**：JSON
- **数据库**：SQLite
- **AI 服务**：Ollama、火山引擎方舟、OpenAI 兼容 API

## 📝 文件格式

### .transnb 文件

翻译笔记本使用自定义的 JSON 格式存储，包含：

```json
{
  "cells": [
    {
      "type": "markdown",
      "content": "源文本",
      "output": "翻译结果"
    }
  ]
}
```

### 词书格式

支持导入 KyleBing 格式的 JSON 词书，包含单词、音标、释义、例句等字段。

## 🎯 快捷键

| 快捷键              | 功能                       |
| ---------------- | ------------------------ |
| Ctrl+N           | 新建文件                     |
| Ctrl+O           | 打开文件                     |
| Ctrl+K           | 打开文件夹（工作区）               |
| Ctrl+I           | 导入文本                     |
| Ctrl+S           | 保存文件                     |
| Ctrl+Enter       | 翻译当前单元格                  |
| Ctrl+A           | 上方插入单元格                  |
| Ctrl+B           | 下方插入单元格                  |
| Delete           | 删除选中单元格                  |
| Ctrl+Shift+B     | 打开背诵模式                   |
| Ctrl+Z           | 撤销（预留）                   |
| Ctrl+Y           | 重做（预留）                   |
| **Ctrl+Shift+Q** | **全部折叠/展开原文**            |
| **Ctrl+Shift+W** | **全部折叠/展开结果**            |
| **Ctrl+Q**       | **选中折叠/展开原文**            |
| **Ctrl+W**       | **选中折叠/展开结果**            |
| **Shift+↑**      | **向上多选单元格 (未完成/BUGING)** |
| **Shift+↓**      | **向下多选单元格 (未完成/BUGING)** |
| **Shift+点击**     | **按住Shift点击鼠标多选单元格**     |

## 📚 相关文档

- [架构文档](./ARCHITECTURE.md) - 详细的系统架构和设计
- [API 文档](./API.md) - API 接口说明

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

感谢所有为本项目做出贡献的开发者！

***

**享受翻译和学习的乐趣！** 🎉
