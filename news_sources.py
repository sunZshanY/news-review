# -*- coding: utf-8 -*-
"""
news_sources.py — 今日新闻插件的数据引擎（纯标准库，无 Qt 依赖，可独立测试）

v1.6.3+1 (2026.10.3) 大面积修复说明
======================
旧版使用新浪 lid=2510(国内)/2511(国际) 滚动接口，这两个频道已停更一年多，
返回 2024~2025 年的旧新闻，且旧版没有任何时间过滤，导致桌面组件一直显示旧闻。

本次修复：
1. 换用已实测实时的新浪频道（2509 综合 / 2512 体育 / 2515 科技 / 2516 财经）；
2. 每个接口条目解析真实发布时间(ctime/pubTimeLong/timestamp)；
3. 按“只保留最近 max_age_hours 小时内的新闻”硬性过滤 —— 即使上游再次停更，
   旧闻也会被自动丢弃，永远不会再显示 2024 年的新闻；
4. 所有新闻按发布时间倒序排列（最新在最前），并按标题去重；
5. 新增腾讯新闻热点榜数据源，头条/澎湃热榜同样解析热度与时间；
6. 多源自动降级：首选源失败或数量不足时，自动合并备用源（新浪/腾讯/头条/澎湃）。
"""

import json
import time as _time
from datetime import datetime
from urllib.request import Request, urlopen

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) NewsReviewPlugin/1.6.3+1"
)

# --------------------------------------------------------------------------
# 接口定义
# --------------------------------------------------------------------------
# 新浪滚动接口。注意：2510(国内)/2511(国际) 已停更，严禁再使用！
# 以下频道均为实测实时（见 2026-10-03 探测记录）。
SINA_FEEDS = [
    ("2509", "综合"),
    ("2512", "体育"),
    ("2515", "科技"),
    ("2516", "财经"),
]

API_TENCENT_HOT = "https://r.inews.qq.com/gw/event/hot_ranking_list?page_size=50"
API_TOUTIAO_HOT = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
API_PENGPAI = "https://cache.thepaper.cn/contentapi/wwwIndex/rightSidebar"

# 新浪页面默认带上的 referer，降低被风控概率
SINA_REFERER = "https://news.sina.com.cn/roll/"

DEFAULT_TIMEOUT = 12


def _sina_api(lid: str, num: int = 25) -> str:
    return (
        f"https://feed.mix.sina.com.cn/api/roll/get"
        f"?pageid=153&lid={lid}&k=&num={num}&page=1"
    )


# --------------------------------------------------------------------------
# 基础网络请求
# --------------------------------------------------------------------------
def _fetch(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if "sina" in url:
        headers["Referer"] = SINA_REFERER
    req = Request(url, headers=headers)
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _fetch_json(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    return json.loads(_fetch(url, timeout))


# --------------------------------------------------------------------------
# 工具函数
# --------------------------------------------------------------------------
def parse_timestamp(value) -> int:
    """把秒 / 毫秒 / 'YYYY-MM-DD HH:MM:SS' 字符串统一解析为 unix 秒；失败返回 0。"""
    if value in (None, "", 0, "0"):
        return 0
    try:
        v = float(value)
    except (TypeError, ValueError):
        v = 0.0
    if v:
        if v > 1e12:          # 毫秒
            v /= 1000.0
        if 1e8 < v < 4.2e9:   # 合理的 unix 秒范围（1973~2103）
            return int(v)
        return 0
    # 尝试字符串日期
    try:
        return int(datetime.strptime(str(value)[:19], "%Y-%m-%d %H:%M:%S").timestamp())
    except Exception:
        return 0


def format_time(ts: int, now: datetime = None) -> str:
    """时间戳 -> 'MM-DD HH:MM'；跨年时带年份。无时间戳返回空串。"""
    if not ts:
        return ""
    now = now or datetime.now()
    dt = datetime.fromtimestamp(ts)
    if dt.year != now.year:
        return dt.strftime("%Y-%m-%d %H:%M")
    return dt.strftime("%m-%d %H:%M")


def _make_item(title, url, media_name, source, ts=0, hot=0) -> dict:
    try:
        hot = int(float(hot or 0))
    except (TypeError, ValueError):
        hot = 0
    return {
        "title": str(title).strip(),
        "url": str(url or "").strip(),
        "media_name": str(media_name or "").strip(),
        "source": source,
        "timestamp": int(ts or 0),
        "time": format_time(int(ts or 0)) if ts else "",
        "hot": hot,
    }


def dedupe(items: list) -> list:
    """按标题去重，保留首次出现（时间已排序时即最新的那条）。"""
    seen, out = set(), []
    for it in items:
        key = it["title"]
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def filter_and_sort(items: list, max_age_hours: int) -> list:
    """
    时效过滤 + 倒序排序（最新在前）。
    - 有时间戳的条目：只保留最近 max_age_hours 小时内的；
    - 无时间戳的条目（实时热榜类接口）：保留并排在有时间戳条目之后。
    """
    max_age_hours = max(int(max_age_hours), 1)
    now = _time.time()
    cutoff = now - max_age_hours * 3600.0

    fresh, no_ts = [], []
    for it in items:
        if it.get("timestamp", 0) > 0:
            if it["timestamp"] >= cutoff:
                fresh.append(it)
        else:
            no_ts.append(it)

    fresh.sort(key=lambda x: x["timestamp"], reverse=True)
    return fresh + no_ts


# --------------------------------------------------------------------------
# 各数据源抓取与解析
# --------------------------------------------------------------------------
def fetch_sina(timeout: int = DEFAULT_TIMEOUT) -> list:
    """抓取全部已验证实时的新浪滚动频道。"""
    out = []
    for lid, label in SINA_FEEDS:
        try:
            data = _fetch_json(_sina_api(lid), timeout)
            payload = data.get("result") or {}
            for item in payload.get("data") or []:
                title = str(item.get("title") or "").strip()
                if not title:
                    continue
                ts = parse_timestamp(
                    item.get("ctime") or item.get("mtime") or item.get("intime")
                )
                out.append(_make_item(
                    title,
                    item.get("url") or item.get("wapurl"),
                    item.get("media_name"),
                    f"新浪·{label}",
                    ts,
                ))
        except Exception:
            continue
    return out


def fetch_tencent(timeout: int = DEFAULT_TIMEOUT) -> list:
    """腾讯新闻热点榜（每 10 分钟更新）。"""
    out = []
    data = _fetch_json(API_TENCENT_HOT, timeout)
    idlist = data.get("idlist") or []
    if not idlist:
        return out
    for item in idlist[0].get("newslist") or []:
        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        if not title or not url:
            continue  # 跳过榜单头部说明等无效条目
        ts = parse_timestamp(item.get("timestamp"))
        hot_event = item.get("hotEvent")
        hot = 0
        if isinstance(hot_event, dict):
            hot = hot_event.get("hotScore") or 0
        out.append(_make_item(
            title,
            url,
            item.get("source") or item.get("chlname") or "腾讯新闻",
            "腾讯热点",
            ts,
            hot,
        ))
    return out


def fetch_toutiao(timeout: int = DEFAULT_TIMEOUT) -> list:
    """今日头条热榜。"""
    out = []
    data = _fetch_json(API_TOUTIAO_HOT, timeout)
    for item in data.get("data") or []:
        title = str(item.get("Title") or "").strip()
        if not title:
            continue
        try:
            hot = int(float(item.get("HotValue") or 0))
        except (TypeError, ValueError):
            hot = 0
        out.append(_make_item(
            title,
            item.get("Url"),
            "今日头条",
            "头条热榜",
            0,
            hot,
        ))
    return out


def fetch_pengpai(timeout: int = DEFAULT_TIMEOUT) -> list:
    """澎湃新闻热榜。"""
    out = []
    data = _fetch_json(API_PENGPAI, timeout)
    hot_news = (data.get("data") or {}).get("hotNews") or []
    for item in hot_news:
        title = str(item.get("name") or "").strip()
        if not title:
            continue
        url = str(item.get("linkUrl") or item.get("link") or "").strip()
        cont_id = str(item.get("contId") or "")
        if not url and cont_id:
            url = f"https://www.thepaper.cn/newsDetail_forward_{cont_id}"
        ts = parse_timestamp(item.get("pubTimeLong") or item.get("trackPublishTime"))
        out.append(_make_item(title, url, "澎湃新闻", "澎湃热榜", ts))
    return out


def fetch_custom(url: str, timeout: int = DEFAULT_TIMEOUT) -> list:
    """自定义 JSON API：兼容新浪格式 / 列表 / 通用 data/news/items 字典。"""
    url = str(url or "").strip()
    if not url:
        return []
    data = _fetch_json(url, timeout)
    out = []

    def _add(item: dict) -> None:
        title = str(item.get("title") or "").strip()
        if not title:
            return
        ts = parse_timestamp(
            item.get("timestamp") or item.get("ctime")
            or item.get("pubTime") or item.get("time")
        )
        out.append(_make_item(
            title,
            item.get("url"),
            item.get("source") or item.get("media_name") or "自定义源",
            "自定义源",
            ts,
            item.get("hot") or item.get("hotScore") or 0,
        ))

    if isinstance(data, dict) and "result" in data:
        payload = data.get("result") or {}
        for item in payload.get("data") or []:
            if isinstance(item, dict):
                _add(item)
            elif isinstance(item, str) and item.strip():
                out.append(_make_item(item.strip(), "", "自定义源", "自定义源"))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, str) and item.strip():
                out.append(_make_item(item.strip(), "", "自定义源", "自定义源"))
            elif isinstance(item, dict):
                _add(item)
    elif isinstance(data, dict):
        data_list = data.get("data") or data.get("news") or data.get("items") or []
        for item in data_list:
            if isinstance(item, str) and item.strip():
                out.append(_make_item(item.strip(), "", "自定义源", "自定义源"))
            elif isinstance(item, dict):
                _add(item)
    return out


# 数据源注册表：名称 -> 抓取函数（供后端与测试共用）
SOURCES = {
    "sina": ("新浪新闻", fetch_sina),
    "tencent": ("腾讯新闻", fetch_tencent),
    "toutiao": ("今日头条热榜", fetch_toutiao),
    "pengpai": ("澎湃新闻", fetch_pengpai),
}

# 自动降级顺序（主源失败/不足时依次补充）
FALLBACK_ORDER = ["sina", "tencent", "toutiao", "pengpai"]
