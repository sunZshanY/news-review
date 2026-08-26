<div align="center">
 <img src="icon.png" width="18%" alt="今日新闻">
 <h1>今日新闻</h1>

 <p>在桌面展示今日国内与国际新闻的 Class Widgets 2 新闻阅览插件</p>

</div>

## 介绍 / Introduction

「今日新闻」是一款基于 **Python + QML** 的 Class Widgets 2 插件，可在桌面小组件上阅览当日**国内**与**国际**新闻，数据来自新浪新闻接口（无需密钥），接口不可用时自动切换至「每日简报」备用源。

### 特性 / Features

- 📰 今日新闻：国内 / 国际双栏目切换展示，按热度排序
- 🔥 热度标记：高分新闻显示「热」标记
- ⭐ 推荐标记：较高分新闻显示「荐」标记
- ⏰ 定时刷新：可配置自动刷新间隔（10 - 180 分钟）
- 🔔 更新通知：抓取到新头条时发送桌面通知
- 🖱️ 点击标题即可在浏览器中打开原文
- 🎨 跟随 Class Widgets 主题的 Fluent 风格界面，支持深色模式
- 🤏 迷你模式下滚动显示今日头条

## 使用 / Usage

1. 安装 [Class Widgets 2 SDK](https://github.com/Class-Widgets/class-widgets-sdk) 依赖：
```bash
pip install class-widgets-sdk
```

2. 在终端运行 `cw-plugin-pack` 以打包插件：
```bash
cw-plugin-pack
```

3. 在 Class Widgets 2 -> "设置" -> "插件"中导入打包好的插件，然后在桌面上添加「今日新闻」小组件。

## 开发 / Development

```
news-review/
├── cwplugin.json        # 插件清单
├── main.py              # 插件入口（新闻抓取后端）
├── icon.png             # 插件图标
└── qml/
    ├── news_widget.qml  # 新闻小组件界面
    ├── widget_settings.qml  # 小组件设置（显示条数、热度标记）
    └── settings.qml     # 插件设置页（刷新间隔、通知、立即刷新）
```

新闻数据流程：`main.py` 中的 `NewsBackend` 通过后台线程抓取新闻接口，经 Qt 信号推送到 QML 界面渲染。

## 注意声明 / Note the statement
 1. 本插件开发使用ClassWidgets SDK 0.6.0

 2. 此插件使用deepseek-v4-pro和mimo-v2.5-pro开发

## 版权 / License

本项目基于 MIT 协议开源，详情请参阅 [LICENSE](LICENSE) 文件。

---

新人开发，请多多关照喵！~
