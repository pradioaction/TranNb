# 翻译笔记本 软件架构文档

## 1. 项目概述

翻译笔记本是一个基于 PyQt5 的桌面应用程序，用于管理和翻译文本内容，支持 Markdown 编辑、AI 翻译（通过 Ollama 本地模型）、工作区管理和文本导入功能。

### 技术栈

- **GUI 框架**: PyQt5
- **Markdown 渲染**: markdown 库
- **HTTP 请求**: httpx
- **数据格式**: JSON
- **Python 版本**: 3.14+
- **其他依赖**: PyQt5-Qsci, matplotlib, numpy

---

## 2. 系统架构

### 2.1 整体架构图

```
翻译笔记本应用
├── 主入口 (main.py)
└── 核心模块 (src/)
    ├── UI 层
    │   ├── MainWindow (主窗口)
    │   ├── WelcomePage (欢迎页)
    │   ├── SettingsDialog (设置对话框)
    │   └── 背诵模式 UI
    │       ├── RecitationMainPage (背诵模式主页)
    │       ├── QuizPage (测验页面)
    │       └── RecitationSettingsPanel (背诵模式设置面板)
    ├── 业务逻辑层
    │   ├── TranslationService (翻译服务)
    │   ├── CellManager (单元格管理器)
    │   ├── WorkspaceManager (工作区管理器)
    │   ├── FileService (文件服务)
    │   └── 背诵模式服务
    │       ├── BookService (词书管理服务)
    │       └── StudyService (学习服务)
    ├── 数据层
    │   ├── SettingsManager (设置管理器)
    │   ├── BaseCell (单元格基类)
    │   ├── MarkdownCell (Markdown单元格)
    │   └── 背诵模式数据层
    │       ├── DatabaseManager (数据库管理)
    │       └── RecitationDAL (数据访问层)
    ├── 翻译模块
    │   ├── BaseTranslationProvider (翻译提供者基类)
    │   ├── OllamaTranslationProvider (Ollama翻译)
    │   └── TranslationWorker (翻译工作线程)
    ├── 背诵模式模块
    │   ├── 数据模型
    │   │   ├── Book (词书)
    │   │   ├── Word (单词)
    │   │   └── UserStudy (学习记录)
    │   ├── 辅助组件
    │   │   ├── PathManager (路径管理)
    │   │   ├── BookImporter (词书导入)
    │   │   ├── ArticleGenerator (文章生成器)
    │   │   ├── EbbinghausAlgorithm (艾宾浩斯算法)
    │   │   └── DownloadService (下载服务)
    │   └── 工作线程 (workers)
    └── 工具层
        ├── ThemeManager (主题管理)
        ├── FileUtils (文件工具)
        └── SizeCalculator (尺寸计算)
```

### 2.2 层次结构

| 层次 | 职责 | 主要类 |
|------|------|--------|
| 表现层 (UI) | 用户界面展示和交互 | MainWindow, WelcomePage, SettingsDialog, RecitationMainPage, QuizPage |
| 业务逻辑层 | 核心业务逻辑处理 | TranslationService, CellManager, FileService, WorkspaceManager, BookService, StudyService |
| 数据层 | 数据持久化和管理 | SettingsManager, DatabaseManager, RecitationDAL |
| 翻译层 | 翻译能力提供 | BaseTranslationProvider, OllamaTranslationProvider |
| 背诵模式层 | 单词背诵和学习管理 | Book, Word, UserStudy, BookImporter, ArticleGenerator, EbbinghausAlgorithm |
| 工具层 | 通用工具和辅助功能 | ThemeManager, FileUtils, SizeCalculator, PathManager |

---

## 3. 核心模块详解

### 3.1 主入口模块 (main.py)

**职责**:
- 初始化应用程序
- 创建并显示主窗口
- 启动事件循环

**主要函数**:
```python
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
```

---

### 3.2 UI 层 (src/ui/)

#### MainWindow (src/ui/main_window.py)

**职责**:
- 应用主窗口，协调各模块交互
- 管理文件浏览器和编辑器布局
- 处理菜单、工具栏和状态栏
- 协调文件打开、保存、翻译等操作
- 支持文本导入功能

**核心组件**:
- 文件浏览器 (QTreeView + FilteredFileModel)
- 欢迎页/编辑器切换 (QStackedWidget)
- 单元格容器 (QScrollArea + QVBoxLayout)

**核心功能**:
- `new_file()`: 新建 .transnb 文件
- `open_file()`: 打开已有文件
- `open_folder()`: 打开文件夹作为工作区
- `import_text()`: 导入文本文件并自动分割为段落
- `save_file()` / `save_file_as()`: 保存文件
- `translate_current_cell()` / `translate_all_cells()`: 翻译功能
- `insert_cell_above/below()` / `delete_selected_cell()`: 单元格操作
- `set_theme()`: 主题切换（浅色/深色）

**信号/槽**:
- `file_opened` → 加载单元格并切换到编辑器
- `file_saved` → 更新状态和窗口标题
- `cell_content_changed` → 标记文件已修改

---

### 3.3 业务逻辑层 (src/)

#### CellManager (src/cells/cell_manager.py)

**职责**:
- 管理 MarkdownCell 列表
- 处理单元格选择、插入、删除、移动
- 协调单元格翻译请求
- 文件保存/加载数据序列化
- 支持从文本内容直接加载单元格

**核心方法**:
- `add_cell(cell)`: 添加新单元格
- `remove_cell(index)`: 移除指定单元格
- `translate_cell(index)`: 翻译指定单元格
- `insert_cell_above/below()`: 在当前选中单元格上下插入
- `save_to_file(file_path)`: 保存单元格到 JSON 文件
- `load_from_file(file_path)`: 从 JSON 文件加载单元格
- `load_from_text_content(content)`: 从文本内容加载单元格（自动按段落分割）

**数据结构**:
```python
cells_data = [
    {
        'type': 'markdown',
        'content': '源文本',
        'output': '翻译结果'
    }
]
```

---

#### TranslationService (src/translation/translation_service.py)

**职责**:
- 管理多个翻译提供者
- 切换当前活动翻译提供者
- 执行翻译请求
- 管理翻译模式（解析模式、场景模式等）

**核心方法**:
- `register_provider(provider_id, provider)`: 注册翻译提供者
- `set_current_provider(provider_id)`: 设置当前活动提供者
- `translate(text, prompt_template)`: 执行异步翻译
- `load_custom_providers(custom_models)`: 加载自定义模型配置

**提供者类型**:
- 系统提供者 (`system_*`)
- 自定义提供者 (`custom_*`)

---

#### FileService (src/workspace/file_service.py)

**职责**:
- 管理 .transnb 文件的打开、保存、关闭
- 追踪文件修改状态
- 处理文件创建、重命名、删除
- 支持从文本文件导入内容并自动分割为段落
- 发出文件操作相关信号

**核心方法**:
- `create_new_file(filename)`: 在工作区创建新文件
- `create_file_with_content(filename, content)`: 创建新文件并加载文本内容（自动按段落分割成单元格）
- `open_file(file_path)`: 打开文件
- `save_file()` / `save_file_as(new_file_path)`: 保存/另存为
- `close_file()`: 关闭文件
- `set_modified(modified)`: 设置修改状态

**信号**:
- `file_opened(str)`: 文件已打开
- `file_saved(str)`: 文件已保存
- `file_modified(bool)`: 修改状态变化
- `file_closed()`: 文件已关闭
- `error_occurred(str)`: 错误发生

---

#### WorkspaceManager (src/workspace/workspace_manager.py)

**职责**:
- 管理工作区目录
- 监听工作区文件变化
- 获取工作区文件列表

**核心方法**:
- `set_workspace(path, save)`: 设置工作区
- `get_workspace()`: 获取当前工作区路径
- `get_transnb_files(recursive)`: 获取工作区下的 .transnb 文件
- `validate_workspace_path(path)`: 验证工作区路径

**信号**:
- `workspace_changed(str)`: 工作区路径变化
- `files_changed()`: 工作区文件列表变化

---

### 3.4 数据层 (src/settingmanager/)

#### SettingsManager (src/settingmanager/settings_manager.py)

**职责**:
- 管理应用配置
- 从 JSON 文件加载/保存设置
- 提供配置访问接口
- 发出配置变化信号

**配置结构** (settings.json):
```json
{
    "translation": {
        "enabled": false,
        "current_provider": "system_Ollama",
        "ollama": {
            "base_url": "http://localhost:11434",
            "model": "qwen2.5:0.5b",
            "timeout": 30
        }
    },
    "theme": "light",
    "window": { "width": 1200, "height": 800 },
    "prompt_templates": {
        "translation": "请翻译{input}",
        "analysis": "解析{input}...",
        "scenery": "请完成一篇包含{input}的文章"
    },
    "custom_models": [],
    "workspace": {
        "current_path": "",
        "current_file": ""
    },
    "reading": { "font_size": 12 }
}
```

**核心方法**:
- `get(key, default)`: 获取配置值
- `set(key, value, auto_save)`: 设置配置值
- `save()`: 保存配置到文件

---

### 3.5 翻译模块 (src/translation/)

#### BaseTranslationProvider (src/translation/providers/base.py)

**职责**:
- 定义翻译提供者的抽象接口
- 提供配置管理基础功能

**抽象方法**:
- `async translate(text, prompt_template)`: 执行翻译
- `test_connection()`: 测试连接
- `get_info()`: 获取提供者信息

---

#### OllamaTranslationProvider (src/translation/providers/ollama.py)

**职责**:
- 实现基于 Ollama 的翻译
- 管理本地模型列表
- 测试 Ollama 服务连接

**API 调用**:
```
POST /api/generate
{
    "model": "qwen2.5:0.5b",
    "prompt": "请翻译...",
    "stream": false
}

GET /api/tags  # 获取模型列表
```

---

#### TranslationWorker (src/translation/translation_worker.py)

**职责**:
- 在后台线程执行翻译
- 避免阻塞主 UI 线程
- 发出翻译进度和结果信号

---

### 3.6 单元格模块 (src/cells/)

#### MarkdownCell (src/cells/markdown_cell.py)

**职责**:
- 提供 Markdown 源文本和翻译结果的编辑/预览
- 支持编辑模式和阅读模式切换
- 集成翻译功能
- 自适应高度调整

**核心组件**:
- `MarkdownEditor`: 自定义的 Markdown 编辑器组件
  - 编辑模式 (Edit)
  - 阅读模式 (Read, 渲染 Markdown)
- 源文本区 (Source)
- 翻译结果区 (Translation)

**核心方法**:
- `translate()`: 执行翻译
- `set_content(content)`: 设置源文本
- `set_output(content)`: 设置翻译结果
- `adjust_height()`: 自适应调整高度
- `apply_theme(theme)`: 应用主题

---

### 3.7 工具层 (src/utils/)

#### ThemeManager (src/utils/theme_manager.py)

**职责**:
- 管理应用主题（浅色/深色）
- 提供主题配置访问
- 发出主题变化信号

**主题配置**:
```python
theme = {
    'foreground': '#000000',
    'background': '#f5f5f5',
    'editor_background': '#ffffff',
    'editor_foreground': '#000000',
    'markdown_background': '#fafafa',
    'border': '#cccccc',
    'output_border': '#dddddd',
    'scroll_area': '#f5f5f5'
}
```

---

#### FileUtils (src/utils/file_utils.py)

**职责**:
- 文件路径处理和验证
- 文件扩展名管理
- 工作区路径检查

**常量**:
- `TRANSNB_EXTENSION = '.transnb'`

**核心方法**:
- `normalize_path(path)`: 规范化路径
- `ensure_transnb_extension(filename)`: 确保有 .transnb 扩展名
- `validate_filename(filename, workspace)`: 验证文件名有效性
- `is_path_in_workspace(file_path, workspace)`: 检查路径是否在工作区内

---

#### SizeCalculator (src/utils/size_calculator.py)

**职责**:
- 计算文本内容所需的精确高度
- 支持自适应单元格高度

---

### 3.8 背诵模式模块 (src/recitation/)

背诵模式是一个完整的单词学习和记忆系统，采用艾宾浩斯遗忘曲线算法来优化学习效果。

---

#### 数据模型 (src/recitation/models.py)

**Book (词书)**:
- 表示一个单词本，包含多个单词
- 字段: id, name, path, count, create_time

**Word (单词)**:
- 表示一个单词条目
- 字段: id, book_id, word, phonetic, definition, example, raw_data

**UserStudy (学习记录)**:
- 记录用户对单词的学习状态
- 字段: id, book_id, word_id, stage, weight, last_review, next_review

---

#### 数据库管理 (src/recitation/database.py)

**DatabaseManager**:
- 管理 SQLite 数据库连接和表结构
- 数据表:
  - `book`: 词书表
  - `word`: 单词表（与词书外键关联）
  - `user_study`: 学习记录表（与词书和单词外键关联）
- 启用外键约束，确保数据一致性
- 提供数据库压缩功能

---

#### 数据访问层 (src/recitation/dal.py)

**RecitationDAL**:
- 提供完整的 CRUD 操作
- 词书操作: add_book, get_book_by_id, get_all_books, update_book, delete_book
- 单词操作: add_word, add_words_batch, get_word_by_id, get_words_by_book_id, get_unstudied_words, get_words_for_review, delete_word
- 学习记录操作: add_user_study, get_user_study_by_word_id, update_user_study, delete_user_study
- 进度统计: get_book_progress, get_book_detailed_stats
- 搜索功能: search_words

---

#### 路径管理 (src/recitation/path_manager.py)

**PathManager**:
- 管理工作区隔离的路径
- 数据目录: `.TransRead/`（在工作区下，Windows 下自动设为隐藏）
- 数据库文件: `words.db`
- 配置文件: `studywordmode.json`
- 提供路径合法性检查和目录创建功能

---

#### 词书管理服务 (src/recitation/book_service.py)

**BookService**:
- 词书导入: 支持从 JSON 文件导入词书
- 词书管理: 获取所有词书、删除词书
- 词书选择: 记录当前选择的词书到配置
- 进度展示: 获取词书及其学习进度

---

#### 学习服务 (src/recitation/study_service.py)

**StudyService**:
- 每日设置: 管理每日新学和复习单词数量
- 单词抽取:
  - `get_study_words`: 获取未学习的新单词（随机排序）
  - `get_review_words`: 获取需要复习的单词（按权重排序）
  - `get_today_words`: 获取今日学习和复习单词（智能缓存，每日自动刷新）
- 学习进度:
  - `start_study_word`: 开始学习一个单词，初始化学习记录
  - `review_word`: 复习一个单词，更新学习状态和下次复习时间
- 批量操作: 支持批量开始学习和批量复习

---

#### 艾宾浩斯算法 (src/recitation/ebbinghaus.py)

**EbbinghausAlgorithm**:
- 遗忘曲线阶段间隔:
  - 阶段 0: 5 分钟
  - 阶段 1: 30 分钟
  - 阶段 2: 12 小时
  - 阶段 3: 1 天
  - 阶段 4: 2 天
  - 阶段 5: 4 天
  - 阶段 6: 7 天
  - 阶段 7: 15 天
  - 阶段 8: 30 天
- 复习逻辑:
  - 答对: 阶段 +1，间隔延长
  - 答错: 阶段 -1，间隔缩短
- 权重计算: 使用指数衰减算法，接近下次复习时间时权重增加

---

#### 文章生成器 (src/recitation/article_generator.py)

**ArticleGenerator**:
- 格式化文章: 给新学单词加下划线 (`<u>`)，给复习单词加粗 (`**`)
- 提取标题: 从文章第一句话自动提取标题
- 保存文章: 按日期目录组织，保存为 `.transnb` 格式
- 单词汇总: 生成 Markdown 格式的单词汇总（可选）

---

#### 词书导入器 (src/recitation/book_importer.py)

**BookImporter**:
- 解析 KyleBing 格式的 JSON 词书
- 支持复杂的嵌套数据结构
- 提取字段: 单词、音标、释义、例句
- 保留原始数据供后续扩展

---

#### 背诵模式 UI (src/recitation/ui/)

**RecitationMainPage**:
- 背诵模式主界面
- 显示词书列表和学习进度
- 提供词书导入、选择、删除功能
- 展示今日新学和复习单词
- 支持生成文章和开始测验

**QuizPage**:
- 单词测验界面
- 展示单词并让用户自测
- 记录测验结果

**RecitationSettingsPanel**:
- 背诵模式设置面板
- 调整每日新学和复习单词数量

---

#### 工作线程 (src/recitation/workers.py)

提供一系列后台工作线程，避免阻塞 UI：
- InitializeDBWorker: 初始化数据库
- AddBookWorker: 添加词书
- ImportWordsWorker: 导入单词
- GetAllBooksWorker: 获取所有词书
- DeleteBookWorker: 删除词书
- GetWordsWorker: 获取单词
- GetUnstudiedWordsWorker: 获取未学单词
- GetReviewWordsWorker: 获取复习单词
- UpdateUserStudyWorker: 更新学习记录
- AddUserStudyWorker: 添加学习记录
- GetBookProgressWorker: 获取词书进度
- ImportBookWorker: 导入词书
- DownloadBookWorker: 下载词书
- GetAllBooksWithProgressWorker: 获取带进度的词书列表
- SelectBookWorker: 选择词书
- GetCurrentBookWorker: 获取当前词书
- GetDailySettingsWorker: 获取每日设置
- SetDailySettingsWorker: 设置每日设置
- GetTodayWordsWorker: 获取今日单词
- StartStudyWordWorker: 开始学习单词
- ReviewWordWorker: 复习单词
- StartStudyBatchWordsWorker: 批量开始学习
- ReviewBatchWordsWorker: 批量复习
- UpdateAllWeightsWorker: 更新所有单词权重

---

## 4. 数据流程

### 4.1 翻译流程

```
用户点击翻译
    ↓
CellManager.translate_selected_cell()
    ↓
MarkdownCell.translate()
    ↓
创建 TranslationWorker 线程
    ↓
TranslationService.translate(text, prompt_template)
    ↓
获取当前 TranslationProvider
    ↓
OllamaTranslationProvider.translate()
    ↓
发送 HTTP 请求到 Ollama API
    ↓
接收翻译结果
    ↓
TranslationWorker.finished 信号
    ↓
MarkdownCell.set_output(result)
    ↓
标记文件已修改
```

### 4.2 文件保存流程

```
用户点击保存
    ↓
FileService.save_file()
    ↓
CellManager.save_to_file(file_path)
    ↓
序列化单元格数据为 JSON
    ↓
写入文件
    ↓
file_saved 信号
    ↓
更新状态栏和窗口标题
```

### 4.3 文件打开流程

```
用户选择文件
    ↓
FileService.open_file()
    ↓
验证文件有效性
    ↓
file_opened 信号
    ↓
CellManager.load_from_file(file_path)
    ↓
从 JSON 加载并创建 MarkdownCell
    ↓
切换到编辑器页面
```

### 4.4 文本导入流程

```
用户点击导入文本
    ↓
MainWindow.import_text()
    ↓
选择要导入的文本文件 (支持 .txt, .md, .html, .htm)
    ↓
读取文件内容 (UTF-8 编码)
    ↓
FileService.create_file_with_content(filename, content)
    ↓
内容预处理:
    - 将 \r\n 替换为 \n
    - 按换行符分割成行
    - 过滤空行和纯空白段落
    ↓
为每个段落创建 MarkdownCell
    ↓
保存到 .transnb 文件
    ↓
file_opened 信号
    ↓
加载并显示内容
    ↓
标记为已修改
```

### 4.5 背诵模式 - 词书导入流程

```
用户点击导入词书
    ↓
选择 JSON 词书文件
    ↓
BookImporter.import_from_file()
    ↓
解析 JSON 数据
    ↓
提取单词、音标、释义、例句
    ↓
RecitationDAL.add_book() - 保存词书
    ↓
RecitationDAL.add_words_batch() - 批量保存单词
    ↓
刷新词书列表
```

### 4.6 背诵模式 - 学习流程

```
用户选择词书
    ↓
StudyService.get_today_words()
    ↓
检查是否需要刷新
    ↓
获取未学习单词 (get_study_words)
    ↓
获取需要复习单词 (get_words_for_review)
    ↓
保存到配置（每日缓存）
    ↓
展示今日单词列表
    ↓
用户开始学习
    ↓
StudyService.start_study_word() - 初始化学习记录
    ↓
EbbinghausAlgorithm.calculate_initial_state()
    ↓
设置阶段=0，下次复习=5分钟后
    ↓
更新 user_study 表
```

### 4.7 背诵模式 - 复习流程

```
用户复习单词
    ↓
QuizPage 展示单词
    ↓
用户回答正确/错误
    ↓
StudyService.review_word(word_id, is_correct)
    ↓
EbbinghausAlgorithm.calculate_review_result()
    ↓
根据结果调整阶段:
    - 正确: 阶段 +1
    - 错误: 阶段 -1
    ↓
计算新的复习间隔和权重
    ↓
RecitationDAL.update_user_study()
    ↓
更新学习记录
```

### 4.8 背诵模式 - 生成文章流程

```
用户点击生成文章
    ↓
获取今日新学和复习单词
    ↓
收集单词文本
    ↓
GenerateArticleWorker (后台线程)
    ↓
TranslationService.generate_scene_text(words)
    ↓
调用 Ollama API 生成包含单词的文章
    ↓
ArticleGenerator.format_article()
    ↓
给新学单词加下划线，复习单词加粗
    ↓
ArticleGenerator.extract_title()
    ↓
提取文章标题
    ↓
ArticleGenerator.save_article()
    ↓
在工作区创建 YYMMDD 日期目录
    ↓
保存为 .transnb 格式
    ↓
FileService.open_file()
    ↓
在编辑器中打开生成的文章
```

---

## 5. 扩展点

### 5.1 新增翻译提供者

1. 继承 `BaseTranslationProvider`
2. 实现 `translate()`, `test_connection()`, `get_info()` 方法
3. 在 `TranslationService` 中注册新提供者

### 5.2 新增单元格类型

1. 继承 `BaseCell`
2. 实现自定义 UI 和逻辑
3. 在 `CellManager` 中添加创建方法
4. 更新文件序列化格式

### 5.3 新增主题

1. 在 `ThemeManager` 中添加新主题配置
2. 更新 `SettingsManager` 中的默认设置

---

## 6. 依赖关系

```
MainWindow
├── SettingsManager
├── ThemeManager
├── TranslationService
│   ├── OllamaTranslationProvider
│   └── (其他 Providers)
├── WorkspaceManager
├── FileService
│   └── WorkspaceManager
├── CellManager
│   ├── MarkdownCell
│   │   ├── BaseCell
│   │   ├── MarkdownEditor
│   │   ├── TranslationWorker
│   │   └── TranslationService
│   └── TranslationService
└── 背诵模式
    ├── PathManager (路径管理)
    ├── DatabaseManager (数据库管理)
    │   └── PathManager
    ├── RecitationDAL (数据访问层)
    │   └── DatabaseManager
    ├── BookService (词书服务)
    │   ├── RecitationDAL
    │   ├── PathManager
    │   └── BookImporter (词书导入)
    ├── StudyService (学习服务)
    │   ├── RecitationDAL
    │   ├── PathManager
    │   └── EbbinghausAlgorithm (艾宾浩斯算法)
    ├── ArticleGenerator (文章生成器)
    │   └── TranslationService (用于生成)
    └── UI 组件
        ├── RecitationMainPage
        ├── QuizPage
        └── RecitationSettingsPanel
```

---

## 7. 目录结构

```
myui/
├── main.py                          # 应用入口
├── requirements.txt                 # 依赖列表
├── settings.json                    # 配置文件
├── test.transnb                     # 示例文件
└── src/
    ├── __init__.py
    ├── ui/                          # UI 层
    │   ├── __init__.py
    │   └── main_window.py           # 主窗口
    ├── cells/                       # 单元格模块
    │   ├── __init__.py
    │   ├── base_cell.py             # 单元格基类
    │   ├── cell_manager.py          # 单元格管理器
    │   └── markdown_cell.py         # Markdown 单元格
    ├── components/                  # UI 组件
    │   ├── __init__.py
    │   ├── settings_dialog.py       # 设置对话框
    │   └── welcome_page.py          # 欢迎页
    ├── translation/                 # 翻译模块
    │   ├── __init__.py
    │   ├── base_engine.py
    │   ├── model_manager.py
    │   ├── translation_service.py   # 翻译服务
    │   ├── translation_worker.py    # 翻译工作线程
    │   ├── modes/                   # 翻译模式
    │   │   ├── __init__.py
    │   │   ├── parse_mode.py
    │   │   ├── scene_mode.py
    │   │   └── translation_mode.py
    │   └── providers/               # 翻译提供者
    │       ├── __init__.py
    │       ├── base.py              # 基类
    │       └── ollama.py            # Ollama 实现
    ├── workspace/                   # 工作区模块
    │   ├── __init__.py
    │   ├── file_service.py          # 文件服务
    │   ├── filtered_file_model.py   # 文件模型过滤
    │   └── workspace_manager.py     # 工作区管理器
    ├── settingmanager/              # 设置管理
    │   ├── __init__.py
    │   └── settings_manager.py      # 设置管理器
    ├── recitation/                  # 背诵模式模块
    │   ├── __init__.py
    │   ├── models.py                # 数据模型 (Book, Word, UserStudy)
    │   ├── path_manager.py          # 路径管理
    │   ├── database.py              # 数据库管理
    │   ├── dal.py                   # 数据访问层 (RecitationDAL)
    │   ├── book_service.py          # 词书服务
    │   ├── study_service.py         # 学习服务
    │   ├── ebbinghaus.py            # 艾宾浩斯算法
    │   ├── article_generator.py     # 文章生成器
    │   ├── book_importer.py         # 词书导入器
    │   ├── download_service.py      # 下载服务
    │   ├── workers.py               # 后台工作线程
    │   └── ui/                      # 背诵模式 UI
    │       ├── __init__.py
    │       ├── recitation_main_page.py   # 背诵模式主页
    │       ├── quiz_page.py               # 测验页面
    │       ├── dialogs.py                 # 对话框
    │       └── recitation_settings_panel.py # 设置面板
    └── utils/                       # 工具模块
        ├── __init__.py
        ├── file_utils.py            # 文件工具
        ├── size_calculator.py       # 尺寸计算
        └── theme_manager.py         # 主题管理
```
