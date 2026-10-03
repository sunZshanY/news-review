# -*- coding: utf-8 -*-
"""
test_sources.py — 今日新闻插件数据引擎测试

运行：python test_sources.py
- 第一部分：离线单元测试（mock 数据，不联网）
- 第二部分：在线新鲜度验证（联网实测各数据源，断言无旧闻）
退出码非 0 表示存在失败项。
"""

import json
import sys
import time
from datetime import datetime

import news_sources

FAILURES = []


def check(label, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {label}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


# --------------------------------------------------------------------------
# 一、离线单元测试
# --------------------------------------------------------------------------
def test_parse_timestamp():
    print("\n== 离线单元测试: parse_timestamp ==")
    ns = news_sources
    check("秒级时间戳", ns.parse_timestamp("1790999435") == 1790999435)
    check("毫秒时间戳", ns.parse_timestamp(1790895819017) == 1790895819)
    check("日期字符串", ns.parse_timestamp("2026-10-03 12:00:00") ==
          int(datetime(2026, 10, 3, 12, 0, 0).timestamp()))
    check("空值返回 0", ns.parse_timestamp(None) == 0 and ns.parse_timestamp("") == 0)
    check("垃圾值返回 0", ns.parse_timestamp("abc") == 0)


def test_format_time():
    print("\n== 离线单元测试: format_time ==")
    ns = news_sources
    now = datetime(2026, 10, 3, 13, 0, 0)
    ts = int(datetime(2026, 10, 3, 8, 5, 0).timestamp())
    check("同年格式 MM-DD HH:MM", ns.format_time(ts, now) == "10-03 08:05")
    ts2 = int(datetime(2025, 12, 31, 23, 59, 0).timestamp())
    check("跨年带年份", ns.format_time(ts2, now) == "2025-12-31 23:59")
    check("无时间戳返回空串", ns.format_time(0, now) == "")


def test_filter_and_sort():
    print("\n== 离线单元测试: filter_and_sort（防旧闻核心）==")
    ns = news_sources
    now = time.time()
    h = 3600.0
    items = [
        {"title": "最新", "timestamp": int(now - 1 * h)},      # 1 小时前
        {"title": "旧闻", "timestamp": int(now - 500 * h)},    # 20 天前 -> 应被过滤
        {"title": "更旧", "timestamp": int(now - 9000 * h)},   # 2025 年 -> 应被过滤
        {"title": "热榜无时间戳", "timestamp": 0},             # 无时间戳 -> 保留
    ]
    out = ns.filter_and_sort(items, 48)
    titles = [i["title"] for i in out]
    check("旧闻被过滤（不再出现 2024/2025 年新闻）", "旧闻" not in titles and "更旧" not in titles)
    check("新文保留", "最新" in titles)
    check("无时间戳条目保留", "热榜无时间戳" in titles)
    check("最新排最前", out[0]["title"] == "最新")
    # 时效上限：max_age=1 小时时，"最新"(1h 前) 边界外
    out2 = ns.filter_and_sort(items, 1)
    check("1 小时时效过滤生效", all(i["title"] != "最新" for i in out2))


def test_dedupe():
    print("\n== 离线单元测试: dedupe ==")
    ns = news_sources
    items = [
        {"title": "A", "timestamp": 100},
        {"title": "A", "timestamp": 50},
        {"title": "B", "timestamp": 90},
        {"title": "", "timestamp": 1},
    ]
    out = ns.dedupe(items)
    check("按标题去重", len(out) == 2)
    check("保留首条（最新）", out[0]["timestamp"] == 100)


def _mock_sina_payload():
    now = int(time.time())
    return {
        "result": {"data": [
            {"title": "实时新闻A", "url": "https://a", "media_name": "媒体A",
             "ctime": str(now - 1800), "mtime": str(now)},
            {"title": "实时新闻B", "url": "https://b", "media_name": "媒体B",
             "ctime": str(now - 3600)},
            {"title": "", "url": "", "media_name": "", "ctime": str(now)},  # 空标题丢弃
        ]}
    }


def test_parsers_offline():
    print("\n== 离线单元测试: 各数据源解析（mock）==")
    ns = news_sources
    _orig_fetch_json = ns._fetch_json
    try:
        # 新浪：4 个频道 × 2 条 mock = 8 条，来源标签应各不相同
        ns._fetch_json = lambda url, timeout=12: _mock_sina_payload()
        sina = ns.fetch_sina()
        check("新浪解析条数（4 频道）", len(sina) == 8, f"got {len(sina)}")
        check("新浪频道标签齐全", len({i["source"] for i in sina}) == len(ns.SINA_FEEDS),
              str({i["source"] for i in sina}))
        if sina:
            check("新浪条目含时间戳与展示时间",
                  sina[0]["timestamp"] > 0 and sina[0]["time"] and "·" in sina[0]["source"])

        # 腾讯（含头部说明条目，应被跳过）
        now = int(time.time())
        ns._fetch_json = lambda url, timeout=12: {"idlist": [{"newslist": [
            {"title": "腾讯新闻用户最关注的热点，每10分钟更新一次", "url": ""},
            {"title": "热点新闻X", "url": "https://view.inews.qq.com/a/x",
             "timestamp": now - 600, "source": "人民日报",
             "hotEvent": {"hotScore": 1043335}},
        ]}]}
        tt = ns.fetch_tencent()
        check("腾讯解析跳过头部条目", len(tt) == 1, f"got {len(tt)}")
        if tt:
            check("腾讯条目含时间与热度", tt[0]["time"] and tt[0]["hot"] == 1043335)

        # 头条
        ns._fetch_json = lambda url, timeout=12: {"data": [
            {"Title": "头条热点", "Url": "https://www.toutiao.com/trending/1", "HotValue": "24232285"},
        ]}
        tt2 = ns.fetch_toutiao()
        check("头条解析条数与热度", len(tt2) == 1 and tt2[0]["hot"] == 24232285)

        # 澎湃（无 linkUrl 时用 contId 拼接）
        ns._fetch_json = lambda url, timeout=12: {"data": {"hotNews": [
            {"name": "澎湃热点", "contId": "34190175", "pubTimeLong": str(now * 1000)},
        ]}}
        pp = ns.fetch_pengpai()
        check("澎湃解析条数", len(pp) == 1, f"got {len(pp)}")
        if pp:
            check("澎湃 URL 由 contId 拼接", "newsDetail_forward_34190175" in pp[0]["url"])

        # 自定义 API
        ns._fetch_json = lambda url, timeout=12: {"data": [
            {"title": "自定义新闻", "url": "https://c", "timestamp": now - 300},
        ]}
        cu = ns.fetch_custom("https://example.com/api")
        check("自定义 API 解析", len(cu) == 1 and cu[0]["time"])
    finally:
        ns._fetch_json = _orig_fetch_json  # 恢复真实网络请求


# --------------------------------------------------------------------------
# 二、在线新鲜度验证
# --------------------------------------------------------------------------
def test_live_freshness():
    print("\n== 在线新鲜度验证（联网实测）==")
    ns = news_sources
    now = time.time()
    max_age_h = 48
    MIN_FILTERED = 10  # 时效过滤后最少保留条数

    def verify(name, items, require_ts=True):
        if not items:
            check(f"{name}: 有数据", False, "empty")
            return
        check(f"{name}: 有数据（{len(items)} 条）", True)
        raw_ts = [i for i in items if i["timestamp"] > 0]
        if require_ts:
            check(f"{name}: 条目均有时间戳", len(raw_ts) == len(items),
                  f"{len(raw_ts)}/{len(items)}")
        else:
            # 热榜类接口本身不带时间戳，属于正常设计
            check(f"{name}: 条目数充足", len(items) >= 10, f"{len(items)} 条")

        # 插件管线验证：时效过滤后的结果才是真正展示的内容
        filtered = ns.filter_and_sort(items, max_age_h)
        f_ts = [i for i in filtered if i["timestamp"] > 0]
        if require_ts:
            check(f"{name}: 时效过滤后仍 ≥ {MIN_FILTERED} 条",
                  len(filtered) >= MIN_FILTERED, f"got {len(filtered)}")
        if f_ts:
            newest = max(i["timestamp"] for i in f_ts)
            oldest = min(i["timestamp"] for i in f_ts)
            age_h = (now - newest) / 3600
            oldest_age_h = (now - oldest) / 3600
            check(f"{name}: 过滤后最新一条距今 < 24 小时", age_h < 24,
                  f"最新 {age_h:.1f}h 前，{datetime.fromtimestamp(newest):%Y-%m-%d %H:%M}")
            check(f"{name}: 过滤后全部在 {max_age_h}h 时效内", oldest_age_h <= max_age_h,
                  f"最旧 {oldest_age_h:.1f}h 前")
        # 展示过滤后前 3 条
        for i in filtered[:3]:
            print(f"      [{i['time'] or '??':>16}] {i['title'][:40]}")

    try:
        sina = ns.fetch_sina()
    except Exception as e:
        sina = []
        print("  新浪抓取异常:", repr(e))
    verify("新浪新闻", sina)

    try:
        tencent = ns.fetch_tencent()
    except Exception as e:
        tencent = []
        print("  腾讯抓取异常:", repr(e))
    verify("腾讯热点", tencent, require_ts=False)

    try:
        toutiao = ns.fetch_toutiao()
    except Exception as e:
        toutiao = []
        print("  头条抓取异常:", repr(e))
    verify("头条热榜", toutiao, require_ts=False)

    try:
        pengpai = ns.fetch_pengpai()
    except Exception as e:
        pengpai = []
        print("  澎湃抓取异常:", repr(e))
    verify("澎湃热榜", pengpai)

    # 汇总管线验证：合并 + 时效过滤 + 去重 + 倒序
    combined = ns.dedupe(ns.filter_and_sort(
        sina + tencent + toutiao + pengpai, max_age_h))
    print(f"\n  合并管线: {len(combined)} 条（去重后）")
    check("合并后非空", bool(combined))
    if combined:
        check("合并后首条为最新", combined[0]["timestamp"] == max(
            i["timestamp"] for i in combined if i["timestamp"]))
        years = {datetime.fromtimestamp(i["timestamp"]).year for i in combined if i["timestamp"]}
        check("合并后无 2024/2025 旧闻",
              not (years & {2024, 2025}), f"年份: {sorted(years)}")


if __name__ == "__main__":
    print(f"测试开始: {datetime.now():%Y-%m-%d %H:%M:%S}")
    test_parse_timestamp()
    test_format_time()
    test_filter_and_sort()
    test_dedupe()
    test_parsers_offline()
    test_live_freshness()

    print("\n" + "=" * 56)
    if FAILURES:
        print(f"失败 {len(FAILURES)} 项: {FAILURES}")
        sys.exit(1)
    print("全部测试通过 ✔")
