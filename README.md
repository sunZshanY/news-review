<div align="center">
 <img src="icon.png" width="18%" alt="今日新闻">
 <h1>今日新闻</h1>

 <p>在桌面展示今日国内、国际与体育新闻的 Class Widgets 2 新闻阅览插件</p>

> 2026.10.3 已修复新闻显示旧闻的问题（v1.6.3+1）：更换实时数据源并增加时效过滤
 <p>
  <a href="https://github.com/sunZshanY/news-review/releases/latest"><img src="https://img.shields.io/github/v/release/sunZshanY/news-review?style=for-the-badge&color=blue" alt="最新版本"></a>
  <a href="https://github.com/sunZshanY/news-review"><img src="https://img.shields.io/github/stars/sunZshanY/news-review?style=for-the-badge&color=orange" alt="星标"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-purple.svg?style=for-the-badge" alt="License"></a>
 </p>
</div>

## 介绍 / Introduction

「今日新闻」是一款基于 **Python + QML** 的 Class Widgets 2 插件，可在桌面小组件上阅览当日**国内**、**国际**与**体育**新闻。

- 使用deepseek-v4-pro进行开发
- 内置多个数据源：新浪新闻（默认）、腾讯新闻热点榜、今日头条热榜、澎湃新闻
- 支持自定义 JSON API 数据源
- 自动定时刷新、滚动播报、更新桌面通知
- 支持自定义组件尺寸、列表条数、热度标记
- **旧闻自动过滤**：只显示最近 N 小时（默认 48 小时）内的新闻，并按时间倒序排列
- **多源自动降级**：首选数据源失效或新闻量不足时，自动合并备用源（新浪 → 腾讯 → 头条 → 澎湃）

## v1.6.3+1 (2026.10.3) 版本说明

**大面积修复：新闻一直是旧闻（2024 年）的问题**

- 根因：新浪 lid=2510（国内）/ 2511（国际）滚动接口已停更一年多，返回 2024~2025 年旧闻，且旧版没有时间过滤，直接展示
- 换用实测实时的新浪频道：2509 综合 / 2512 体育 / 2515 科技 / 2516 财经，弃用停更的 2510/2511
- 新增**时效过滤**：解析每条新闻的真实发布时间，超过设置时限（默认 48 小时）的自动丢弃，此后即使上游再次停更也不会再显示旧闻
- 新闻按发布时间**倒序排列**（最新在前），并按标题去重
- 新增**腾讯新闻热点榜**数据源；头条/澎湃热榜补充解析热度值
- **多源自动降级**：主源失败或不足 12 条时自动合并备用源
- 小组件每条新闻显示**发布时间**与来源媒体，底栏显示数据源与更新时间；高热度新闻显示“热”标记（可在组件设置中开关）
- 设置页新增**新闻时效**选项（6~168 小时）；修复自定义 API 设置卡片显示条件错误
- 修复热度标记开关无效的问题（开关此前未接入界面）

## v1.6.3 版本说明

**修复**

- 修复新闻内容不显示的问题：组件高度被基础组件固定高度覆盖，导致新闻列表高度为 0
- 修复自动滚动到底部后内容卡住的问题：滚动动画改为「下滑 → 停留 → 回顶 → 停留」循环模式
- 修复自定义尺寸不生效的问题：组件宽度 / 高度 / 列表项高度改为存入组件实例设置，保存后**立即生效**

**新特性（v1.6.1）**

- 数据源可选：新浪新闻 / 今日头条热榜 / 澎湃新闻 / 自定义 API
- 组件宽度（200-500）、高度（150-500）、列表项高度（28-60）可自定义

## 安装 / Install

1. 下载最新发布包：[Releases](https://github.com/sunZshanY/news-review/releases/latest)（`.cwplugin` 或 `.zip`）
2. 打开 Class Widgets 2 设置 → 插件 → 导入插件，选择下载的文件
3. 在桌面小组件编辑界面添加「今日新闻」组件即可

## 开发 / Develop

本插件基于 [Class Widgets SDK](https://github.com/Class-Widgets/class-widgets-sdk) 开发。

### 下载 Class Widgets SDK

```bash
pip install class-widgets-sdk
```

- PyPI：[class-widgets-sdk](https://pypi.org/project/class-widgets-sdk/)（当前最新 `0.6.0`）
- GitHub：[Class-Widgets/class-widgets-sdk](https://github.com/Class-Widgets/class-widgets-sdk)
- 插件模板：[Class-Widgets/Plugin-Template-V2](https://github.com/Class-Widgets/plugin-template-v2)


## 更新日志 / Changelog

| 版本 | 说明 |
| :--- | :--- |
| **v1.6.3+1 (2026.10.3)** | 大面积修复旧闻问题：换实时接口、时效过滤、时间倒序、腾讯源、多源自动降级、显示发布时间 |
| **v1.6.3** | 自定义尺寸保存后立即生效；修复尺寸设置无效问题 |
| **v1.6.2** | 修复新闻内容不显示；滚动改为循环播报 |
| **v1.6.1** | 新增多数据源支持（新浪 / 今日头条 / 澎湃 / 自定义 API） |
| **v1.6.0** | 替换失效的 vvhan API；JSON 字符串传递新闻列表；加入头条热榜与澎湃备用源 |
| **v1.5.x** | 轮询机制获取数据；界面与滚动优化 |

## 相关链接 / Links

- [Class Widgets 2](https://github.com/RinLit-233-shiroko/Class-Widgets-2)
- [Class Widgets SDK](https://pypi.org/project/class-widgets-sdk/)
- [插件广场](https://plaza.cw.rinlit.cn)

## 版权 / License

本项目基于 [MIT 协议](LICENSE) 开源。

<p align="center"><b>新人开发，请多多关照呢喵❤️~</b></p>
