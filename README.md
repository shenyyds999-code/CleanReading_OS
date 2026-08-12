# 🚀 WebView 程序生成器 (WebView Builder)

> **输入一个服务器地址，一键生成三端安装包**：Windows 桌面端 (.exe) + 安卓借书机端 + 安卓手机端 (.apk)。

一个开源的 **Web 应用打包工具**：任何网站 / Web 系统，填个网址就能封装成能独立安装运行的桌面程序和安卓 App。适合用来打包**学校管理系统、借阅系统、企业内部工具、个人项目**等。

本项目正在开发中（v0.1-draft），核心骨架与打包逻辑已完成，可运行生成简易安装包。

---

## ✨ 它能做什么

把任意 Web 应用打包成三种形态：

| 端 | 产物 | 典型用途 |
|----|------|---------|
| 🖥️ 桌面端 | `.exe` | 查书电脑、管理终端（隐藏浏览器地址栏，纯应用感） |
| 📱 安卓触屏端 | `.apk` | 借书机（全屏 / 禁软键盘 / 防休眠 / 配合扫码枪） |
| 📱 安卓手机端 | `.apk` | 校外移动访问（登录态持久化） |

配合 **CleanReading OS 校园图书馆系统** 使用效果最佳（本项目最初就是为它设计的打包工具）。

---

## 🧰 技术栈

- **桌面端**：Electron + electron-builder
- **安卓端**：原生 Android WebView + Gradle
- **生成器本体**：Node.js（Electron GUI + CLI 双入口）
- **许可证**：MIT

---

## ⚙️ 快速开始

### 环境要求
- [ ] Node.js 18+
- [ ] （可选）打包 `.apk` 需要 JDK 17+ 与 Android SDK（详见 `docs/ENVIRONMENT.md`）
- [ ] （可选）打包 `.exe` 需要 Windows 或带 wine 的 Linux

### 用命令行（最简）

```bash
# 安装依赖
npm install

# 一键生成桌面端 + 手机端 apk
node src/cli.js --url https://books.example.com --name 校园图书馆

# 仅生成借书机端（kiosk 模式）
node src/cli.js --url https://books.example.com --name 校园图书馆 --kiosk --desktop=false
```

产物输出到 `./dist/<应用名>/`。

### 用图形界面

```bash
npm start
```
打开可视化窗口，填地址、勾平台、点"一键生成"。

---

## 📁 项目结构

```
webview-builder/
├── src/
│   ├── main.js              # Electron GUI 主进程
│   ├── preload.js           # 安全桥接
│   ├── renderer/            # GUI 界面
│   ├── cli.js               # 命令行入口
│   └── builder/
│       ├── common.js        # 核心引擎（URL校验/模板渲染/环境检查）
│       ├── desktop.js       # exe 打包
│       └── android.js       # apk 打包
├── templates/
│   ├── desktop/             # Electron 壳模板
│   └── android/             # Gradle 安卓工程模板
├── docs/
│   ├── DESIGN.md            # 设计方案
│   └── ENVIRONMENT.md       # 打包环境准备
├── LICENSE
└── README.md
```

---

## 🗺️ 开发路线图

- [x] M0 环境 + 项目骨架
- [ ] M1 MVP：GUI + CLI + 桌面 exe 打包
- [ ] M2 借书机专项：kiosk 全屏 / 禁软键盘 / 扫码枪
- [ ] M3 体验完善：图标上传 / 窗口配置 / PWA
- [ ] M4 开源化：完整文档 / 贡献指南

---

## 🧪 当前状态

- ✅ 核心引擎（common.js）完成
- ✅ 桌面端打包逻辑（Electron 壳）
- ✅ 安卓端打包逻辑（Gradle 工程 + kiosk 模式）
- ✅ GUI + CLI 双入口
- 🔄 模板与资源文件完善中
- ⏳ 打包环境文档 & 端到端实测

---

## 📄 许可证

[MIT](./LICENSE)

## 🤝 贡献

欢迎提交 Issue 与 PR。请阅读 `docs/CONTRIBUTING.md`（规划中）。
