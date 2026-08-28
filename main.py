"""
今日新闻
A Class Widgets 2 plugin. 新闻阅览插件，在桌面展示今日国内与国际新闻。
"""

import json
import threading
from datetime import datetime
from urllib.error import URLError
from urllib.request import Request, urlopen

from enum import IntEnum
from ClassWidgets.SDK import CW2Plugin, ConfigBaseModel, PluginAPI


class NotificationLevel(IntEnum):
    INFO = 0
    ANNOUNCEMENT = 1
    WARNING = 2
    SYSTEM = 3

from PySide6.QtCore import QObject, Qt, QTimer, Signal, Slot

# 新浪新闻接口（feed.mix.sina.com.cn）
API_DOMESTIC = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2510&k=&num=20&page=1"
API_INTL = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2511&k=&num=20&page=1"
API_SPORT = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2512&k=&num=20&page=1"

# 备用接口（每日简报）
API_BACKUP = "https://api.vvhan.com/api/60s"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) NewsReviewPlugin/1.0"
)

WIDGET_ID = "com.newsreview.news.widget"


class NewsConfig(ConfigBaseModel):
    """插件全局配置"""

    refresh_interval: int = 30  # 自动刷新间隔（分钟），最小值 10
    notify_on_update: bool = True  # 抓取到新头条时发送桌面通知
    widget_width: int = 300  # 组件宽度
    widget_height: int = 480  # 组件高度
    item_height: int = 36  # 列表项高度


def _fetch_json(url: str, timeout: int = 10) -> dict:
    """通过 urllib 请求 JSON 接口"""
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


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
        QTimer.singleShot(800, self.refresh)

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
            self._fetch_primary()
        except Exception as exc:
            self._status = "error"
            self.statusChanged.emit("error")
        finally:
            with self._lock:
                self._fetching = False

    def _fetch_primary(self) -> None:
        news = []
        errors = []

        # 获取国内新闻
        try:
            payload = _fetch_json(API_DOMESTIC).get("result") or {}
            raw = payload.get("data") or []
            for item in raw:
                news_item = {
                    "title": str(item.get("title", "")).strip(),
                    "url": str(item.get("url", "")).strip(),
                    "media_name": str(item.get("media_name", "")).strip(),
                }
                if news_item["title"]:
                    news.append(news_item)
        except Exception as e:
            errors.append(f"国内新闻: {e}")

        # 获取国际新闻
        try:
            payload = _fetch_json(API_INTL).get("result") or {}
            raw = payload.get("data") or []
            for item in raw:
                news_item = {
                    "title": str(item.get("title", "")).strip(),
                    "url": str(item.get("url", "")).strip(),
                    "media_name": str(item.get("media_name", "")).strip(),
                }
                if news_item["title"]:
                    news.append(news_item)
        except Exception as e:
            errors.append(f"国际新闻: {e}")

        # 获取体育新闻
        try:
            payload = _fetch_json(API_SPORT).get("result") or {}
            raw = payload.get("data") or []
            for item in raw:
                news_item = {
                    "title": str(item.get("title", "")).strip(),
                    "url": str(item.get("url", "")).strip(),
                    "media_name": str(item.get("media_name", "")).strip(),
                }
                if news_item["title"]:
                    news.append(news_item)
        except Exception as e:
            errors.append(f"体育新闻: {e}")

        # 如果新浪接口全部失败，尝试备用接口
        if not news:
            try:
                backup_data = _fetch_json(API_BACKUP)
                if isinstance(backup_data, list):
                    for i, item in enumerate(backup_data):
                        if isinstance(item, str) and item.strip():
                            news.append({
                                "title": item.strip(),
                                "url": "",
                                "media_name": "每日简报",
                            })
                elif isinstance(backup_data, dict):
                    data_list = backup_data.get("data") or backup_data.get("news") or []
                    for item in data_list:
                        if isinstance(item, str) and item.strip():
                            news.append({
                                "title": item.strip(),
                                "url": "",
                                "media_name": "每日简报",
                            })
            except Exception as e:
                errors.append(f"备用接口: {e}")

        if news:
            self._apply_data(news, "新浪新闻" if not errors else "新浪新闻（部分）")
        else:
            self._status = "error"
            self.statusChanged.emit("error")
            print(f"[今日新闻] 获取失败: {'; '.join(errors)}")



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
        self._config.widget_height = max(int(height), 200)

    @Slot(result=int)
    def getWidgetHeight(self) -> int:
        return int(self._config.widget_height)

    @Slot(int)
    def setItemHeight(self, height: int) -> None:
        self._config.item_height = max(int(height), 24)

    @Slot(result=int)
    def getItemHeight(self) -> int:
        return int(self._config.item_height)


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
            },
        )

        self.api.ui.register_settings_page(
            qml_path="qml/settings.qml",
            title="今日新闻",
            icon="ic_fluent_news_20_regular",
        )

        self.backend.start()
        print(f"[今日新闻] 插件已加载")

    def on_unload(self):
        if self.backend is not None:
            self.backend._timer.stop()
        print(f"[今日新闻] 插件已卸载")
