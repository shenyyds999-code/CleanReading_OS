/**
 * main.js — WebView 生成器 Electron 主进程 (GUI)
 *
 * 打开一个图形窗口：输入服务器地址 + 应用名 → 勾选平台 → 一键生成。
 */
'use strict';

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { buildDesktop } = require('./builder/desktop');
const { buildAndroid } = require('./builder/android');
const {
  normalizeServerUrl,
  sanitizeAppName,
  checkEnv,
  BuilderError,
} = require('./builder/common');

function createWindow() {
  const win = new BrowserWindow({
    width: 720,
    height: 680,
    title: 'WebView 程序生成器',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  win.loadFile(path.join(__dirname, 'renderer', 'index.html'));
  return win;
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// —— 生成请求 ——
ipcMain.handle('build', async (_evt, payload) => {
  const { serverUrl, appName, wantDesktop, wantAndroid, kiosk, fullscreen, outDir } = payload;
  try {
    const url = normalizeServerUrl(serverUrl);
    const name = sanitizeAppName(appName);

    const logs = [];
    const log = (m) => logs.push(m);

    const buildDir = path.resolve(outDir || './dist');
    fs.mkdirSync(buildDir, { recursive: true });

    const opts = { serverUrl: url, appName: name, kioskMode: !!kiosk, fullscreen: !!fullscreen, log };

    const results = {};
    if (wantDesktop) {
      log('═════ 桌面端 (.exe) ═════');
      results.desktop = buildDesktop(opts, buildDir);
    }
    if (wantAndroid) {
      log('═════ 安卓端 (.apk) ═════');
      results.android = buildAndroid(opts, buildDir);
    }

    return { ok: true, results, logs };
  } catch (e) {
    return {
      ok: false,
      error: e instanceof BuilderError ? e.message : String(e && e.stack || e),
      logs,
    };
  }
});

// —— 环境检查 ——
ipcMain.handle('check-env', (_evt, wantAndroid) => {
  return checkEnv(!!wantAndroid)
    .map(([name, ok]) => ({ name, ok }));
});
