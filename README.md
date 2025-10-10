# Corona Engine Editor
- 此仓库为 Corona Engine 的编辑器
- 前端 Web：
	- 基于 Node.js（Vue + Tailwind）
	- 实现基于积木可视化编程（类似 Scratch），积木运行时转为 Python
- 后端/脚本层 Python：
	- 基于 MCP 接入大模型
	- 使用 PyQt6 的 QWebEngineView 及 QDockWidget 搭建前端界面布局
- 底层 C++：
	- 支持 Python 层的热重载，保存文件自动更新 Python 代码逻辑
  
### 环境配置
- 运行 `build.py` 将自动下载/使用本地 Node.js，并安装前端依赖并构建前端；同时检查并安装 Python 依赖（`requirements.txt`）
- Python 层可独立运行
	- 程序入口为 `Backend/main.py`（建议使用模块方式运行，确保导入路径正确：`python -m Backend.main`）
- Web 层可独立运行
	- 代码位于 `Frontend/`
