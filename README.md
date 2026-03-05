# ModelScope 配额查询器

ModelScope API 配额查询桌面应用程序，支持查询模型级别和账户级别的剩余配额。

## 功能特性

- 📊 **实时配额查询** - 查询 ModelScope API 当日剩余额度
- 🖥️ **桌面 GUI** - 图形界面，操作简单直观
- 🔄 **多模型管理** - 支持同时添加多个模型（最多 10 个）
- 💾 **配置保存** - 自动保存模型列表和配置
- ⚡ **异步查询** - 界面不卡顿
- 🔒 **无窗口模式** - 可使用 `.pyw` 文件隐藏 DOS 窗口

## 环境要求

- Python 3.8+
- Windows 10/11

## 安装依赖

```bash
pip install requests
```

## 使用方法

### 方式 1：双击运行（推荐）

进入项目目录，双击 `quota_gui.pyw` 即可启动。

- `quota_gui.py` - 会显示 DOS 窗口（适合调试）
- `quota_gui.pyw` - 无 DOS 窗口，更干净

### 方式 2：命令行运行

```bash
python quota_gui.py
```

## 界面说明

```
<img width="749" height="531" alt="demo" src="https://github.com/user-attachments/assets/ae47426a-a080-4133-b8c6-d35e506fbeca" />

```

### 操作指南

1. **添加模型**：在底部输入框填写模型 ID（如 `Qwen/Qwen3.5-35B-A3B`），点击"添加模型"
2. **刷新配额**：选中模型后右键点击"刷新"，或点击"刷新账户配额"
3. **删除模型**：右键点击模型，选择"删除"
4. **查看详情**：表格显示总额度、已使用、剩余次数、使用率

## 配置文件

程序会自动创建 `config.json`，内容示例：

```json
{
  "api_key": "ms-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "api_url": "https://api-inference.modelscope.cn/v1/chat/completions",
  "models": [
    "Qwen/Qwen3.5-35B-A3B",
    "Qwen/Qwen3-8B-Chat"
  ]
}
```

### 修改配置

- **API Key**：直接编辑 `config.json` 中的 `api_key`
- **模型列表**：在 GUI 中添加/删除模型会自动保存

## 故障排除

### 问题：请求超时
- 检查网络连接
- 确认能访问 `api-inference.modelscope.cn`
- 尝试增加超时时间（修改代码中的 `timeout=15`）

### 问题：配额显示为 429
- 账户配额已用完，请明天再试
- 或更换 API Key

### 问题：显示乱码
- 确保使用 UTF-8 编码
- Windows Terminal 支持良好

## 技术栈

- Python 3.8+
- Tkinter（GUI）
- requests（HTTP 请求）
- threading（异步查询）

## 文件说明

| 文件 | 说明 |
|------|------|
| `quota_gui.py` | 主程序（含 GUI） |
| `quota_gui.pyw` | 无窗口启动器 |
| `config.json` | 配置文件（自动生成） |

## 注意事项

1. 需要有效的 ModelScope API Key
2. 配额每日刷新，具体时间参考 ModelScope 官方
3. 模型数量限制：最多 10 个
4. 确保网络可以访问 `api-inference.modelscope.cn`
