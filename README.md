# FrontierLab · 交通智能科研前沿工作台

一个无需前端构建工具的中文交通预测科研情报网站，适合通过 **GitHub Pages + GitHub Actions** 免费公开部署。覆盖多视角时空建模、自监督学习、动态图神经网络、事件引导交通预测、非周期扰动、天气/节假日等外部因素以及跨域泛化。

> 本项目区分 **自动发现候选** 和 **人工精选解读**。自动检索只提供可追溯元数据，不会自动给出无法核验的期刊等级、模型创新性或论文录用状态。

## 1. 直接部署到 GitHub Pages

**目标仓库**：`https://github.com/ZMLGoodLucky/research-frontier-hub`

1. 将此 ZIP 解压，把内部所有文件与文件夹上传到仓库 **根目录**，包括隐藏目录 `.github/workflows/`、`site/`、`scripts/`、`config/`、`data/`、`README.md`。
2. 进入仓库 **Settings → Pages**，在 **Build and deployment → Source** 下选择 **GitHub Actions**。
3. 打开仓库 **Actions → Daily Research Watch + GitHub Pages → Run workflow**。首次发布可能需要手动触发一次。
4. 到 **Settings → Pages** 查看实际部署链接。一般为：`https://zmlgoodlucky.github.io/research-frontier-hub/`。该地址只有 Pages 成功发布后才可用。

> 如果仓库没有上传按钮，请进入 Code → Add file → Upload files，并拖入解压后的文件。**注意**：网页版上传有时无法可靠保留 `.github` 隐藏目录和嵌套目录结构。建议使用 GitHub Desktop 或在仓库根目录上传后逐级检查文件路径。使用 Git 命令见后文。

### 使用 Git 命令上传（更可靠）

```bash
git clone https://github.com/ZMLGoodLucky/research-frontier-hub.git
cd research-frontier-hub
# 将 ZIP 解压后的内容复制到当前目录（保留 .github 隐藏文件夹）
git add .
git commit -m "feat: launch FrontierLab research dashboard"
git push origin main
```

### 每日自动更新

GitHub Actions 计划 **每天北京时间 09:00（UTC 01:00）**运行；GitHub 定时任务可能延迟。无新成果时不会杜撰新条目，仍会保存采集状态。它将：

1. 使用 OpenAlex 检索发表日期位于最近14天的道路交通预测相关论文（14 天是漏检回补窗口，并不代表每天都会新增论文）；
2. 使用 arXiv API 发现新增预印本；
3. 使用 MIT News RSS 发现与交通或时空建模有关的机构资讯（无匹配时为零）；
4. 去重并保存 `site/data.json` 和 `site/seed.js`，随后重新部署站点。

如数据源异常，工作流保留旧记录并在 `fetch_status` 里记录错误。OpenAlex 当前支持无密钥的低频检索；注册免费 API Key 可提高配额：仓库 **Settings → Secrets and variables → Actions → New repository secret**，名称 `OPENALEX_API_KEY`。不强制配置。

## 2. 研究内容维护

| 文件 | 用途 |
| --- | --- |
| `site/index.html` | 完整中文网站结构 |
| `site/styles.css` | 响应式研究仪表板样式 |
| `site/app.js` | 搜索、筛选、收藏、详情、导出 |
| `site/data.json` | 网站内容数据，自动生成 |
| `data/curated.json` | 人工核实与精选记录，优先于自动候选 |
| `data/feeds.json` | 高校等机构 RSS 列表 |
| `config/interests.json` | 研究方向、关键词、自动收集时间范围 |
| `scripts/collect.py` | 每日采集程序，仅 Python 标准库 |
| `.github/workflows/research-weekly.yml` | GitHub 定时更新与 Pages 发布工作流 |

**新增公众号文章**：在 `data/curated.json` 新增 `type: "insight"` 的对象，保留真实原文链接、发布日期、发布主体、中文研究解读。由于微信公众号不提供可靠的开放检索 API，此站默认不自动抓取公众号内容，更不会伪造某公众号的内容。

**投稿期刊 / 会议级别**：维护 `level` 时应注明分类体系及版本，例如“中科院分区（2026版，已核对）”或“CCF 2026目录 A 类（已核对）”。JCR Quartile、中科院分区、CCF 推荐等级并不等价；无验证时维持“待核验”。arXiv 不等于录用。

**安全性**：静态站点的收藏数据只保存在本地浏览器的 `localStorage`，不上传服务器。不要把私有数据、密钥或论文审稿材料放在公开仓库。

## 3. 本地测试

```bash
python scripts/collect.py --offline
cd site
python -m http.server 8000
```

浏览器访问 `http://localhost:8000`。静态网页也可以直接双击 `site/index.html`，会使用 `seed.js` 作为浏览器的离线数据回退。

```bash
python -m unittest discover -s tests -v
```

## 4. 当前能力边界

- **已实现**：精选研究解读、在线来源链接、中文方向分类、时间筛选、搜索、本地收藏与 JSON 导出、响应式布局、自动抓取 OpenAlex/arXiv、MIT News RSS、GitHub Actions 计划任务和 Pages 自动部署。
- **需要人工维护**：刊会年份及等级核验、创新性与比较结论、全文实验审读、代码地址验证、公众号文章审核。
- **不会自动生成**：无法可靠验证的中科院分区、CCF 等级、作者声明以外的正式录用结果、模型性能和实验结论。

## 5. 许可与引用

本项目仅记录公开元数据、少量编辑性中文概括及原文链接。请以各出版社、会议和数据平台的原始记录为准。采集源及发布日期会明确列出，不进行文章全文转载。
