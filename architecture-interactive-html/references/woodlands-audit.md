# 本技能依据的 Woodlands 成果审计

这是参照案例的本地证据说明，仅用于理解怎样从已验证成果提取流程。以下路径、hash、数值和文件名不属于新项目的默认输入，不要求后续环境能访问这些绝对路径。

## 当前参照版本

- 主成果：`E:/人工智能/Codex/10/Woodlands_交互方案.html`。
- 源工程：`E:/人工智能/Codex/10/woodlands/`。
- 审计版本：2026-10-02，HTML SHA256 `9998461e3f047e27841eab5166067331b3ea39cfef14146d4507e7ecefff18bb`。
- 当前9章：场地、社区愿景/回应、形体、总图、剖面、功能、已建案例、比较、原册；另有模型首页。
- 源SKP、3方案、原册17页等均是本案例事实。技能不复制这些常量。

## 真正输入与派生资料

| 类别 | 原案例输入/处理证据 | 对新项目的含义 |
|---|---|---|
| 任务/文本 | `research/content-research.json`、原册；记录冲突/来源状态 | 用户任务书/原文，模型提取，不照搬60户/5m/面积上限 |
| 模型 | `※MP-OP.skp`、`assets/model/source_inventory.json`、`source_geometry.json` | 可读取源模型与当前解析工具；保存层级、变换和单位 |
| 几何映射 | `display-provenance.json`、`tools/export_web_models.py` | 源对象/面范围依据，避免材质合并mesh误框选 |
| 场地/配景 | context receipts、原底图、源树/车点位 | 真实场地输入、周边证据、配景授权；不自动生成地形 |
| 指标 | `research/masterplan-metrics.json`、原册表格、面积证据 | 每项目重新确认面积/计容口径与停车假设 |
| 功能/剖面 | `functions-source.json`、原生剖切平面/场景和source ID | 类别和切线据来源生成；未知楼层字段保持空 |
| 原册 | 原PDF、每页图、源页映射 | 任意实际页数和比例，生成阅读器，不固定17页 |
| 案例 | `community-cases.json`、`precedent-photo-receipts.json` | 当前项目的案例机制、官方身份和图片授权/署名 |
| 本地构建 | `tools/build_showcase.py`、本地Three/Orbit、字体许可证 | 采用实际可用工具，最终离线依赖全落实 |

用户不需要手工交这些JSON或receipt。它们是agent从原始资料提取、变换并验证产生的工作资料。

## 最值得复用的已验证行为

`src/app.js` 的状态同步、`viewport-chapters.js/css` 的图文同显与共享轨道、`functions.js` 的投影fit和热点解释、`book.js/css` 的原页读取和入口去重、`sections.js` 的真实源剖切，以及 `tools/render_subject_centered_thumbnails.cjs` 的源建筑face-range构图。

最新居中QA记录：`qa/subject-centering-9998461e3f04.json`。5种屏幕×中英文，30次实际方案模型打开，14张截图；center最大数值残差约2.27e-13px，最窄已测frame下主体留边约12.96px。这里的结果只适用该构建与已测矩阵。

独立源核对：`qa/subject-centering-source-9998461e3f04.json`。检查原152资产、25源模块、17研究文件、原17页及非thumbnail图片保持一致；独立根据原building roots/indexed Float32 vertices/实际相机重算bbox。新图只改取景/派生图片，不改源几何。

## 不能直接迁移的部分

- 多个模块和HTML控件固定OP1–OP3；build固定17页；通用化要改为数据驱动。
- 名称、地图、住宅类别、材料名/高度阈值、镜头角度/距离、图框范围、北向依据、配景点位、种子和案例照片都是项目特定。
- 原 `functions-source.json` 是资料证据，实际label/category与camera参数仍有源码常量；receipt不是运行配置。未来项目不能只替换一个PDF或模型JSON。
- 部分原指标路径没有完整null降级，案例/地图缺必要资产时会出错；本技能要求的新项目能力降级必须实际实现，不能声称旧源码已有。
- 原减少动态处理不等于所有模型初始化已停止自动旋转；未来实现要单独验证prefers-reduced-motion。
- 原册页宽、aspect、中文font subset、Three版本适配与多GPU测试是本环境细节，不强加给未来GPT。

因此此技能提供输入契约、流程、风格和验收，不能作为“复制现有50MB文件就自动适配所有项目”的承诺。后续模型需要据新资料建立manifest、实现/适配组件并真实验证。
