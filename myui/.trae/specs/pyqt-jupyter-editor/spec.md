# PyQt Jupyter 风格编辑器 - 产品需求文档

## Overview
- **Summary**: 基于 PyQt 框架开发的桌面端交互式代码编辑器，复刻 Jupyter Notebook 核心体验，支持单元格化编辑、代码运行、Markdown 渲染和文件管理。
- **Purpose**: 提供一个轻量化、桌面原生、无浏览器依赖的交互式编程环境，让用户能够以 Jupyter 风格进行代码编写和数据分析。
- **Target Users**: 数据科学家、Python 开发者、学生和教育工作者。

## Goals
- 实现 Jupyter 风格的单元格系统（代码/Markdown）
- 支持 Python 代码运行和多类型输出展示
- 提供完整的文件管理功能
- 实现流畅的用户体验和响应式界面
- 保证跨平台兼容性

## Non-Goals (Out of Scope)
- 多内核支持（Python/Julia/R）- 进阶需求
- 代码调试功能（单步运行、断点）- 进阶需求
- 云端同步/版本管理 - 进阶需求
- 协同编辑功能 - 进阶需求

## Background & Context
- Jupyter Notebook 是数据分析领域广泛使用的交互式编程工具
- 浏览器依赖和启动速度限制了其在某些场景的使用
- PyQt 提供原生桌面体验，性能更好，响应更快
- 用户需要一个轻量化的桌面替代方案

## Functional Requirements
- **FR-1**: 支持代码单元格和 Markdown 单元格两种类型
- **FR-2**: 支持单元格的增删改查和移动操作
- **FR-3**: 支持代码运行控制（运行当前/全部/至当前，停止运行）
- **FR-4**: 代码编辑器支持语法高亮、自动缩进、括号匹配
- **FR-5**: 支持代码补全和代码格式化
- **FR-6**: 支持多种输出类型（文本、错误、图片、图表）
- **FR-7**: Markdown 渲染支持标题、列表、加粗、斜体、链接
- **FR-8**: 文件管理支持新建、打开、保存、另存为
- **FR-9**: 支持快捷键操作（运行、切换类型等）
- **FR-10**: 状态栏显示内核状态和运行信息

## Non-Functional Requirements
- **NFR-1**: 100+ 单元格流畅滚动，无卡顿
- **NFR-2**: 代码运行不阻塞 UI 主线程
- **NFR-3**: 内核崩溃不导致主程序崩溃
- **NFR-4**: 支持 Windows 10/11、macOS、Linux 跨平台
- **NFR-5**: 支持浅色/深色主题切换
- **NFR-6**: 启动时间 < 2 秒

## Constraints
- **Technical**: PyQt 6.4+ / PySide6, QScintilla, Python 3.8+
- **Business**: 独立桌面应用，无需服务器端支持
- **Dependencies**: Matplotlib, Markdown 解析库

## Assumptions
- 用户具备基本的 Python 编程知识
- 用户熟悉 Jupyter Notebook 操作习惯
- 系统已安装 Python 环境

## Acceptance Criteria

### AC-1: 单元格类型切换
- **Given**: 用户选中一个单元格
- **When**: 用户点击切换类型按钮或使用快捷键
- **Then**: 单元格在代码和 Markdown 类型之间切换
- **Verification**: `programmatic`

### AC-2: 单元格运行
- **Given**: 存在代码单元格
- **When**: 用户点击运行按钮或使用 Ctrl+Enter
- **Then**: 代码执行并在下方显示输出结果
- **Verification**: `programmatic`

### AC-3: Markdown 渲染
- **Given**: Markdown 单元格包含标题、列表、加粗文本
- **When**: 切换到预览模式或运行单元格
- **Then**: 正确渲染富文本格式
- **Verification**: `human-judgment`

### AC-4: 多单元格滚动
- **Given**: 文档包含 100+ 单元格
- **When**: 用户滚动文档
- **Then**: 滚动流畅，无明显卡顿
- **Verification**: `human-judgment`

### AC-5: 代码运行不阻塞 UI
- **Given**: 执行耗时 5 秒的代码
- **When**: 代码运行期间操作 UI
- **Then**: UI 响应正常，可进行其他操作
- **Verification**: `programmatic`

### AC-6: 文件保存与打开
- **Given**: 用户编辑文档后保存
- **When**: 用户关闭并重新打开应用
- **Then**: 文档内容完整恢复
- **Verification**: `programmatic`

### AC-7: 内核崩溃处理
- **Given**: 代码导致 Python 内核崩溃
- **When**: 内核崩溃后
- **Then**: 主程序保持运行，提示用户重启内核
- **Verification**: `programmatic`

### AC-8: 快捷键支持
- **Given**: 用户使用 Ctrl+Enter
- **When**: 选中代码单元格
- **Then**: 当前单元格执行，光标停留在原单元格
- **Verification**: `programmatic`

### AC-9: 图片输出展示
- **Given**: 代码包含 Matplotlib 绘图
- **When**: 运行代码单元格
- **Then**: 图表正确渲染在输出区域
- **Verification**: `human-judgment`

### AC-10: 深色主题切换
- **Given**: 用户在设置中切换主题
- **When**: 选择深色主题
- **Then**: 整个界面切换为深色配色
- **Verification**: `human-judgment`

## Open Questions
- [ ] 是否需要支持 ipynb 文件导入导出？
- [ ] 是否需要实现变量浏览器功能？
- [ ] 是否需要支持代码格式化功能？
