---
name: Crop Guard Platform
description: 农作物病虫害智能检测平台视觉系统
colors:
  primary: "#0d9488"
  primary-deep: "#0f766e"
  primary-light: "#ccfbf1"
  success: "#22c55e"
  accent-green: "#16a34a"
  text-primary: "#1f2937"
  text-secondary: "#6b7280"
  border: "#e5e7eb"
  surface: "#ffffff"
  background: "#f0fdfa"
  background-muted: "#f9fafb"
typography:
  body:
    fontFamily: "Avenir, Helvetica, Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.6
  title:
    fontFamily: "Avenir, Helvetica, Arial, sans-serif"
    fontSize: "18px"
    fontWeight: 600
    lineHeight: 1.4
  display:
    fontFamily: "Avenir, Helvetica, Arial, sans-serif"
    fontSize: "24px"
    fontWeight: 700
    lineHeight: 1.3
  label:
    fontFamily: "Avenir, Helvetica, Arial, sans-serif"
    fontSize: "12px"
    fontWeight: 500
    lineHeight: 1.5
    letterSpacing: "0.02em"
rounded:
  sm: "6px"
  md: "10px"
  lg: "16px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  xxl: "48px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "10px 24px"
  button-primary-hover:
    backgroundColor: "{colors.primary-deep}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "10px 24px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "10px 14px"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
---

# Design System: Crop Guard Platform

## 1. Overview

**Creative North Star: "田间晨露"**

清晨的田野，露珠挂在叶尖，空气清新而温和。这个平台应该给人同样的感受：干净、清新、让人安心。不追求炫酷的技术感，不堆砌华丽的装饰，而是像一个可靠的农技伙伴，用温暖而专业的方式帮助用户完成检测任务。

系统明确拒绝 PRODUCT.md 中列出的四类反面参考：极客暗黑风格（黑底霓虹、过度动效）、儿童科普风格（卡通化、配色幼稚）、传统农业系统（过时表格堆砌）、SaaS 模板风格（渐变泛滥、卡片套卡片）。

**Key Characteristics:**
- 清新自然的色彩：以青绿为主调，搭配温暖的中性色，营造田间清晨的舒适感
- 圆润柔和的形态：大圆角、柔和阴影，避免尖锐和生硬
- 克制的信息密度：留白充足，信息层次分明，不堆砌
- 一致的组件语言：全平台统一的按钮、表单、卡片样式

## 2. Colors: 清晨田野的色调

以青绿色为主色调，搭配暖灰色中性色。整体色调偏暖不偏冷，营造自然、舒适、可信赖的视觉感受。

### Primary
- **青绿** (#0d9488): 平台的核心色彩，用于主按钮、选中态、导航高亮、品牌标识。是田间叶片的生命色，传递健康与专业的信号。
- **深青绿** (#0f766e): 主色的悬停态和按压态，比主色深一度，提供清晰的交互反馈。
- **青绿薄纱** (#ccfbf1): 主色的极浅版本，用于选中行背景、标签底色、提示区域，不喧宾夺主。

### Neutral
- **墨灰** (#1f2937): 正文文本色，深而不黑，阅读舒适。
- **雾灰** (#6b7280): 次要文本、说明文字、占位符，降低信息层级。
- **银线** (#e5e7eb): 边框、分割线、表单轮廓，轻量不突兀。
- **纯白** (#ffffff): 卡片、表单、弹窗背景，与页面底色形成层次。
- **晨雾** (#f0fdfa): 页面全局背景色，带一丝青绿暖意，不是冰冷的纯白。
- **薄雾灰** (#f9fafb): 次级面板、侧边栏背景，与晨雾形成微妙层次。

### Semantic
- **新绿** (#22c55e): 成功状态、完成提示、健康指标。
- **翠绿** (#16a34a): 强调绿，用于重要标签或数值。

### Named Rules

**The 露珠规则。** 主色（青绿）在任意页面上的面积占比不超过 15%。它的稀缺性赋予它信号价值：当用户看到青绿色，就知道"这是可以操作的地方"。大面积使用主色会让界面变成主题公园，而非工具。

**The 暖灰规则。** 所有中性色（文本、边框、背景）都微微偏向暖色调。不使用纯灰（#808080）或冷灰（#blue-gray），始终保持一丝温暖感。

## 3. Typography

**Body Font:** Avenir (主) → Helvetica → Arial → system-ui → sans-serif (回退栈)

**Character:** Avenir 是一款人文主义无衬线字体，线条均匀、字形开阔，兼具专业感和亲和力。不使用衬线字体或显示字体，保持工具的克制感。中文回退到系统默认黑体。

### Hierarchy
- **Display** (700, 24px, 行高 1.3): 页面标题、登录欢迎语。仅用于一级标题。
- **Title** (600, 18px, 行高 1.4): 卡片标题、区块标题、表单分组标题。
- **Body** (400, 14px, 行高 1.6): 正文、表单标签、数据展示。最大行宽 65-75ch。
- **Label** (500, 12px, 行高 1.5, 字距 0.02em): 小标签、状态文字、辅助说明。

### Named Rules

**The 克制字号规则。** 不使用超过 28px 的字号。工具界面不需要杂志式的大标题，过大的字号会挤压信息空间。

## 4. Elevation

系统采用扁平为主、微妙阴影为辅的层次策略。不使用重阴影或浮起效果，保持界面的安静感。层次通过底色差异和极轻阴影区分，而非通过浮起来强调。

### Shadow Vocabulary
- **卡片阴影** (`0 1px 3px rgba(0, 0, 0, 0.06)`): 卡片、弹窗、下拉菜单的默认阴影，极轻量，仅提供与背景的分离感。
- **悬停阴影** (`0 4px 12px rgba(0, 0, 0, 0.08)`): 可交互卡片的悬停态，比默认阴影稍重，暗示可点击。
- **弹窗阴影** (`0 8px 24px rgba(0, 0, 0, 0.12)`): 模态弹窗、浮层，提供足够的视觉分离。

### Named Rules

**The 安静规则。** 阴影永远是背景角色，不是装饰。如果一个阴影让人第一眼就注意到"这个东西浮起来了"，那它太重了。

## 5. Components

所有组件遵循圆润亲和的形态语言，使用柔和的圆角和温暖的色彩。

### Buttons
- **Shape:** 圆润，10px 圆角 (border-radius: 10px)
- **Primary:** 青绿底 (#0d9488) + 白色文字，padding 10px 24px。用于页面主操作（登录、检测、保存）。
- **Hover:** 深青绿底 (#0f766e)，transition 0.2s ease。
- **Focus:** 2px 青绿轮廓偏移 (outline: 2px solid #0d9488; outline-offset: 2px)
- **Ghost/Secondary:** 透明底 + 深灰文字，hover 时显示青绿薄纱底色。用于次要操作。
- **Disabled:** 50% 透明度，cursor: not-allowed。

### Cards / Containers
- **Corner Style:** 大圆角 (16px)
- **Background:** 纯白 (#ffffff)
- **Shadow:** 卡片阴影 (0 1px 3px rgba(0,0,0,0.06))
- **Border:** 无边框，通过阴影与背景分离
- **Internal Padding:** 24px

### Inputs / Fields
- **Style:** 白色背景 + 银线边框 (#e5e7eb)，10px 圆角
- **Focus:** 青绿边框 + 极淡青绿外发光 (box-shadow: 0 0 0 3px rgba(13,148,136,0.1))
- **Error:** 红色边框 + 红色提示文字
- **Disabled:** 浅灰背景 + 灰色文字
- **Padding:** 10px 14px

### Navigation (Sidebar)
- **竖屏模式:** 左侧固定，白色背景，宽度 220px
- **横屏模式:** 底部固定，白色背景
- **默认态:** 灰色图标 + 灰色文字
- **Hover:** 青绿薄纱底色 (#ccfbf1)
- **Active:** 青绿图标 + 青绿文字 + 左侧 3px 青绿指示条

### Chips / Tags
- **Style:** 青绿薄纱底色 (#ccfbf1) + 青绿文字 (#0d9488)，全圆角 (9999px)
- **用于:** 病虫害类别标签、检测状态标签

## 6. Do's and Don'ts

### Do:
- **Do** 使用青绿 (#0d9488) 作为唯一的主色调，保持全平台一致性。
- **Do** 使用圆角 10-16px 的组件形态，营造亲和感。
- **Do** 保持充足的留白，让信息呼吸。卡片间距至少 16px。
- **Do** 使用 0.2s ease 的 transition 作为标准交互反馈速度。
- **Do** 在深色文本 (#1f2937) 上确保对比度达到 WCAG AA 标准。
- **Do** 使用晨雾 (#f0fdfa) 作为页面背景，而非纯白。

### Don't:
- **Don't** 使用黑底霓虹、过度动效、炫技但不实用的极客暗黑风格。
- **Don't** 使用卡通化、配色幼稚、过度简化的儿童科普风格。
- **Don't** 使用过时的表格堆砌、密集信息、毫无设计感的传统农业系统风格。
- **Don't** 使用过度装饰、渐变泛滥、卡片套卡片的 SaaS 模板风格。
- **Don't** 在组件上使用超过 3px 的边框作为彩色装饰条（side-stripe borders）。
- **Don't** 使用渐变文字 (background-clip: text)。
- **Don't** 使用毛玻璃效果 (glassmorphism) 作为默认装饰。
- **Don't** 让主色占据页面超过 15% 的面积。
- **Don't** 使用超过 28px 的字号。
- **Don't** 使用重阴影让元素"浮起来"。
