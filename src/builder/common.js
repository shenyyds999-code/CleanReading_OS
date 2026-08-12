/**
 * common.js — WebView 生成器核心引擎
 *
 * 职责：
 *  - 校验并规范化输入（服务器地址、应用名）
 *  - 生成三端 WebView 壳工程（基于 templates/ 模板渲染）
 *  - 图标归一化（转成各端需要的格式）
 *  - 输出目录编排
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT = path.join(__dirname, '..');
const TEMPLATES = path.join(ROOT, 'templates');

class BuilderError extends Error {
  constructor(message) {
    super(message);
    this.name = 'BuilderError';
  }
}

/** 规范化服务器地址：去掉末尾斜杠，检测必需协议 */
function normalizeServerUrl(raw) {
  if (!raw || !raw.trim()) {
    throw new BuilderError('服务器地址不能为空');
  }
  let url = raw.trim();
  // 已含协议但非 http/https → 直接拒绝
  if (/^[a-z][a-z0-9+.-]*:\/\//i.test(url) && !/^https?:\/\//i.test(url)) {
    throw new BuilderError('服务器地址只支持 http/https 协议');
  }
  // 没有协议则默认补 https://
  if (!/^https?:\/\//i.test(url)) {
    url = 'https://' + url;
  }
  let parsed;
  try {
    parsed = new URL(url);
  } catch (e) {
    throw new BuilderError('服务器地址不是合法的 URL：' + raw);
  }
  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    throw new BuilderError('服务器地址只支持 http/https 协议');
  }
  // 去掉末尾斜杠
  return url.replace(/\/+$/, '');
}

/** 校验应用名：只保留安全字符，避免路径/包名出问题 */
function sanitizeAppName(name) {
  if (!name || !name.trim()) {
    throw new BuilderError('应用名称不能为空');
  }
  const clean = name.trim().replace(/[^\w\u4e00-\u9fff-]+/g, '');
  if (!clean) {
    throw new BuilderError('应用名称只能包含中文、字母、数字、下划线或连字符');
  }
  return clean;
}

/** 生成一个安全的 Android applicationId（包名） */
function toPackageId(appNameCn) {
  // 取拼音/英文部分，转成小写点分形式 demo.app
  const ascii = appNameCn.replace(/[^\w-]/g, '').toLowerCase();
  const base = ascii || 'webview';
  return `com.generated.${base}`;
}

/** 渲染一个模板：把 {{VAR}} 替换成实际值 */
function renderTemplate(templatePath, vars, destPath) {
  let content = fs.readFileSync(templatePath, 'utf8');
  for (const [k, v] of Object.entries(vars)) {
    content = content.split(`{{${k}}}`).join(String(v));
  }
  fs.mkdirSync(path.dirname(destPath), { recursive: true });
  fs.writeFileSync(destPath, content, 'utf8');
}

/** 递归拷贝目录 */
function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(s, d);
    } else {
      fs.copyFileSync(s, d);
    }
  }
}

/** 运行子进程并回传日志 */
function run(cmd, cwd, log) {
  log && log(`  $ ${cmd}`);
  try {
    execSync(cmd, { cwd, stdio: ['ignore', 'pipe', 'pipe'] });
    return true;
  } catch (e) {
    const err = Buffer.from(e.stderr || '').toString();
    log && log('  ❌ 命令失败:');
    log && log(err.split('\n').slice(0, 20).join('\n'));
    return false;
  }
}

/** 检查生成所需的系统工具是否存在 */
function checkEnv(needAndroid) {
  const checks = [];
  const has = (cmd) => {
    try { execSync(`${cmd} --version`, { stdio: 'ignore' }); return true; }
    catch { return false; }
  };
  checks.push(['node', has('node')]);
  checks.push(['npm', has('npm')]);
  if (needAndroid) {
    checks.push(['java', has('java')]);
    checks.push(['gradle', has('gradle')]);
    checks.push(['Android SDK (ANDROID_HOME)', !!process.env.ANDROID_HOME]);
  }
  return checks;
}

module.exports = {
  ROOT,
  TEMPLATES,
  BuilderError,
  normalizeServerUrl,
  sanitizeAppName,
  toPackageId,
  renderTemplate,
  copyDir,
  run,
  checkEnv,
};
