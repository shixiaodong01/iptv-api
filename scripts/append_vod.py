"""把静态点播片单（config/vod_movies.txt）合并进最终的直播源结果。

这些条目是完整的 VOD m3u8（整部电影一个播放列表），不是直播流，
会被 iptv-api 的直播测速环节判定为无效而丢弃。因此这里跳过测速，
在生成结果之后直接追加，保证"片名即频道名"的体验。
"""

from pathlib import Path

OUTPUT_DIR = Path("output")
FINAL_TXT = OUTPUT_DIR / "result.txt"
FINAL_M3U = OUTPUT_DIR / "result.m3u"
VOD_SOURCE = Path("config/vod_movies.txt")

# 用第一条片名做幂等标记，避免重复追加
PROBE_NAME = "杨柳春风"


def load_entries():
    """读取片单，返回 [(片名, 地址), ...]，忽略分类行与空行。"""
    if not VOD_SOURCE.exists():
        return []
    entries = []
    for raw in VOD_SOURCE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.endswith("#genre#") or "," not in line:
            continue
        name, url = line.split(",", 1)
        name, url = name.strip(), url.strip()
        if name and url.startswith("http"):
            entries.append((name, url))
    return entries


def group_title():
    for raw in VOD_SOURCE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.endswith("#genre#"):
            return line.replace(",#genre#", "") or "点播电影"
    return "点播电影"


def append_txt(entries, group):
    if not FINAL_TXT.exists():
        print(f"[vod] 未找到 {FINAL_TXT}，跳过 TXT 追加")
        return
    text = FINAL_TXT.read_text(encoding="utf-8")
    if PROBE_NAME in text:
        print("[vod] TXT 已包含片单，跳过")
        return
    with FINAL_TXT.open("a", encoding="utf-8") as f:
        f.write(f"\n{group},#genre#\n")
        for name, url in entries:
            f.write(f"{name},{url}\n")
    print(f"[vod] TXT 追加 {len(entries)} 条")


def append_m3u(entries, group):
    if not FINAL_M3U.exists():
        print(f"[vod] 未找到 {FINAL_M3U}，跳过 M3U 追加")
        return
    text = FINAL_M3U.read_text(encoding="utf-8")
    if PROBE_NAME in text:
        print("[vod] M3U 已包含片单，跳过")
        return
    with FINAL_M3U.open("a", encoding="utf-8") as f:
        for name, url in entries:
            f.write(f'#EXTINF:-1 tvg-name="{name}" group-title="{group}",{name}\n')
            f.write(f"{url}\n")
    print(f"[vod] M3U 追加 {len(entries)} 条")


def main():
    entries = load_entries()
    if not entries:
        print("[vod] 片单为空，跳过")
        return
    group = group_title()
    append_txt(entries, group)
    append_m3u(entries, group)


if __name__ == "__main__":
    main()
