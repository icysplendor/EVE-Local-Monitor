# EVE Visual Alert (EWS)

![AI Generated](https://img.shields.io/badge/Code-AI%20Generated-f39f37) ![Python](https://img.shields.io/badge/Python-3.10+-3776ab) ![EVE Online](https://img.shields.io/badge/Game-EVE%20Online-cyan)

**EVE Visual Alert** represents a completely automated threat detection tool designed for EVE Online. It utilizes computer vision (OpenCV) to monitor specific screen regions for hostile indicators and provides audio/webhook alerts based on specific logic priorities.

**EVE Visual Alert** 是一个专为 EVE Online 设计的自动化威胁检测工具。利用计算机视觉（OpenCV）监控屏幕特定区域的敌对信号，并根据特定的逻辑优先级提供音频和 Webhook 警报。

---

## 🤖 A Note on AI Generation / 关于 AI 生成的说明

> **This project is 100% AI-generated.**
>
> Every line of code in this repository—from the PyQT6 graphical interface, the multi-threaded visual logic, to the configuration management—was written by an **AI Coding Agent** through a continuous conversational prompt session. No manual coding was performed by a human developer. This project serves as a demonstration of LLM capabilities in complex software engineering.

> **这个项目是 100% 由 AI 生成的。**
>
> 本仓库中的每一行代码——从 PyQT6 图形界面、多线程视觉逻辑，到配置管理系统——均由 **AI 编程智能体** 通过连续的对话指令生成。没有人类开发者手动编写任何代码。本项目旨在展示大语言模型（LLM）在复杂软件工程中的能力。

---
## 请注意，本程序现在仅在游戏缩放率为100%的情况下才可以使用！
## Please note that this program can only be used when the game scaling is 100%!

## ✨ Features / 功能特性

*   **Non-Intrusive Monitoring**: Uses screen capture analysis only. Does not read game memory or inject code. Safe and compliant with TOS (Screen Reader category).
    *   **非入侵式监控**：仅使用屏幕截图分析。不读取游戏内存，不注入代码。符合 TOS 安全标准（屏幕阅读器类别）。
*   **Sci-Fi UI**: A dark, compact, EVE-inspired interface utilizing PyQt6.
    *   **科幻 UI**：基于 PyQt6 构建的深色、紧凑、EVE 风格的界面。
*   **Logic-Based Audio Engine**:
    *   Determines threat priority (Overview > Local).
    *   Supports "Mixed Threat" alerts (e.g., detected rats AND hostiles simultaneously).
    *   **逻辑音频引擎**：智能判断威胁优先级（总览 > 本地），支持“混合威胁”警报（如同时检测到刷怪和敌对）。
*   **Template Matching**: Supports transparent PNGs for precise icon matching regardless of background nebula changes.
    *   **模板匹配**：支持带透明通道的 PNG 图片，无论背景星云如何变化都能精准识别图标。
*   **Webhook Support**: Can send JSON payloads to external services (like Discord) when alarms trigger.
    *   **Webhook 支持**：报警触发时可向外部服务（如 Discord）发送通知。
*   **Bilingual**: Instant switching between English and Chinese.
    *   **双语支持**：一键切换中文和英文界面。

## 🛠️ Installation / 安装

### Prerequisites / 前置要求
*   Windows 10/11 (High DPI supported)
*   Python 3.10+

### Setup / 配置步骤

1.  **Clone or Download** the repository.
    下载本仓库。
2.  **Install Dependencies**:
    安装依赖库：
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the Software**:
    运行软件：
    ```bash
    python main.py
    ```

---

## 📁 Usage Guide / 使用指南

### 1. Asset Preparation / 素材准备
The software requires you to provide template images to check against.
软件需要您提供用于比对的模板图片。

*   Go to the `assets` folder.
    进入 `assets` 文件夹。
*   **`assets/hostile_icons`**: Place images of hostile indicators (e.g., Red/Neutral symbols in Local/Overview).
    放入敌对指示图标（例如本地/总览中的红/白名图标）。
*   **`assets/monster_icons`**: Place images of ratting indicators (e.g., NPC names or icons).
    放入刷怪指示图标（例如 NPC 名字或图标）。

> **Tip**: Use small, cropped **PNG images with transparent backgrounds** for best results. Do not use full screenshots as templates.
> **提示**：请使用裁剪好的、带有**透明背景的小尺寸 PNG 图片**以获得最佳效果。切勿将整个屏幕截图作为模板。

### 2. Operation / 操作流程
1.  **Set Regions**: Click the buttons (Local/Overview/Rats) and draw a box over the corresponding area on your screen.
    **设定区域**：点击按钮（本地/总览/怪物），在屏幕对应位置画框。
2.  **Load Audio**: Select `.wav` or `.mp3` files for each alarm type.
    **加载音频**：为每种警报类型选择音频文件。
3.  **Threshold**: Adjust the similarity threshold (Recommended: 0.85).
    **阈值**：调整相似度阈值（推荐 0.85）。
4.  **ENGAGE**: Click to start monitoring.
    **启动**：点击“启动监控”。

---

## ⚠️ Disclaimer / 免责声明

**EVE Online Terms of Service Notice:**
This software functions as a screen reader and overlay. It **does not** automate inputs (keyboard/mouse simulation) and **does not** read game memory. While screen readers are generally considered "Grey Area" or allowable (similar to Discord Overlay or OBS), CCP Games has the final say.

**Use at your own risk. The author (and the AI) accepts no responsibility for bans or losses.**

**EVE Online 服务条款说明：**
本软件仅作为屏幕阅读器和覆盖层运行。它**不包含**任何输入自动化（模拟鼠标键盘），也**不读取**游戏内存。虽然屏幕阅读器通常被视为“灰色地带”或允许的辅助工具（类似于 Discord 覆盖或 OBS），但 CCP Games 拥有最终解释权。

**请自行承担使用风险。作者（以及 AI）不对账号封禁或资产损失承担任何责任。**

---

<p align="center">Generated with ❤️ by Intelligence</p>
