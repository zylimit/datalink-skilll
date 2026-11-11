# Project: datalink-skill
_Last updated: 2026-11-12_

## Pinned（仅高置信"必须遵守"写入；受保护不可修订）
    - 本流程工作空间点顶栏 France FBB，不沿用页面上碰巧已选的空间（依据：用户说「这里我们选择 France FBB」；适用范围：这条已教的 DataLink 编排流程；其他任务是否换空间还没定）
    - 新建应用场景只点「空白应用」；进表单只点「空白页面」（依据：用户说新建目前只选空白应用场景，表单入口框的是空白页面；适用范围：新建这条路；打开已有场景不走新建弹窗）
    - 从画布删除字段必须在确认框输入 Delete（依据：页面规则，用户要求删掉新增字段并认可结果；适用范围：表单设计画布上的字段删除；回收站里的彻底删除还没做）
    - 看完的图片马上删除（依据：用户说「图片看完就删除」；适用范围：用户发来的图和操作 DataLink 时自己截的图）

## Decisions（按时间顺序追加，历史不可改；三要素缺一不算决策）
    - 2026-11-12: 已经学到的 DataLink 操作和字段属性写在 `.claude/skills/datalink/references/confirmed-operations.md`，由 `.claude/skills/datalink/SKILL.md` 当参考来读（依据：用户说「目前已经学到的，落盘，作为 Skill 的参考」；适用范围：DataLink 表单编排；取代：无）
    - 2026-11-12: 流程启用后不能再拖节点，子流程的数据传递不再继续查（依据：用户说「流程启动就是拖不进去，放弃」；适用范围：已启用的工作流；取代：无）

## TODO（权威待办清单）
    - [P1][OPEN][#1] 继续学参考里还没教完的步骤：打开已有场景、命名实操、保存、发布、公式和跨表取值（Context：.claude/skills/datalink/references/confirmed-operations.md「还没教完」）

## In Progress

## Done（最近完成的放前面）
    - 2026-11-12: 学完表单设置 10 个页签和全局配置，补进技能参考（evidence：.claude/skills/datalink/references/confirmed-operations.md）
    - 2026-11-12: 落盘 DataLink 技能参考，含操作顺序和 26 个基础/增强字段的属性（evidence：.claude/skills/datalink/references/confirmed-operations.md）

## Risks & Assumptions
    - Risk：字段属性来自一次点选，公式、跨表、水印等子弹层没进，条件默认值可能看漏（Mitigation：参考里标了待定，技能遇到这些就停）
    - Assumption：France FBB 只固定在这条已教流程上（Confidence：Med）

## Notes（简要要点）
    - 2026-11-12: 核对环境是德国站 https://datalink-de.gtsdata.huawei.com/ ，可见 Chrome。研究用的表单是应用001 / 表单001，临时字段已从画布删除。

## Context Index（轻量索引）
    - Skill：.claude/skills/datalink/SKILL.md
    - Reference：.claude/skills/datalink/references/confirmed-operations.md
