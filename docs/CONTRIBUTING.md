# 贡献指南 (CONTRIBUTING.md)

欢迎为 WebView 程序生成器贡献代码、文档或想法！本项目是 MIT 开源的校园/个人工具，由学生发起，鼓励互助。

---

## 🗺️ 从哪里开始

- 想报告 bug 或提功能建议 → 在 Gitee/GitHub 提 **Issue**
- 想改代码 → 先看 [DESIGN.md](./DESIGN.md) 了解架构，认领或建议一个任务
- 想补文档 → README / docs 里任何不清晰的地方都欢迎

---

## 🧭 代码规范

- 语言：Node.js，风格遵循项目现有（CommonJS，`'use strict'`）
- 提交信息：用一句话说清"做了什么"，推荐前缀：
  - `feat:` 新功能
  - `fix:` 修 bug
  - `docs:` 文档
  - `refactor:` 重构
  - `chore:` 杂务

示例：`fix: 服务器地址校验拒绝非 http 协议`

---

## 🔀 提 PR 的流程

1. Fork 本仓库
2. 建分支：`git checkout -b fix/xxx` 或 `feat/xxx`
3. 实现 + 自测（至少跑 `node --check` 和相关 CLI 测试）
4. 提交（看清上文规范）
5. 开 PR 并说明改动与为什么

---

## ✅ 提 PR 前的自测清单

- [ ] JS 语法：`node --check <文件>`
- [ ] JSON 合法：`node -e "JSON.parse(require('fs').readFileSync('package.json'))"`
- [ ] CLI 入口能跑：`node src/cli.js --help`
- [ ] URL 校验逻辑：`node src/cli.js --url bad` 应正确报错
- [ ] 不要把密钥 / `.env` / 个人数据提交上来

---

## 📝 文档约定

- 用户向文档（README / ENVIRONMENT）保持新手友好、步骤化
- 输出内容默认简体中文

谢谢你的贡献！🚀
