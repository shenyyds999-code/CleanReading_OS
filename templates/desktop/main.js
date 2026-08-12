/**
 * {{APP_NAME}} — WebView 桌面壳主进程
 * 由 WebView 生成器自动生成，请勿手动修改。
 */
'use strict';

const { app, BrowserWindow } = require('electron');
const path = require('path');

const SERVER_URL = '{{SERVER_URL}}';
const WINDOW_WIDTH = parseInt('{{WINDOW_WIDTH}}', 10);
const WINDOW_HEIGHT = parseInt('{{WINDOW_HEIGHT}}', 10);
const FULLSCREEN = '{{FULLSCREEN}}' === 'true';

function createWindow() {
  const win = new BrowserWindow({
    width: WINDOW_WIDTH,
    height: WINDOW_HEIGHT,
    fullscreen: FULLSCREEN,
    title: '{{APP_NAME}}',
    autoHideMenuBar: true,          // 隐藏菜单栏，纯应用感
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  // 外部链接用系统浏览器打开，不在壳内跳走
  win.webContents.setWindowOpenHandler(({ url }) => {
    require('electron').shell.openExternal(url);
    return { action: 'deny' };
  });

  win.loadURL(SERVER_URL);

  win.webContents.on('did-fail-load', (_e, code, desc) => {
    if (code === -3) return; // 忽略中止
    win.loadFile(path.join(__dirname, 'index.html'));
  });

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
