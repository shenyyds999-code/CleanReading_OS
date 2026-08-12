/**
 * preload.js — 在渲染进程安全暴露构建能力
 */
'use strict';

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  build: (payload) => ipcRenderer.invoke('build', payload),
  checkEnv: (wantAndroid) => ipcRenderer.invoke('check-env', wantAndroid),
});
