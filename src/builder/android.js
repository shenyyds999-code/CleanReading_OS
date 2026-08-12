/**
 * android.js — 安卓端 (.apk) 打包逻辑
 *
 * 采用 Gradle 原生工程：
 *  - templates/android/gradle/  工程根文件（settings/build/gradle.properties/app.gradle）
 *  - templates/android/src/     app/src/main 内容（Manifest/java/res）
 *  - 组装成完整 Gradle 工程后 gradlew assembleDebug 出可侧载 apk
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
  toPackageId,
} = require('./common');

const ANDROID_TPL = path.join(TEMPLATES, 'android');
const SRC_MAIN = path.join('app', 'src', 'main');

/**
 * 生成安卓工程
 * @param {object} opts { serverUrl, appName, kioskMode }
 * @param {string} outDir 输出工程目录（<out>/<name>/src）
 */
function scaffoldAndroid(opts, outDir) {
  if (!fs.existsSync(ANDROID_TPL)) throw new BuilderError('缺少安卓端模板：' + ANDROID_TPL);

  // 1. 镜像工程根文件 → outDir/
  copyDir(path.join(ANDROID_TPL, 'gradle'), outDir);

  // 2. 镜像 app/src/main → outDir/app/src/main
  const appMain = path.join(outDir, SRC_MAIN);
  copyDir(path.join(ANDROID_TPL, 'src', 'main'), appMain);

  // 3. 计算 java 源码目标路径
  const pkg = toPackageId(opts.appName);
  const javaSrc = path.join(
    outDir, SRC_MAIN, 'java', ...'com.generated.webview'.split('.')
  );

  // 4. 渲染 MainActivity
  renderTemplate(path.join(ANDROID_TPL, 'src', 'main', 'java', 'com', 'generated', 'webview', 'MainActivity.java'), {
    SERVER_URL: opts.serverUrl,
    APP_NAME: opts.appName,
    KIOSK_MODE: opts.kioskMode ? 'true' : 'false',
  }, path.join(javaSrc, 'MainActivity.java'));

  // 5. 渲染 AndroidManifest —— 应用名
  renderTemplate(path.join(ANDROID_TPL, 'src', 'main', 'AndroidManifest.xml'), {
    APP_NAME: opts.appName,
  }, path.join(outDir, SRC_MAIN, 'AndroidManifest.xml'));

  // 6. 渲染 app/build.gradle —— applicationId
  renderTemplate(path.join(ANDROID_TPL, 'gradle', 'app.gradle'), {
    PACKAGE_ID: pkg,
  }, path.join(outDir, 'app', 'build.gradle'));

  return outDir;
}

/**
 * 打包安卓工程为 .apk
 * @param {object} opts 同上
 * @param {string} buildDir 输出构建目录
 */
function buildAndroid(opts, buildDir) {
  const srcDir = path.join(buildDir, 'src');
  scaffoldAndroid(opts, srcDir);

  const log = opts.log || console.log;
  log(`[android] 生成 Gradle 安卓工程 → ${srcDir}`);
  log(`[android] 构建 debug APK (可侧载安装) ...`);

  const gradlew = path.join(srcDir, 'gradlew');
  const cmd = fs.existsSync(gradlew) ? './gradlew' : 'gradle';
  if (!run(`${cmd} assembleDebug --console=plain`, srcDir, log)) {
    throw new BuilderError('安卓 apk 打包失败（请确认已安装 JDK 与 Android SDK）');
  }

  return path.join(srcDir, 'app', 'build', 'outputs', 'apk', 'debug');
}

module.exports = { scaffoldAndroid, buildAndroid };
