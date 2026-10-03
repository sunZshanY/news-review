"""
今日新闻
A Class Widgets 2 plugin. 新闻阅览插件，在桌面展示最新国内与国际新闻。

v1.6.3+1 (2026.10.3)：大面积修复“总是显示旧新闻”问题 —— 详见 news_sources.py 头部说明。
"""

import json
import os
import sys
import threading
from datetime import datetime

from enum import IntEnum
from ClassWidgets.SDK import CW2Plugin, ConfigBaseModel, PluginAPI
from PySide6.QtCore import QObject, Qt, QTimer, Signal, Slot

# 确保插件所在目录在 sys.path 中，保证 news_sources 可导入
_plugin_dir = os.path.dirname(os.path.abspath(__file__))
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)

import news_sources


class NotificationLevel(IntEnum):
    INFO = 0
    ANNOUNCEMENT = 1
    WARNING = 2
    SYSTEM = 3


WIDGET_ID = "com.newsreview.news.widget"

# 主源不足时补充到的最低条数
MIN_ITEMS = 12


class NewsConfig(ConfigBaseModel):
    """插件全局配置"""
    refresh_interval: int = 30
    notify_on_update: bool = True
    widget_width: int = 320
    widget_height: int = 280
    item_height: int = 38
    custom_api_url: str = ""
    use_custom_api: bool = False
    data_source: str = "sina"
    # 新增：只显示最近 N 小时内的新闻（防旧闻核心开关）
    max_age_hours: int = 48


class NewsBackend(QObject):
    """新闻数据后端，供 QML 小组件与设置页调用"""

    dataChanged = Signal(dict)
    statusChanged = Signal(str)

    def __init__(self, plugin: "Plugin"):
        super().__init__()
        self._plugin = plugin
        self._api = plugin.api
        self._config = plugin.config

        self._lock = threading.Lock()
        self._fetching = False
        self._status = "idle"
        self._data: dict = {
            "date": "",
            "updated": "",
            "source": "",
            "news": [],
        }
        self._last_titles: set[str] = set()

        self._provider = None
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.CoarseTimer)
        self._timer.timeout.connect(self.refresh)

    # ---------------- 定时器 ----------------
    def _restart_timer(self) -> None:
        minutes = max(int(self._config.refresh_interval), 10)
        self._timer.start(minutes * 60 * 1000)

    def start(self) -> None:
        """插件加载完成后启动：先立刻抓取，再开始定时器"""
        self._restart_timer()

        QTimer.singleShot(500, self.refresh)

    # ---------------- 数据抓取 ----------------
    @Slot()
    def refresh(self) -> None:
        """立即刷新新闻（异步执行，不阻塞界面）"""
        with self._lock:
            if self._fetching:
                return
            self._fetching = True

        self._status = "loading"
        self.statusChanged.emit("loading")
        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _fetch_worker(self) -> None:
        try:
            self._fetch_news()
        except Exception as e:
            self._status = "error"
            self.statusChanged.emit("error")
        finally:
            with self._lock:
                self._fetching = False

    # ---------------- 抓取主流程：主源 + 多源自动降级 ----------------
    def _build_attempts(self):
        """返回 [(显示名, 抓取函数)]：首选数据源在前，其余按降级顺序补充。"""
        data_source = str(self._config.data_source or "sina").strip()

        attempts = []
        if data_source == "custom" and self._config.custom_api_url.strip():
            url = self._config.custom_api_url.strip()
            attempts.append(("自定义源", lambda: news_sources.fetch_custom(url)))
        elif data_source in news_sources.SOURCES:
            name, fn = news_sources.SOURCES[data_source]
            attempts.append((name, fn))
        # data_source 无效或为默认 sina 时兜底
        if not attempts:
            attempts.append(news_sources.SOURCES["sina"])

        for key in news_sources.FALLBACK_ORDER:
            name, fn = news_sources.SOURCES[key]
            if not any(a[0] == name for a in attempts):
                attempts.append((name, fn))
        return attempts

    def _fetch_news(self) -> None:
        """获取新闻数据：主源抓取 → 时效过滤 → 不足时补充备用源 → 去重排序"""
        max_age = max(int(self._config.max_age_hours), 1)

        collected: list = []
        used_sources: list = []

        for name, fetch_fn in self._build_attempts():
            try:
                items = fetch_fn() or []
            except Exception:
                items = []

            items = news_sources.filter_and_sort(items, max_age)
            if items:
                collected.extend(items)
                used_sources.append(name)

            # 主源已拿到足够数量的新鲜新闻即可停止
            if len(collected) >= MIN_ITEMS * 2:
                break

        news = news_sources.dedupe(news_sources.filter_and_sort(collected, max_age))

        if news:
            self._apply_data(news, " + ".join(used_sources))
        else:
            self._status = "error"
            self.statusChanged.emit("error")

    def _apply_data(self, news: list, source: str) -> None:
        now = datetime.now()

        titles = {n["title"] for n in news}
        is_first = not self._data["updated"]
        has_new = not is_first and not titles.issubset(self._last_titles)

        self._data = {
            "date": now.strftime("%Y-%m-%d"),
            "updated": now.strftime("%H:%M:%S"),
            "source": source,
            "news": news,
        }
        self._last_titles = titles

        self._status = "ready"
        self.statusChanged.emit("ready")
        self.dataChanged.emit(self._data)
        if has_new:
            self._notify_update(len(titles))

    # ---------------- 通知 ----------------
    def _notify_update(self, count: int) -> None:
        if not self._config.notify_on_update:
            return
        if self._provider is None:
            return
        try:
            self._provider.push(
                NotificationLevel.INFO,
                "今日新闻",
                f"已为您更新 {count} 条新闻，点击查看详情",
                5000,
                True,
            )
        except Exception:
            pass

    def attach_provider(self) -> None:
        """在插件上下文中注册通知提供者"""
        self._provider = self._api.notification.register_provider(
            "com.newsreview.news",
            name="今日新闻",
            use_system_notify=False,
        )

    # ---------------- 供 QML 调用的槽 ----------------
    @Slot(result="QVariantMap")
    def getData(self) -> dict:
        return self._data

    @Slot(result=str)
    def getDate(self) -> str:
        return self._data.get("date", "")

    @Slot(result=str)
    def getUpdated(self) -> str:
        return self._data.get("updated", "")

    @Slot(result=str)
    def getSource(self) -> str:
        return self._data.get("source", "")

    @Slot(result=list)
    def getNewsList(self) -> list:
        return self._data.get("news", [])

    @Slot(result=str)
    def getNewsJson(self) -> str:
        return json.dumps(self._data.get("news", []), ensure_ascii=False)

    @Slot(result=str)
    def getStatus(self) -> str:
        return self._status

    @Slot()
    def refreshNow(self) -> None:
        self.refresh()

    @Slot(int)
    def setRefreshInterval(self, minutes: int) -> None:
        self._config.refresh_interval = max(int(minutes), 10)
        self._restart_timer()

    @Slot(result=int)
    def getRefreshInterval(self) -> int:
        return int(self._config.refresh_interval)

    @Slot(int)
    def setMaxAgeHours(self, hours: int) -> None:
        """设置新闻时效：只显示最近 N 小时内的新闻"""
        self._config.max_age_hours = max(int(hours), 1)

    @Slot(result=int)
    def getMaxAgeHours(self) -> int:
        return int(self._config.max_age_hours)

    @Slot(bool)
    def setNotifyOnUpdate(self, enabled: bool) -> None:
        self._config.notify_on_update = bool(enabled)

    @Slot(result=bool)
    def getNotifyOnUpdate(self) -> bool:
        return bool(self._config.notify_on_update)

    @Slot(int)
    def setWidgetWidth(self, width: int) -> None:
        self._config.widget_width = max(int(width), 200)

    @Slot(result=int)
    def getWidgetWidth(self) -> int:
        return int(self._config.widget_width)

    @Slot(int)
    def setWidgetHeight(self, height: int) -> None:
        self._config.widget_height = max(int(height), 150)

    @Slot(result=int)
    def getWidgetHeight(self) -> int:
        return int(self._config.widget_height)

    @Slot(int)
    def setItemHeight(self, height: int) -> None:
        self._config.item_height = max(int(height), 24)

    @Slot(result=int)
    def getItemHeight(self) -> int:
        return int(self._config.item_height)

    @Slot(str)
    def setCustomApiUrl(self, url: str) -> None:
        self._config.custom_api_url = str(url).strip()

    @Slot(result=str)
    def getCustomApiUrl(self) -> str:
        return str(self._config.custom_api_url)

    @Slot(bool)
    def setUseCustomApi(self, enabled: bool) -> None:
        self._config.use_custom_api = bool(enabled)

    @Slot(result=bool)
    def getUseCustomApi(self) -> bool:
        return bool(self._config.use_custom_api)

    @Slot(str)
    def setDataSource(self, source: str) -> None:
        self._config.data_source = str(source).strip()

    @Slot(result=str)
    def getDataSource(self) -> str:
        return str(self._config.data_source)


class Plugin(CW2Plugin):
    def __init__(self, api: PluginAPI):
        super().__init__(api)
        self.config = NewsConfig()
        self.backend = None

    @Slot(result=QObject)
    def getBackend(self) -> NewsBackend:
        """供插件设置页获取新闻后端（PluginBackendBridge 注册的是插件本体）"""
        return self.backend

    def on_load(self):
        super().on_load()
        if self.pid is None:
            return

        self.api.config.register_plugin_model(self.pid, self.config)

        self.backend = NewsBackend(self)
        self.backend.attach_provider()

        self.api.widgets.register(
            widget_id=WIDGET_ID,
            name="今日新闻",
            qml_path="qml/news_widget.qml",
            backend_obj=self.backend,
            settings_qml="qml/widget_settings.qml",
            default_settings={
                "max_items": 8,
                "show_score": True,
                "widget_width": 320,
                "widget_height": 280,
                "item_height": 38,
            },
        )

        self.api.ui.register_settings_page(
            qml_path="qml/settings.qml",
            title="今日新闻",
            icon="ic_fluent_news_20_regular",
        )

        self.backend.start()


    def on_unload(self):
        if self.backend is not None:
            self.backend._timer.stop()
