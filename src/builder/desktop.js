/**
 * desktop.js — Windows 桌面端 (.exe) 打包逻辑
 *
 * 采用 Electron + electron-builder：
 *  - 生成一个最小 Electron 壳工程
 *  - 壳内 BrowserWindow 加载用户填写的服务器地址
 *  - 配置无障碍/窗口选项（隐藏地址栏、可选全屏/kiosk）
 */
'use strict';

const fs = require('fs');
const path = require('path');
const {
  TEMPLATES,
  BuilderError,
  renderTemplate,
  copyDir,
  run,
} = require('./common');

/**
 * 生成桌面壳工程
 * @param {object} opts { serverUrl, appName, windowWidth, windowHeight, fullscreen }
 * @param {string} outDir  输出工程目录（<输出>/<应用名>/dist/windows/src）
 */
function scaffoldDesktop(opts, outDir) {
  const tpl = path.join(TEMPLATES, 'desktop');
  if (!fs.existsSync(tpl)) throw new BuilderError('缺少桌面端模板：' + tpl);

  // 拷贝模板
  copyDir(tpl, outDir);

  // 渲染 package.json（主进程名、应用名）
  renderTemplate(path.join(tpl, 'package.json'), {
    APP_NAME: opts.appName,
    APP_ID: `com.generated.${opts.appName}`,
  }, path.join(outDir, 'package.json'));

  // 渲染 index.html（壳页面，含加载/错误提示）
  renderTemplate(path.join(tpl, 'index.html'), {
    APP_NAME: opts.appName,
  }, path.join(outDir, 'index.html'));

  // 渲染主进程 main.js —— 注入服务器地址与窗口配置
  renderTemplate(path.join(tpl, 'main.js'), {
    SERVER_URL: opts.serverUrl,
    WINDOW_WIDTH: opts.windowWidth || 1280,
    WINDOW_HEIGHT: opts.windowHeight || 800,
    FULLSCREEN: opts.fullscreen ? 'true' : 'false',
    APP_NAME: opts.appName,
  }, path.join(outDir, 'main.js'));

  return outDir;
}

/**
 * 打包 desktop 工程为 .exe
 * @param {object} opts 同上
 * @param {string} buildDir 输出构建目录
 */
function buildDesktop(opts, buildDir) {
  const srcDir = path.join(buildDir, 'src');
  scaffoldDesktop(opts, srcDir);

  const log = opts.log || console.log;
  log(`[desktop] 生成 Electron 壳 → ${srcDir}`);
  log(`[desktop] 安装依赖 (首次较慢)...`);

  if (!run('npm install', srcDir, log)) {
    throw new BuilderError('桌面端依赖安装失败');
  }

  log(`[desktop] 打包 .exe ...`);
  // electron-builder 生产安装包；--win 在 Windows 上产出 nsis exe
  if (!run('npx electron-builder --win', srcDir, log)) {
    throw new BuilderError('桌面端 exe 打包失败');
  }

  return path.join(srcDir, 'dist');
}

module.exports = { scaffoldDesktop, buildDesktop };
