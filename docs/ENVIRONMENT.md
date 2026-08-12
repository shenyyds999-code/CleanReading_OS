# 打包环境准备 (ENVIRONMENT.md)

本工具把 Web 应用打包成 `.exe` 和 `.apk`，需要对应平台的构建环境。以下是一份面向新手的完整搭建指南。

---

## 一、通用要求（无论打什么包）

| 软件 | 版本 | 用途 |
|------|------|------|
| Node.js | 18+ | 生成器本身运行 |
| npm | 随 Node | 安装依赖 |

安装 Node.js：到 https://nodejs.org 下载 LTS 版本，一路默认安装即可。

验证：

```bash
node -v   # 例如 v20.11.0
npm -v    # 例如 10.2.4
```

---

## 二、打包 Windows 桌面端 (.exe)

生成 `.exe` 需要 **Windows 系统**（或用带 wine 的 Linux）。

| 软件 | 用途 |
|------|------|
| Windows 10/11 | 打包 exe 的主机 |
| Node.js 18+ | 同通用要求 |

> 说明：electron-builder 需要在能运行 Windows 安装器的环境里产出可安装的 `.exe`。

### 验证环境是否就绪

```bash
node node_modules/electron-builder/cli.js --version
```

能输出版本号即 OK。

---

## 三、打包安卓端 (.apk)

生成 `.apk` 需要 **JDK + Android SDK**。

### 1. 安装 JDK 17+

- Windows/Mac：到 https://adoptium.net 下载 Temurin 17，安装
- 验证：

```bash
java -version   # 应显示 version "17.x"
```

### 2. 安装 Android SDK

推荐用 **Android Studio**（免费）一并安装 SDK：

1. 到 https://developer.android.com/studio 下载安装 Android Studio
2. 首次启动会提示安装 SDK，安装默认 Android 14（API 34）即可
3. 记录 SDK 路径（Windows 通常在 `C:\Users\<你的用户名>\AppData\Local\Android\Sdk`）

### 3. 配置环境变量

设置 `ANDROID_HOME` 指向你的 SDK 路径：

**Windows（PowerShell）**：
```powershell
setx ANDROID_HOME "C:\Users\<你>\AppData\Local\Android\Sdk"
```

**macOS / Linux**（写入 `~/.bashrc` 或 `~/.zshrc`）：
```bash
export ANDROID_HOME=$HOME/Library/Android/sdk   # macOS
# 或
export ANDROID_HOME=$HOME/Android/Sdk           # Linux
export PATH=$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin
```

重启终端使环境变量生效。

### 4. 验证

```bash
java -version
echo $ANDROID_HOME    # 应输出 SDK 路径
```

若两者正常，即可用生成器打包 apk。

---

## 四、常见问题

| 问题 | 原因/解决 |
|------|----------|
| `Command 'gradle' not found` | 本项目用包装脚本 gradlew，或用 Android Studio 内置的 Gradle。确认已装 JDK |
| apk 安装后提示"未知来源" | 我们默认产未签名的 debug apk，需在手机开启"允许安装未知来源应用"（详见 README） |
| `no valid Android SDK` | ANDROID_HOME 没配好，或 SDK 未装 API 34，回到第三节 |
| exe 打包慢/卡 | electron-builder 首次要下载 Electron 与 NSIS，耐心等待 |

---

## 五、环境自检脚本

生成器自带环境检查功能（GUI 界面会自动显示 ✓/✗）。命令行可这样快速检查：

```bash
node -e "const c=require('./src/builder/common');console.table(c.checkEnv(true))"
```

`true` 表示检查安卓环境，`false` 只检查 Node/npm。
