#!/usr/bin/env node
/**
 * cli.js — WebView 生成器命令行入口
 *
 * 用法：
 *   node src/cli.js --url https://example.com --name 我的应用
 *   node src/cli.js --url https://example.com --name 我的应用 --desktop --android
 *   node src/cli.js --url ... --name ... --kiosk
 */
'use strict';

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

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--url') args.url = argv[++i];
    else if (a === '--name') args.name = argv[++i];
    else if (a === '--out') args.out = argv[++i];
    else if (a === '--desktop') args.desktop = true;
    else if (a === '--android') args.android = true;
    else if (a === '--kiosk') args.kiosk = true;
    else if (a === '--fullscreen') args.fullscreen = true;
    else if (a === '--help' || a === '-h') args.help = true;
  }
  return args;
}

function help() {
  console.log(`
WebView 程序生成器 - 命令行版 v0.1.0

用法:
  node src/cli.js --url <服务器地址> --name <应用名> [选项]

必选:
  --url <url>       服务器地址，例如 https://books.example.com
  --name <name>     应用名称，例如 校园图书馆

选项:
  --desktop         生成 Windows 桌面端 (.exe)
  --android         生成安卓端 (.apk)
  --kiosk           借书机模式（安卓端：全屏/禁软键盘/防休眠）
  --fullscreen      桌面端全屏
  --out <dir>       输出目录（默认 ./dist）
  --help            显示帮助
  `);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) { help(); return; }

  try {
    const serverUrl = normalizeServerUrl(args.url);
    const appName = sanitizeAppName(args.name);
    const outRoot = path.resolve(args.out || './dist');

    // 默认如果没指定平台，全做
    const wantDesktop = args.desktop !== false;
    const wantAndroid = args.android !== false;

    console.log(`\n🚀 WebView 生成器 v0.1.0`);
    console.log(`   服务器: ${serverUrl}`);
    console.log(`   应用名: ${appName}`);
    console.log(`   输出目录: ${outRoot}\n`);

    // 环境检查
    const checks = checkEnv(wantAndroid);
    const missing = checks.filter(([, ok]) => !ok);
    if (missing.length) {
      console.log('⚠️  缺少以下环境依赖:');
      for (const [name] of missing) console.log(`   - ${name}`);
      console.log('   请先安装后重试 (详见 docs/ENVIRONMENT.md)\n');
      process.exitCode = 1;
      return;
    }

    const buildDir = path.join(outRoot, appName);
    fs.mkdirSync(buildDir, { recursive: true });

    const opts = {
      serverUrl,
      appName,
      kioskMode: !!args.kiosk,
      fullscreen: !!args.fullscreen,
      log: (m) => console.log(m),
    };

    const results = {};
    if (wantDesktop) {
      console.log('\n═════ 桌面端 (.exe) ═════');
      results.desktop = buildDesktop(opts, buildDir);
    }
    if (wantAndroid) {
      console.log('\n═════ 安卓端 (.apk) ═════');
      results.android = buildAndroid(opts, buildDir);
    }

    console.log('\n✅ 生成完成！产物位于:');
    for (const [k, v] of Object.entries(results)) {
      console.log(`   • ${k}: ${v}`);
    }
  } catch (e) {
    if (e instanceof BuilderError) {
      console.error(`\n❌ ${e.message}`);
    } else {
      console.error('\n❌ 发生错误:');
      console.error(e && e.stack ? e.stack : String(e));
    }
    process.exitCode = 1;
  }
}

main();
