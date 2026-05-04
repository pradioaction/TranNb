
# 翻译笔记本 API 接口文档

## 目录

- [翻译服务 (TranslationService)](#翻译服务-translationservice)
- [模型管理器 (ModelManager)](#模型管理器-modelmanager)
- [单元格管理器 (CellManager)](#单元格管理器-cellmanager)
- [文件服务 (FileService)](#文件服务-fileservice)
- [工作区管理器 (WorkspaceManager)](#工作区管理器-workspacemanager)
- [设置管理器 (SettingsManager)](#设置管理器-settingsmanager)
- [翻译提供者 (Translation Providers)](#翻译提供者-translation-providers)
- [单元格 (Cells)](#单元格-cells)
- [主题管理器 (ThemeManager)](#主题管理器-thememanager)
- [文件工具 (FileUtils)](#文件工具-fileutils)
- [背诵模式 API](#背诵模式-api)

---

## 翻译服务 (TranslationService)

### 类定义

```python
class TranslationService:
    def __init__(self)
```

### 方法

#### `set_settings_manager(settings_manager)`

设置配置管理器。

**参数**:
- `settings_manager` (SettingsManager): 配置管理器实例

---

#### `reload_from_settings()`

从设置热重载自定义提供者（无需重启）。

**参数**: 无

**返回值**: 无

---

#### `register_provider(provider_id: str, provider: BaseTranslationProvider) -&gt; bool`

注册一个翻译提供者。

**参数**:
- `provider_id` (str): 提供者唯一标识符，格式如 `system_Ollama` 或 `custom_myModel`
- `provider` (BaseTranslationProvider): 提供者实例

**返回值**:
- `bool`: 注册是否成功

**示例**:
```python
service = TranslationService()
ollama = OllamaTranslationProvider()
service.register_provider("system_Ollama", ollama)
```

---

#### `unregister_provider(provider_id: str) -&gt; bool`

注销一个翻译提供者。

**参数**:
- `provider_id` (str): 要注销的提供者 ID

**返回值**:
- `bool`: 注销是否成功

---

#### `get_provider(provider_id: Optional[str] = None) -&gt; Optional[BaseTranslationProvider]`

获取指定的翻译提供者，或获取当前活动提供者。

**参数**:
- `provider_id` (str, optional): 提供者 ID，不提供则返回当前提供者

**返回值**:
- `BaseTranslationProvider | None`: 提供者实例或 None

---

#### `set_current_provider(provider_id: str) -&gt; bool`

设置当前活动的翻译提供者。

**参数**:
- `provider_id` (str): 提供者 ID

**返回值**:
- `bool`: 设置是否成功

---

#### `get_current_provider() -&gt; Optional[BaseTranslationProvider]`

获取当前活动的翻译提供者。

**返回值**:
- `BaseTranslationProvider | None`: 当前提供者实例或 None

---

#### `get_translation_timeout_seconds() -&gt; int`

获取当前选用模型的超时（秒）。

**返回值**:
- `int`: 超时时间（秒，范围 15-600）

---

#### `list_providers() -&gt; List[str]`

列出所有已注册的提供者 ID。

**返回值**:
- `List[str]`: 提供者 ID 列表

---

#### `list_providers_by_type(provider_type: ProviderType) -&gt; List[str]`

按类型列出提供者。

**参数**:
- `provider_type` (ProviderType): 类型枚举 (SYSTEM 或 CUSTOM)

**返回值**:
- `List[str]`: 匹配类型的提供者 ID 列表

---

#### `load_custom_providers(custom_models: List[Dict[str, Any]])`

使用热重载替换所有自定义提供者，避免配置更新后仍沿用旧实例。

**参数**:
- `custom_models` (List[Dict]): 自定义模型配置列表

**配置示例**:
```python
[
    {
        "name": "myCustomModel",
        "api_key": "",
        "endpoint": "",
        "model": "",
        "timeout": 30,
        "backend": "ollama",
        "enabled": true
    }
]
```

---

#### `get_all_providers_info() -&gt; Dict[str, Dict[str, Any]]`

获取所有提供者的信息。

**返回值**:
- `Dict[str, Dict]`: 提供者信息字典，键为 provider_id

---

#### `async translate(text: str, prompt_template: str = "", provider_name: Optional[str] = None, **kwargs) -&gt; str`

执行翻译。

**参数**:
- `text` (str): 要翻译的文本
- `prompt_template` (str, optional): 提示词模板
- `provider_name` (str, optional): 指定使用的提供者，不指定则用当前提供者
- `**kwargs`: 其他可选参数

**返回值**:
- `str`: 翻译结果

**异常**:
- `ValueError`: 没有可用的提供者

**示例**:
```python
result = await service.translate(
    "Hello world",
    prompt_template="请将以下文本翻译成中文: {input}"
)
```

---

#### `async generate_scene_text(words: List[str], prompt_template: Optional[str] = None, provider_name: Optional[str] = None, **kwargs) -&gt; str`

生成包含指定单词的场景文章。

**参数**:
- `words` (List[str]): 要包含在文章中的单词列表
- `prompt_template` (str, optional): 提示词模板
- `provider_name` (str, optional): 指定使用的提供者
- `**kwargs`: 其他可选参数

**返回值**:
- `str`: 生成的文章

**异常**:
- `ValueError`: 没有可用的提供者

---

#### `process_with_parse_mode(input_data: Any, prompt_template: str = "") -&gt; Any`

使用解析模式处理（用于单元格翻译）。

**参数**:
- `input_data` (Any): 输入数据
- `prompt_template` (str, optional): 提示词模板

**返回值**:
- `Any`: 处理结果

---

#### `get_translation_mode()`

获取翻译模式（预留接口）。

---

#### `get_scene_mode()`

获取场景模式（预留接口）。

---

## 模型管理器 (ModelManager)

### 类定义

```python
class ModelManager:
    def __init__(self)
```

### 方法

#### `add_model(model_name: str, model_config: Dict[str, Any]) -&gt; bool`

添加新模型。

**参数**:
- `model_name` (str): 模型名称
- `model_config` (Dict[str, Any]): 模型配置

**返回值**:
- `bool`: 是否成功

---

#### `update_model(model_name: str, model_config: Dict[str, Any]) -&gt; bool`

更新模型配置。

**参数**:
- `model_name` (str): 模型名称
- `model_config` (Dict[str, Any]): 模型配置

**返回值**:
- `bool`: 是否成功

---

#### `delete_model(model_name: str) -&gt; bool`

删除模型。

**参数**:
- `model_name` (str): 模型名称

**返回值**:
- `bool`: 是否成功

---

#### `enable_model(model_name: str) -&gt; bool`

启用模型。

**参数**:
- `model_name` (str): 模型名称

**返回值**:
- `bool`: 是否成功

---

#### `disable_model(model_name: str) -&gt; bool`

禁用模型。

**参数**:
- `model_name` (str): 模型名称

**返回值**:
- `bool`: 是否成功

---

#### `set_model_enabled(model_name: str, enabled: bool) -&gt; bool`

设置模型启用状态。

**参数**:
- `model_name` (str): 模型名称
- `enabled` (bool): 是否启用

**返回值**:
- `bool`: 是否成功

---

#### `register_model(model_name: str, model_config: Dict[str, Any])`

注册模型（与 add_model 相同）。

**参数**:
- `model_name` (str): 模型名称
- `model_config` (Dict[str, Any]): 模型配置

**返回值**: 无

---

#### `set_current_model(model_name: str) -&gt; bool`

设置当前活动模型。

**参数**:
- `model_name` (str): 模型名称

**返回值**:
- `bool`: 是否成功

---

#### `get_current_model() -&gt; Optional[str]`

获取当前活动模型。

**返回值**:
- `str | None`: 当前模型名称或 None

---

#### `get_model_config(model_name: Optional[str] = None) -&gt; Optional[Dict[str, Any]]`

获取模型配置。

**参数**:
- `model_name` (str, optional): 模型名称，不提供则返回当前模型配置

**返回值**:
- `Dict[str, Any] | None`: 模型配置

---

#### `list_models() -&gt; List[str]`

列出所有模型。

**返回值**:
- `List[str]`: 模型名称列表

---

#### `list_enabled_models() -&gt; List[str]`

列出所有启用的模型。

**返回值**:
- `List[str]`: 模型名称列表

---

#### `get_all_models() -&gt; Dict[str, Dict[str, Any]]`

获取所有模型。

**返回值**:
- `Dict[str, Dict[str, Any]]`: 模型字典

---

#### `load_models(models_list: List[Dict[str, Any]])`

批量加载模型。

**参数**:
- `models_list` (List[Dict[str, Any]]): 模型配置列表

**返回值**: 无

---

#### `export_models() -&gt; List[Dict[str, Any]]`

导出所有模型。

**返回值**:
- `List[Dict[str, Any]]`: 模型配置列表

---

## 单元格管理器 (CellManager)

### 类定义

```python
class CellManager(QObject):
    content_changed = Signal()
```

### 方法

#### `set_settings_manager(settings_manager)`

设置配置管理器。

**参数**:
- `settings_manager` (SettingsManager): 配置管理器实例

---

#### `add_cell(cell)`

添加单元格。

**参数**:
- `cell` (BaseCell): 单元格实例

---

#### `remove_cell(index: int)`

移除指定索引的单元格。

**参数**:
- `index` (int): 单元格索引

---

#### `clear_all_cells()`

清除所有单元格。

---

#### `select_cell(index: int)`

选择指定索引的单元格。

**参数**:
- `index` (int): 单元格索引

---

#### `translate_cell(index: int)`

翻译指定索引的单元格。

**参数**:
- `index` (int): 单元格索引

---

#### `translate_selected_cell()`

翻译当前选中的单元格。

---

#### `translate_all_cells()`

翻译所有单元格。

---

#### `insert_cell_above()`

在当前选中单元格上方插入新单元格。

---

#### `insert_cell_below()`

在当前选中单元格下方插入新单元格。

---

#### `delete_selected_cell()`

删除当前选中的单元格。

---

#### `move_cell(from_index: int, to_index: int)`

移动单元格。

**参数**:
- `from_index` (int): 原索引
- `to_index` (int): 目标索引

---

#### `adjust_all_cell_heights()`

调整所有单元格高度。

---

#### `save_to_file(file_path: str)`

保存单元格到文件。

**参数**:
- `file_path` (str): 文件路径

**文件格式**:
```json
{
    "version": "1.0",
    "cells": [
        {
            "type": "markdown",
            "content": "源文本",
            "output": "翻译结果"
        }
    ]
}
```

---

#### `load_from_file(file_path: str)`

从文件加载单元格。

**参数**:
- `file_path` (str): 文件路径

---

#### `load_from_text_content(content: str)`

从文本内容加载单元格，自动按段落分割。

**参数**:
- `content` (str): 文本内容

---

## 文件服务 (FileService)

### 类定义

```python
class FileService(QObject):
    file_opened = pyqtSignal(str)
    file_saved = pyqtSignal(str)
    file_modified = pyqtSignal(bool)
    file_closed = pyqtSignal()
    error_occurred = pyqtSignal(str)
```

### 方法

#### `set_cell_manager(cell_manager)`

设置单元格管理器。

**参数**:
- `cell_manager` (CellManager): 单元格管理器实例

---

#### `is_file_open(file_path: str = None) -&gt; bool`

检查文件是否已打开，或是否有文件已打开。

**参数**:
- `file_path` (str, optional): 文件路径，不提供则检查是否有打开的文件

**返回值**:
- `bool`: 文件是否已打开

---

#### `get_current_file() -&gt; Optional[str]`

获取当前打开的文件路径。

**返回值**:
- `str | None`: 文件路径或 None

---

#### `is_modified() -&gt; bool`

检查当前文件是否有未保存的修改。

**返回值**:
- `bool`: 是否已修改

---

#### `set_modified(modified: bool)`

设置当前文件的修改状态。

**参数**:
- `modified` (bool): 修改状态

---

#### `create_new_file(filename: str) -&gt; Optional[str]`

在工作区创建新文件并打开。

**参数**:
- `filename` (str): 文件名

**返回值**:
- `str | None`: 新文件路径，失败返回 None

**信号**:
- `file_opened`: 文件打开成功时发出
- `error_occurred`: 错误发生时发出

---

#### `create_file_with_content(filename: str, content: str) -&gt; Optional[str]`

在工作区创建新文件并加载文本内容，自动按段落分割成单元格。

**参数**:
- `filename` (str): 文件名
- `content` (str): 要加载的文本内容

**返回值**:
- `str | None`: 新文件路径，失败返回 None

**信号**:
- `file_opened`: 文件打开成功时发出
- `error_occurred`: 错误发生时发出

---

#### `open_file(file_path: str, check_unsaved: bool = True) -&gt; bool`

打开文件。

**参数**:
- `file_path` (str): 文件路径
- `check_unsaved` (bool, optional): 是否检查未保存修改，默认 True

**返回值**:
- `bool`: 是否成功打开

**信号**:
- `file_opened`: 打开成功时发出
- `error_occurred`: 错误发生时发出

---

#### `save_file() -&gt; bool`

保存当前文件。

**返回值**:
- `bool`: 是否成功保存

**信号**:
- `file_saved`: 保存成功时发出
- `error_occurred`: 错误发生时发出

---

#### `save_file_as(new_file_path: str) -&gt; bool`

另存为新文件。

**参数**:
- `new_file_path` (str): 新文件路径

**返回值**:
- `bool`: 是否成功保存

**信号**:
- `file_opened`: 打开新文件时发出
- `error_occurred`: 错误发生时发出

---

#### `rename_file(old_path: str, new_filename: str) -&gt; bool`

重命名文件。

**参数**:
- `old_path` (str): 原文件路径
- `new_filename` (str): 新文件名

**返回值**:
- `bool`: 是否成功重命名

**信号**:
- `file_opened`: 如果重命名的是当前文件则发出
- `error_occurred`: 错误发生时发出

---

#### `delete_file(file_path: str) -&gt; bool`

删除文件。

**参数**:
- `file_path` (str): 文件路径

**返回值**:
- `bool`: 是否成功删除

**信号**:
- `file_closed`: 如果删除的是当前文件则发出
- `error_occurred`: 错误发生时发出

---

#### `close_file(emit_signal: bool = True)`

关闭当前文件。

**参数**:
- `emit_signal` (bool, optional): 是否发出 `file_closed` 信号，默认 True

**信号**:
- `file_closed`: 文件关闭时发出

---

## 工作区管理器 (WorkspaceManager)

### 类定义

```python
class WorkspaceManager(QObject):
    workspace_changed = pyqtSignal(str)
    files_changed = pyqtSignal()
```

### 方法

#### `load_workspace() -&gt; bool`

加载保存的工作区配置。

**返回值**:
- `bool`: 是否成功加载

---

#### `set_workspace(path: str, save: bool = True) -&gt; bool`

设置工作区路径。

**参数**:
- `path` (str): 工作区目录路径
- `save` (bool, optional): 是否保存到配置，默认 True

**返回值**:
- `bool`: 是否设置成功

**信号**:
- `workspace_changed`: 工作区路径变化时发出
- `files_changed`: 文件列表变化时发出

---

#### `get_workspace() -&gt; Optional[str]`

获取当前工作区路径。

**返回值**:
- `str | None`: 工作区路径或 None

---

#### `validate_workspace_path(path: str) -&gt; Tuple[bool, str]`

验证工作区路径。

**参数**:
- `path` (str): 路径

**返回值**:
- `Tuple[bool, str]`: (是否有效, 错误信息)

---

#### `get_transnb_files(recursive: bool = False) -&gt; List[str]`

获取工作区下的所有 .transnb 文件。

**参数**:
- `recursive` (bool, optional): 是否递归查找，默认 False

**返回值**:
- `List[str]`: 文件路径列表

---

## 设置管理器 (SettingsManager)

### 类定义

```python
class SettingsManager(QObject):
    reading_font_size_changed = pyqtSignal(int)
```

### 方法

#### `get(key: str, default: Any = None) -&gt; Any`

获取配置值。

**参数**:
- `key` (str): 配置键，支持点号分隔，如 `translation.ollama.model`
- `default` (Any, optional): 默认值

**返回值**:
- `Any`: 配置值

**示例**:
```python
model = settings.get("translation.ollama.model")
```

---

#### `set(key: str, value: Any, auto_save: bool = True)`

设置配置值。

**参数**:
- `key` (str): 配置键
- `value` (Any): 配置值
- `auto_save` (bool, optional): 是否自动保存到文件，默认 True

**示例**:
```python
settings.set("translation.ollama.model", "qwen2.5:7b")
```

---

#### `save()`

保存配置到文件。

---

#### `get_translation_settings() -&gt; Dict[str, Any]`

获取翻译相关设置。

**返回值**:
- `Dict`: 翻译设置字典

---

#### `set_translation_settings(settings: Dict[str, Any], auto_save: bool = True)`

设置翻译相关设置。

**参数**:
- `settings` (Dict): 翻译设置字典
- `auto_save` (bool, optional): 是否自动保存

---

#### `get_all_settings() -&gt; Dict[str, Any]`

获取所有设置。

**返回值**:
- `Dict`: 完整配置字典

---

#### `reset_to_default()`

重置为默认配置。

---

### 提示词模板相关

#### `get_prompt_templates() -&gt; Dict[str, str]`

获取所有提示词模板。

**返回值**:
- `Dict[str, str]`: 模板字典

---

#### `set_prompt_templates(templates: Dict[str, str], auto_save: bool = True)`

设置所有提示词模板。

**参数**:
- `templates` (Dict[str, str]): 模板字典
- `auto_save` (bool, optional): 是否自动保存

---

#### `get_prompt_template(template_type: str) -&gt; str`

获取指定类型的提示词模板。

**参数**:
- `template_type` (str): 模板类型，如 `translation`, `analysis`, `scenery`

**返回值**:
- `str`: 提示词模板

---

#### `set_prompt_template(template_type: str, template: str, auto_save: bool = True)`

设置指定类型的提示词模板。

**参数**:
- `template_type` (str): 模板类型
- `template` (str): 模板内容
- `auto_save` (bool, optional): 是否自动保存

---

### 自定义模型相关

#### `get_custom_models() -&gt; List[Dict[str, Any]]`

获取自定义模型列表。

**返回值**:
- `List[Dict]`: 自定义模型配置列表

---

#### `set_custom_models(models: List[Dict[str, Any]], auto_save: bool = True)`

设置自定义模型列表。

**参数**:
- `models` (List[Dict]): 模型配置列表
- `auto_save` (bool, optional): 是否自动保存

---

#### `add_custom_model(model: Dict[str, Any], auto_save: bool = True)`

添加一个自定义模型。

**参数**:
- `model` (Dict): 模型配置
- `auto_save` (bool, optional): 是否自动保存

---

### 工作区相关

#### `get_workspace() -&gt; Dict[str, Any]`

获取工作区配置。

**返回值**:
- `Dict`: 工作区配置

---

#### `set_workspace(workspace: Dict[str, Any], auto_save: bool = True)`

设置工作区配置。

**参数**:
- `workspace` (Dict): 工作区配置
- `auto_save` (bool, optional): 是否自动保存

---

#### `get_workspace_path() -&gt; str`

获取工作区路径。

**返回值**:
- `str`: 路径字符串

---

#### `set_workspace_path(path: str, auto_save: bool = True)`

设置工作区路径。

**参数**:
- `path` (str): 路径
- `auto_save` (bool, optional): 是否自动保存

---

#### `get_current_file() -&gt; str`

获取上次打开的文件路径。

**返回值**:
- `str`: 文件路径

---

#### `set_current_file(file_path: str, auto_save: bool = True)`

设置当前文件路径。

**参数**:
- `file_path` (str): 文件路径
- `auto_save` (bool, optional): 是否自动保存

---

#### `get_recent_files() -&gt; List[str]`

获取最近打开的文件列表。

**返回值**:
- `List[str]`: 文件路径列表

---

#### `set_recent_files(files: List[str], auto_save: bool = True)`

设置最近打开的文件列表。

**参数**:
- `files` (List[str]): 文件路径列表
- `auto_save` (bool, optional): 是否自动保存

---

#### `get_cell_states() -&gt; Dict[str, Any]`

获取单元格状态。

**返回值**:
- `Dict[str, Any]`: 状态字典

---

#### `set_cell_states(states: Dict[str, Any], auto_save: bool = True)`

设置单元格状态。

**参数**:
- `states` (Dict[str, Any]): 状态字典
- `auto_save` (bool, optional): 是否自动保存

---

### 翻译提供者相关

#### `get_current_translation_provider() -&gt; str`

获取当前翻译提供者 ID。

**返回值**:
- `str`: 提供者 ID

---

#### `set_current_translation_provider(provider_id: str, auto_save: bool = True)`

设置当前翻译提供者。

**参数**:
- `provider_id` (str): 提供者 ID
- `auto_save` (bool, optional): 是否自动保存

---

#### `parse_provider_id(provider_id: str) -&gt; Tuple[str, str]`

解析 provider_id，返回 (type, name) 元组。

**参数**:
- `provider_id` (str): 提供者 ID

**返回值**:
- `Tuple[str, str]`: (类型, 名称) 元组

---

#### `build_provider_id(provider_type: str, name: str) -&gt; str`

构建 provider_id。

**参数**:
- `provider_type` (str): 类型（system 或 custom）
- `name` (str): 名称

**返回值**:
- `str`: provider_id

---

#### `get_ollama_settings() -&gt; Dict[str, Any]`

获取 Ollama 配置。

**返回值**:
- `Dict`: Ollama 配置字典

---

#### `set_ollama_settings(settings: Dict[str, Any], auto_save: bool = True)`

设置 Ollama 配置。

**参数**:
- `settings` (Dict): 配置字典
- `auto_save` (bool, optional): 是否自动保存

---

### 阅读字体相关

#### `get_reading_font_size() -&gt; int`

获取阅读模式字体大小。

**返回值**:
- `int`: 字体大小（pt）

---

#### `set_reading_font_size(font_size: int, auto_save: bool = True)`

设置阅读模式字体大小。

**参数**:
- `font_size` (int): 字体大小
- `auto_save` (bool, optional): 是否自动保存

**信号**:
- `reading_font_size_changed`: 字体大小变化时发出

---

## 翻译提供者 (Translation Providers)

### BaseTranslationProvider (基类)

#### 类定义

```python
class BaseTranslationProvider(ABC):
    def __init__(self, name: str, provider_type: ProviderType = ProviderType.SYSTEM)
```

#### 抽象方法

##### `async translate(text: str, prompt_template: str = "", **kwargs) -&gt; str`

执行翻译。

**参数**:
- `text` (str): 要翻译的文本
- `prompt_template` (str, optional): 提示词模板
- `**kwargs`: 其他参数

**返回值**:
- `str`: 翻译结果

---

##### `test_connection() -&gt; bool`

测试连接。

**返回值**:
- `bool`: 连接是否成功

---

##### `get_info() -&gt; Dict[str, Any]`

获取提供者信息。

**返回值**:
- `Dict`: 信息字典

---

#### 其他方法

##### `set_config(key: str, value: Any)`

设置配置项。

**参数**:
- `key` (str): 配置键
- `value` (Any): 配置值

---

##### `get_config(key: str, default: Any = None) -&gt; Any`

获取配置项。

**参数**:
- `key` (str): 配置键
- `default` (Any, optional): 默认值

**返回值**:
- `Any`: 配置值

---

##### `update_config(config: Dict[str, Any])`

批量更新配置。

**参数**:
- `config` (Dict): 配置字典

---

##### `get_display_name() -&gt; str`

获取显示名称。

**返回值**:
- `str`: 显示名称

---

### OllamaTranslationProvider

#### 类定义

```python
class OllamaTranslationProvider(BaseTranslationProvider):
    def __init__(self, name: str = "Ollama", provider_type: ProviderType = ProviderType.SYSTEM)
```

#### 默认配置

```python
{
    "base_url": "http://localhost:11434",
    "model": "qwen2.5:0.5b",
    "timeout": 30
}
```

#### 方法

##### `async translate(text: str, prompt_template: str = "", **kwargs) -&gt; str`

执行翻译（实现基类抽象方法）。

**API**:
- `POST /api/generate`
- 请求体: `{"model": "...", "prompt": "...", "stream": false}`

---

##### `list_models() -&gt; List[str]`

获取 Ollama 本地已下载的模型列表。

**返回值**:
- `List[str]`: 模型名称列表

**API**:
- `GET /api/tags`

---

##### `test_connection() -&gt; bool`

测试 Ollama 服务连接。

**返回值**:
- `bool`: 连接是否成功

---

##### `get_info() -&gt; Dict[str, Any]`

获取提供者信息。

**返回值**:
```python
{
    "name": "Ollama",
    "type": "system",
    "base_url": "...",
    "model": "..."
}
```

---

### OpenAITranslationProvider

#### 类定义

```python
class OpenAITranslationProvider(BaseTranslationProvider):
    def __init__(self)
```

#### 默认配置

```python
{
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-3.5-turbo",
    "timeout": 60,
    "proxy": "",
    "api_key_env": "OPENAI_API_KEY"
}
```

#### 方法

##### `async translate(text: str, prompt_template: str = "", **kwargs) -&gt; str`

执行翻译（实现基类抽象方法）。

**API**:
- `POST /chat/completions`
- 请求体: `{"model": "...", "messages": [...]}`

---

##### `test_connection() -&gt; bool`

测试 OpenAI 兼容服务连接。

**返回值**:
- `bool`: 连接是否成功

---

##### `get_info() -&gt; Dict[str, Any]`

获取提供者信息。

**返回值**:
```python
{
    "name": "OpenAI",
    "type": "system",
    "backend": "openai",
    "base_url": "...",
    "model": "..."
}
```

---

### CustomOllamaProvider

#### 类定义

```python
class CustomOllamaProvider(OllamaTranslationProvider):
    def __init__(self, name: str, config: Dict[str, Any])
```

自定义 Ollama 提供者，继承自 OllamaTranslationProvider。

---

### CustomArkProvider

#### 类定义

```python
class CustomArkProvider(BaseTranslationProvider):
    def __init__(self, name: str, config: Dict[str, Any])
```

火山引擎方舟：使用官方 Ark Runtime（OpenAI 兼容 Chat）。

#### 默认配置

```python
{
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "model": "",
    "api_key": "",
    "timeout": 120
}
```

#### 方法

##### `async translate(text: str, prompt_template: str = "", **kwargs) -&gt; str`

执行翻译（实现基类抽象方法）。

**API**:
- 使用 volcenginesdkarkruntime.Ark SDK 调用 `/api/v3/chat/completions`

---

##### `test_connection() -&gt; bool`

测试 Ark 服务连接。

**返回值**:
- `bool`: 连接是否成功

---

##### `get_info() -&gt; Dict[str, Any]`

获取提供者信息。

**返回值**:
```python
{
    "name": "自定义模型名",
    "type": "custom",
    "backend": "ark",
    "base_url": "...",
    "model": "..."
}
```

---

### ProviderType 枚举

```python
class ProviderType(Enum):
    SYSTEM = "system"
    CUSTOM = "custom"
```

---

### APIKeyResolver (API 密钥解析器)

#### 核心函数

##### `resolve_openai_api_key(config: Dict[str, Any]) -&gt; Optional[str]`

解析 OpenAI 兼容的 API 密钥。

**参数**:
- `config` (Dict): 提供者配置，支持 `api_key_env` 指定环境变量名

**返回值**:
- `str | None`: API 密钥或 None

**配置示例**:
```python
{
    "api_key_env": "MY_CUSTOM_KEY"  # 优先使用此环境变量
}
```

---

### build_custom_provider (工厂函数)

#### 函数定义

```python
def build_custom_provider(name: str, model: Dict[str, Any]) -&gt; BaseTranslationProvider
```

根据自定义模型配置中的 `backend` 字段，构建对应的提供者实例。

**参数**:
- `name` (str): 提供者名称
- `model` (Dict[str, Any]): 模型配置字典

**返回值**:
- `BaseTranslationProvider`: 构建的提供者实例

**支持的 backend**:
- `ollama`: 构建 CustomOllamaProvider（默认）
- `ark`: 构建 CustomArkProvider
- `openai`: 构建 OpenAI 兼容的自定义提供者

---

## 单元格 (Cells)

### BaseCell (基类)

#### 类定义

```python
class BaseCell(QWidget):
    selected = Signal(object)
    translate_requested = Signal(object)
    delete_requested = Signal(object)
    move_up_requested = Signal(object)
    move_down_requested = Signal(object)
```

#### 信号

- `selected`: 单元格被选中
- `translate_requested`: 请求翻译
- `delete_requested`: 请求删除
- `move_up_requested`: 请求上移
- `move_down_requested`: 请求下移

#### 方法

##### `set_translation_service(service)`

设置翻译服务。

**参数**:
- `service` (TranslationService): 翻译服务实例

---

##### `set_settings_manager(manager)`

设置配置管理器。

**参数**:
- `manager` (SettingsManager): 配置管理器实例

---

##### `set_selected(selected)`

设置选中状态。

**参数**:
- `selected` (bool): 是否选中

---

##### `apply_theme(theme)`

应用主题。

**参数**:
- `theme` (Dict): 主题配置字典

---

##### `set_gutter_visible(visible)`

控制左侧按钮区域显示/隐藏。

**参数**:
- `visible` (bool): 是否显示

---

##### `adjust_height()`

调整单元格高度（子类可覆盖）。

---

### MarkdownCell

#### 类定义

```python
class MarkdownCell(BaseCell):
    def __init__(self)
```

#### 方法

##### `set_settings_manager(settings_manager)`

设置配置管理器。

**参数**:
- `settings_manager` (SettingsManager): 配置管理器实例

---

##### `set_content(content: str)`

设置源文本内容。

**参数**:
- `content` (str): 文本内容

---

##### `get_content() -&gt; str`

获取源文本内容。

**返回值**:
- `str`: 文本内容

---

##### `set_output(content: str)`

设置翻译结果。

**参数**:
- `content` (str): 翻译结果文本

---

##### `get_output() -&gt; str`

获取翻译结果。

**返回值**:
- `str`: 翻译结果文本

---

##### `translate()`

执行翻译。

---

##### `apply_theme(theme: Dict[str, str])`

应用主题。

**参数**:
- `theme` (Dict): 主题配置字典

---

##### `adjust_height()`

调整单元格高度。

---

##### `toggle_cell_collapse()`

切换单元格折叠状态。

---

##### `toggle_input_collapse()`

切换原文折叠状态。

---

##### `toggle_output_collapse()`

切换译文折叠状态。

---

#### 单元格组件 Widgets

##### MarkdownEditor

```python
class MarkdownEditor(QWidget):
    content_changed = Signal()
    needs_height_update = Signal()
```

**方法**:
- `set_content(content: str)`: 设置内容
- `get_content() -&gt; str`: 获取内容
- `update_reading()`: 更新阅读模式渲染
- `switch_to_edit_mode()`: 切换到编辑模式
- `switch_to_reading_mode()`: 切换到阅读模式
- `apply_theme(theme: Dict[str, str])`: 应用主题
- `set_settings_manager(settings_manager)`: 设置配置管理器

##### ClickableIndicator

可点击的指示线组件。

##### ClickableTextEdit

可双击切换模式的文本编辑器组件。

---

### CellFactory (单元格工厂)

#### 类定义

```python
class CellFactory:
    @staticmethod
    def create_cell(cell_type: str, **kwargs) -&gt; BaseCell
```

#### 方法

##### `create_cell(cell_type: str, **kwargs) -&gt; BaseCell`

创建单元格。

**参数**:
- `cell_type` (str): 单元格类型（"markdown"）
- `**kwargs`: 其他参数

**返回值**:
- `BaseCell`: 单元格实例

---

### CellSignalManager (信号管理器)

#### 类定义

```python
class CellSignalManager:
    def __init__(self, cell_manager: CellManager)
```

#### 方法

##### `connect_cell_signals(cell: BaseCell)`

连接单元格信号。

**参数**:
- `cell` (BaseCell): 单元格实例

---

##### `disconnect_cell_signals(cell: BaseCell)`

断开单元格信号。

**参数**:
- `cell` (BaseCell): 单元格实例

---

### CellHeightCalculator (高度计算器)

#### 类定义

```python
class CellHeightCalculator:
    @staticmethod
    def calculate_height(text: str, font_size: int = 12) -&gt; int
```

#### 方法

##### `calculate_height(text: str, font_size: int = 12) -&gt; int`

计算文本内容所需的高度。

**参数**:
- `text` (str): 文本内容
- `font_size` (int, optional): 字体大小，默认 12

**返回值**:
- `int`: 计算后的高度（像素）

---

## 主题管理器 (ThemeManager)

### 类定义

```python
class ThemeManager(QObject):
    theme_changed = pyqtSignal(str)
```

### 方法

#### `set_theme(theme_name: str)`

设置主题。

**参数**:
- `theme_name` (str): 主题名称（`light` 或 `dark`）

---

#### `get_theme() -&gt; Dict[str, str]`

获取当前主题配置。

**返回值**:
- `Dict[str, str]`: 主题配置字典

---

#### `get_theme_name() -&gt; str`

获取当前主题名称。

**返回值**:
- `str`: 主题名称

---

### 主题配置

#### 浅色主题

```python
{
    "foreground": "#000000",
    "background": "#f5f5f5",
    "editor_background": "#ffffff",
    "editor_foreground": "#000000",
    "markdown_background": "#fafafa",
    "border": "#cccccc",
    "output_border": "#dddddd",
    "scroll_area": "#f5f5f5",
    "cell_selected": "#e8f4fd"
}
```

#### 深色主题

```python
{
    "foreground": "#ffffff",
    "background": "#1e1e1e",
    "editor_background": "#2d2d2d",
    "editor_foreground": "#ffffff",
    "markdown_background": "#252526",
    "border": "#3c3c3c",
    "output_border": "#333333",
    "scroll_area": "#1e1e1e",
    "cell_selected": "#1e3a5f"
}
```

---

## 文件工具 (FileUtils)

### 常量

#### `TRANSNB_EXTENSION`

翻译笔记本文件扩展名，值为 `".transnb"`。

---

### 方法

#### `normalize_path(path: str) -&gt; Path`

规范化路径。

**参数**:
- `path` (str): 路径字符串

**返回值**:
- `Path`: 规范化后的 Path 对象

---

#### `ensure_transnb_extension(filename: str) -&gt; str`

确保文件名有 .transnb 扩展名。

**参数**:
- `filename` (str): 文件名

**返回值**:
- `str`: 处理后的文件名

---

#### `validate_filename(filename: str, workspace: str) -&gt; Tuple[bool, str]`

验证文件名有效性。

**参数**:
- `filename` (str): 文件名
- `workspace` (str): 工作区路径

**返回值**:
- `Tuple[bool, str]`: (是否有效, 错误信息)

---

#### `is_path_in_workspace(file_path: str, workspace: str) -&gt; bool`

检查文件路径是否在工作区内。

**参数**:
- `file_path` (str): 文件路径
- `workspace` (str): 工作区路径

**返回值**:
- `bool`: 是否在工作区内

---

#### `check_directory_permissions(directory: str) -&gt; Tuple[bool, str]`

检查目录权限。

**参数**:
- `directory` (str): 目录路径

**返回值**:
- `Tuple[bool, str]`: (是否有读写权限, 错误信息)

---

## 背诵模式 API

### 数据模型 (src/recitation/models.py)

#### Book (词书)

```python
@dataclass
class Book:
    id: Optional[int] = None
    name: str = ""
    path: str = ""
    count: int = 0
    create_time: Optional[datetime] = None
```

**字段说明**:
- `id`: 词书 ID（主键）
- `name`: 词书名称
- `path`: 词书文件路径
- `count`: 单词数量
- `create_time`: 创建时间

---

#### Word (单词)

```python
@dataclass
class Word:
    id: Optional[int] = None
    book_id: int = 0
    word: str = ""
    phonetic: str = ""
    definition: str = ""
    example: str = ""
    raw_data: str = ""
```

**字段说明**:
- `id`: 单词 ID（主键）
- `book_id`: 所属词书 ID
- `word`: 单词文本
- `phonetic`: 音标
- `definition`: 释义
- `example`: 例句
- `raw_data`: 原始 JSON 数据（保留）

---

#### UserStudy (学习记录)

```python
@dataclass
class UserStudy:
    id: Optional[int] = None
    book_id: int = 0
    word_id: int = 0
    stage: int = 0
    weight: float = 0.0
    last_review: Optional[datetime] = None
    next_review: Optional[datetime] = None
```

**字段说明**:
- `id`: 学习记录 ID（主键）
- `book_id`: 词书 ID
- `word_id`: 单词 ID
- `stage`: 学习阶段 (0-8)
- `weight`: 复习权重
- `last_review`: 上次复习时间
- `next_review`: 下次复习时间

---

### 路径管理 (src/recitation/path_manager.py)

#### PathManager

```python
class PathManager:
    def __init__(self, workspace_path: Optional[str] = None)
```

**方法**:

##### `set_workspace(workspace_path: str)`

设置工作区路径。

**参数**:
- `workspace_path`: 工作区路径

---

##### `get_workspace() -&gt; Optional[str]`

获取当前工作区路径。

**返回值**:
- 工作区路径，未设置返回 None

---

##### `get_data_dir() -&gt; Optional[Path]`

获取背诵模式数据目录路径（`.TransRead/`）。

**返回值**:
- Path 对象或 None

---

##### `get_db_path() -&gt; Optional[Path]`

获取数据库文件路径。

**返回值**:
- Path 对象或 None

---

##### `get_config_path() -&gt; Optional[Path]`

获取配置文件路径。

**返回值**:
- Path 对象或 None

---

##### `ensure_data_dir() -&gt; bool`

确保数据目录存在，不存在则创建（Windows 下自动设为隐藏）。

**返回值**:
- 是否成功

---

##### `is_valid() -&gt; bool`

检查路径管理器是否有效（是否已设置工作区）。

**返回值**:
- 是否有效

---

### 数据库管理 (src/recitation/database.py)

#### DatabaseManager

```python
class DatabaseManager:
    def __init__(self, path_manager: PathManager)
```

**方法**:

##### `initialize() -&gt; bool`

初始化数据库，创建数据目录和表结构。

**返回值**:
- 是否成功

---

##### `vacuum() -&gt; bool`

压缩数据库，清理未使用空间。

**返回值**:
- 是否成功

---

##### `is_initialized() -&gt; bool`

检查数据库是否已初始化。

**返回值**:
- 是否已初始化

---

##### `get_connection() -&gt; ContextManager[sqlite3.Connection]`

获取数据库连接的上下文管理器。

**用法示例**:
```python
with db_manager.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM book")
```

---

### 模块化数据访问层 (src/recitation/dal/)

背诵模式采用模块化 DAL 设计，将数据访问拆分为多个专门的类。

#### BookDAL (词书数据访问)

```python
class BookDAL:
    def __init__(self, db_manager: DatabaseManager)
```

**方法**:

##### `add_book(book: Book) -&gt; Optional[Book]`

添加词书。

**参数**:
- `book`: 词书对象

**返回值**:
- 插入后的词书对象（包含生成的 id），失败返回 None

---

##### `refresh_book_count(book_id: int) -&gt; bool`

重新同步词书数量（从 word 表实际统计）。

**参数**:
- `book_id`: 词书 ID

**返回值**:
- 是否成功

---

##### `get_book_by_id(book_id: int) -&gt; Optional[Book]`

根据 ID 获取词书。

**参数**:
- `book_id`: 词书 ID

**返回值**:
- 词书对象或 None

---

##### `get_all_books() -&gt; List[Book]`

获取所有词书。

**返回值**:
- 词书列表

---

##### `update_book(book: Book) -&gt; bool`

更新词书。

**参数**:
- `book`: 词书对象

**返回值**:
- 是否成功

---

##### `delete_book(book_id: int) -&gt; bool`

删除词书（级联删除相关单词和学习记录）。

**参数**:
- `book_id`: 词书 ID

**返回值**:
- 是否成功

---

#### WordDAL (单词数据访问)

```python
class WordDAL:
    def __init__(self, db_manager: DatabaseManager)
```

**方法**:

##### `add_word(word: Word) -&gt; Optional[Word]`

添加单词。

**参数**:
- `word`: 单词对象

**返回值**:
- 插入后的单词对象，失败返回 None

---

##### `add_words_batch(words: List[Word]) -&gt; int`

批量添加单词。

**参数**:
- `words`: 单词列表

**返回值**:
- 成功添加的数量

---

##### `get_word_by_id(word_id: int) -&gt; Optional[Word]`

根据 ID 获取单词。

**参数**:
- `word_id`: 单词 ID

**返回值**:
- 单词对象或 None

---

##### `get_words_by_book_id(book_id: int) -&gt; List[Word]`

获取词书的所有单词。

**参数**:
- `book_id`: 词书 ID

**返回值**:
- 单词列表

---

##### `get_unstudied_words(book_id: int, limit: Optional[int] = None) -&gt; List[Word]`

获取词书中未学习的单词（随机排序）。

**参数**:
- `book_id`: 词书 ID
- `limit`: 返回数量限制（可选）

**返回值**:
- 单词列表

---

##### `get_words_for_review(book_id: int, limit: Optional[int] = None) -&gt; List[Word]`

获取需要复习的单词（按权重排序）。

**参数**:
- `book_id`: 词书 ID
- `limit`: 返回数量限制（可选）

**返回值**:
- 单词列表

---

##### `update_word(word: Word) -&gt; bool`

更新单词。

**参数**:
- `word`: 单词对象

**返回值**:
- 是否成功

---

##### `delete_word(word_id: int) -&gt; bool`

删除单词。

**参数**:
- `word_id`: 单词 ID

**返回值**:
- 是否成功

---

##### `check_word_exists_in_book(book_id: int, word_text: str) -&gt; bool`

检查单词是否已存在于指定词书中。

**参数**:
- `book_id`: 词书 ID
- `word_text`: 单词文本

**返回值**:
- 是否存在

---

##### `search_words(search_text: str, book_id: Optional[int] = None) -&gt; List[Word]`

搜索单词（支持模糊搜索单词和释义）。

**参数**:
- `search_text`: 搜索文本
- `book_id`: 可选，限定搜索的词书 ID

**返回值**:
- 匹配的单词列表

---

##### `search_word_exact_lower(word_text: str, book_id: Optional[int] = None) -&gt; Optional[Word]`

全小写精确搜索单词（在所有词书或指定词书中）。

**参数**:
- `word_text`: 单词文本
- `book_id`: 可选，限定搜索的词书 ID

**返回值**:
- 单词对象或 None

---

#### UserStudyDAL (学习记录数据访问)

```python
class UserStudyDAL:
    def __init__(self, db_manager: DatabaseManager)
```

**方法**:

##### `add_user_study(user_study: UserStudy) -&gt; Optional[UserStudy]`

添加学习记录。

**参数**:
- `user_study`: 学习记录对象

**返回值**:
- 插入后的学习记录对象，失败返回 None

---

##### `get_user_study_by_word_id(book_id: int, word_id: int) -&gt; Optional[UserStudy]`

根据单词 ID 获取学习记录。

**参数**:
- `book_id`: 词书 ID
- `word_id`: 单词 ID

**返回值**:
- 学习记录对象或 None

---

##### `get_user_studies_by_book_id(book_id: int) -&gt; List[UserStudy]`

获取词书的所有学习记录。

**参数**:
- `book_id`: 词书 ID

**返回值**:
- 学习记录列表

---

##### `update_user_study(user_study: UserStudy) -&gt; bool`

更新学习记录。

**参数**:
- `user_study`: 学习记录对象

**返回值**:
- 是否成功

---

##### `delete_user_study(user_study_id: int) -&gt; bool`

删除学习记录。

**参数**:
- `user_study_id`: 学习记录 ID

**返回值**:
- 是否成功

---

#### StatDAL (统计数据访问)

```python
class StatDAL:
    def __init__(self, db_manager: DatabaseManager)
```

**方法**:

##### `get_book_progress(book_id: int) -&gt; Dict[str, Any]`

获取词书学习进度统计。

**参数**:
- `book_id`: 词书 ID

**返回值**:
```python
{
    "total": 100,      # 单词总数
    "studied": 50,     # 已学习数
    "review_due": 20   # 待复习数
}
```

---

##### `get_book_detailed_stats(book_id: int) -&gt; Dict[str, Any]`

获取词书的详细统计信息（用于删除确认）。

**参数**:
- `book_id`: 词书 ID

**返回值**:
```python
{
    "name": "词书名",
    "word_count": 100,
    "study_count": 50
}
```

---

#### RecitationDAL (统一 DAL 入口，向后兼容)

```python
class RecitationDAL:
    def __init__(self, db_manager: DatabaseManager)
```

**方法**: 包含 BookDAL、WordDAL、UserStudyDAL、StatDAL 的所有方法，作为统一接口。

---

### 词书管理服务 (src/recitation/book_service.py)

#### BookService

```python
class BookService:
    def __init__(self, dal: RecitationDAL, path_manager: PathManager)
```

**方法**:

##### `import_book(file_path: str) -&gt; Optional[Book]`

从 JSON 文件导入词书。

**参数**:
- `file_path`: JSON 文件路径

**返回值**:
- 导入的词书对象，失败返回 None

---

##### `get_all_books() -&gt; List[Book]`

获取所有词书。

**返回值**:
- 词书列表

---

##### `get_book_with_progress(book_id: int) -&gt; Optional[Dict[str, Any]]`

获取词书及其进度信息。

**参数**:
- `book_id`: 词书 ID

**返回值**:
```python
{
    "book": Book对象,
    "total": 100,
    "studied": 50,
    "review_due": 20,
    "progress": 50.0  # 进度百分比
}
```

---

##### `get_all_books_with_progress() -&gt; List[Dict[str, Any]]`

获取所有词书及其进度信息。

**返回值**:
- 词书进度信息列表

---

##### `select_book(book_id: int) -&gt; bool`

选择当前学习的词书（保存到配置）。

**参数**:
- `book_id`: 词书 ID

**返回值**:
- 是否成功

---

##### `get_current_book() -&gt; Optional[Book]`

获取当前选择的词书。

**返回值**:
- 词书对象或 None

---

##### `delete_book(book_id: int) -&gt; bool`

删除词书。

**参数**:
- `book_id`: 词书 ID

**返回值**:
- 是否成功

---

### 学习服务 (src/recitation/study_service.py)

#### StudyService

```python
class StudyService:
    def __init__(self, dal: RecitationDAL, path_manager: PathManager)
```

**方法**:

##### `get_daily_new_words() -&gt; int`

获取每日新学单词数量（默认 20）。

**返回值**:
- 数量

---

##### `set_daily_new_words(count: int)`

设置每日新学单词数量。

**参数**:
- `count`: 数量

---

##### `get_daily_review_words() -&gt; int`

获取每日复习单词数量（默认 50）。

**返回值**:
- 数量

---

##### `set_daily_review_words(count: int)`

设置每日复习单词数量。

**参数**:
- `count`: 数量

---

##### `get_study_words(book_id: int, count: Optional[int] = None) -&gt; List[Word]`

获取未学习的新单词（随机排序）。

**参数**:
- `book_id`: 词书 ID
- `count`: 数量（可选，默认使用每日设置）

**返回值**:
- 单词列表

---

##### `get_review_words(book_id: int, count: Optional[int] = None) -&gt; List[Word]`

获取需要复习的单词（按权重排序）。

**参数**:
- `book_id`: 词书 ID
- `count`: 数量（可选，默认使用每日设置）

**返回值**:
- 单词列表

---

##### `get_today_words(book_id: int, force_refresh: bool = False) -&gt; Tuple[List[Word], List[Word]]`

获取今日学习和复习单词（智能缓存，每日自动刷新）。

**参数**:
- `book_id`: 词书 ID
- `force_refresh`: 是否强制刷新

**返回值**:
- `(new_words, review_words)` 元组

---

##### `refresh_today_words(book_id: int) -&gt; Tuple[List[Word], List[Word]]`

强制刷新今日单词（跳过本轮）。

**参数**:
- `book_id`: 词书 ID

**返回值**:
- `(new_words, review_words)` 新的单词列表元组

---

##### `start_study_word(book_id: int, word_id: int) -&gt; Optional[UserStudy]`

开始学习一个单词，初始化学习记录。

**参数**:
- `book_id`: 词书 ID
- `word_id`: 单词 ID

**返回值**:
- 学习记录对象，失败返回 None

---

##### `review_word(book_id: int, word_id: int, is_correct: bool) -&gt; Optional[UserStudy]`

复习一个单词，更新学习状态和下次复习时间。

**参数**:
- `book_id`: 词书 ID
- `word_id`: 单词 ID
- `is_correct`: 是否答对

**返回值**:
- 更新后的学习记录对象，失败返回 None

---

##### `start_study_batch_words(book_id: int, word_ids: List[int]) -&gt; List[Optional[UserStudy]]`

批量开始学习单词。

**参数**:
- `book_id`: 词书 ID
- `word_ids`: 单词 ID 列表

**返回值**:
- 学习记录对象列表

---

##### `review_batch_words(book_id: int, word_results: List[Tuple[int, bool]]) -&gt; List[Optional[UserStudy]]`

批量复习单词。

**参数**:
- `book_id`: 词书 ID
- `word_results`: `(word_id, is_correct)` 元组列表

**返回值**:
- 学习记录对象列表

---

##### `update_all_weights(book_id: int) -&gt; int`

更新词书所有单词的权重。

**参数**:
- `book_id`: 词书 ID

**返回值**:
- 更新的单词数量

---

### 艾宾浩斯算法 (src/recitation/ebbinghaus.py)

#### EbbinghausAlgorithm

```python
class EbbinghausAlgorithm:
    def __init__(self)
```

**方法**:

##### `calculate_initial_state() -&gt; Tuple[int, float, datetime, datetime]`

计算初始学习状态。

**返回值**:
- `(stage, weight, last_review, next_review)` 元组

---

##### `calculate_review_result(stage: int, weight: float, last_review: datetime, is_correct: bool) -&gt; Tuple[int, float, datetime, datetime]`

计算复习后的状态。

**参数**:
- `stage`: 当前阶段
- `weight`: 当前权重
- `last_review`: 上次复习时间
- `is_correct`: 是否答对

**返回值**:
- `(new_stage, new_weight, new_last_review, new_next_review)` 元组

---

##### `update_weight_current(stage: int, last_review: datetime, next_review: datetime) -&gt; float`

更新当前时间点的权重。

**参数**:
- `stage`: 当前阶段
- `last_review`: 上次复习时间
- `next_review`: 下次复习时间

**返回值**:
- 当前权重

---

**遗忘曲线阶段间隔**:
- 阶段 0: 5 分钟
- 阶段 1: 30 分钟
- 阶段 2: 12 小时
- 阶段 3: 1 天
- 阶段 4: 2 天
- 阶段 5: 4 天
- 阶段 6: 7 天
- 阶段 7: 15 天
- 阶段 8: 30 天

---

### 文章生成器 (src/recitation/article_generator.py)

#### ArticleGenerator

```python
class ArticleGenerator:
    @staticmethod
```

**方法**:

##### `format_article(article_text: str, new_words: List[Word], review_words: List[Word]) -&gt; str`

格式化文章：给新学单词加下划线（`<u>`），给复习单词加粗（`**`）。

**参数**:
- `article_text`: 原始文章文本
- `new_words`: 新学单词列表
- `review_words`: 复习单词列表

**返回值**:
- 格式化后的 Markdown 文本

---

##### `extract_title(article_text: str, max_length: int = 20) -&gt; str`

从文章第一句话提取标题。

**参数**:
- `article_text`: 文章文本
- `max_length`: 标题最大长度（默认 20）

**返回值**:
- 标题字符串

---

##### `save_article(workspace_path: str, article_text: str, title: str) -&gt; Tuple[bool, str]`

保存文章到工作区，按日期目录组织。

**参数**:
- `workspace_path`: 工作区路径
- `article_text`: 文章文本
- `title`: 标题

**返回值**:
- `(success, file_path_or_error)` 元组

---

##### `create_words_summary(new_words: List[Word], review_words: List[Word]) -&gt; str`

创建单词汇总（Markdown 格式）。

**参数**:
- `new_words`: 新学单词列表
- `review_words`: 复习单词列表

**返回值**:
- Markdown 格式的汇总文本

---

### 词书导入器 (src/recitation/book_importer.py)

#### BookImporter

```python
class BookImporter:
    def __init__(self)
```

**方法**:

##### `import_from_file(file_path: str) -&gt; Tuple[Optional[Book], List[Word]]`

从 JSON 文件导入词书。

**参数**:
- `file_path`: JSON 文件路径

**返回值**:
- `(book, words)` 元组，失败返回 `(None, [])`

---

### 背诵模式 UI (src/recitation/ui/)

#### RecitationMainPage

背诵模式主界面。

**主要功能**:
- 显示词书列表和学习进度
- 提供词书导入、选择、删除功能
- 展示今日新学和复习单词
- 支持生成文章和开始检测

#### QuizPage

单词检测界面。

**主要功能**:
- 展示单词并让用户自测
- 记录检测结果

#### RecitationSettingsPanel

背诵模式设置面板。

**主要功能**:
- 调整每日新学和复习单词数量

---

### 附录：配置文件格式

#### settings.json

```json
{
    "translation": {
        "enabled": false,
        "current_provider": "system_Ollama",
        "ollama": {
            "base_url": "http://localhost:11434",
            "model": "qwen2.5:0.5b"
        },
        "openai": {
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-3.5-turbo"
        }
    },
    "theme": "light",
    "window": { "width": 1200, "height": 800 },
    "prompt_templates": {
        "translation": "请翻译{input}",
        "analysis": "请解析{input}",
        "scenery": "请完成一篇包含{input}的文章"
    },
    "custom_models": [],
    "workspace": {
        "current_path": "",
        "current_file": "",
        "recent_files": [],
        "cell_states": {}
    },
    "reading": { "font_size": 12 }
}
```

#### .transnb 文件格式

```json
{
    "version": "1.0",
    "cells": [
        {
            "type": "markdown",
            "content": "源文本内容",
            "output": "翻译结果内容"
        }
    ]
}
```

#### 背诵模式配置文件格式 (studywordmode.json)

```json
{
    "current_book_id": 1,
    "daily_new_words": 20,
    "daily_review_words": 50,
    "today_date": "2025-01-15",
    "today_words_1": {
        "new_words": [1, 2, 3],
        "review_words": [10, 11, 12]
    }
}
```

---

### 附录：背诵模式数据库表结构

#### book 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| name | TEXT | 词书名称 |
| path | TEXT | 文件路径 |
| count | INTEGER | 单词数量 |
| create_time | TIMESTAMP | 创建时间 |

#### word 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| book_id | INTEGER | 外键 → book.id |
| word | TEXT | 单词 |
| phonetic | TEXT | 音标 |
| definition | TEXT | 释义 |
| example | TEXT | 例句 |
| raw_data | TEXT | 原始 JSON |

索引:
- `idx_word_book_id`: book_id

#### user_study 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| book_id | INTEGER | 外键 → book.id |
| word_id | INTEGER | 外键 → word.id |
| stage | INTEGER | 学习阶段 (0-8) |
| weight | REAL | 复习权重 |
| last_review | TIMESTAMP | 上次复习时间 |
| next_review | TIMESTAMP | 下次复习时间 |

索引:
- `idx_user_study_book_id`: book_id
- `idx_user_study_word_id`: word_id
- `idx_user_study_next_review`: next_review

