import requests
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# === GitHub Raw 目录 ===
REPO_USER = "kfwong15"
REPO_NAME = "colection"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO_USER}/{REPO_NAME}/main/source/m3u"
API_URL = f"https://api.github.com/repos/{REPO_USER}/{REPO_NAME}/contents/source/m3u"

MERGE_FILE = "merge.m3u"
VALID_FILE = "valid.m3u"
MAX_WORKERS = 15
TIMEOUT = 5
DELAY_RANGE = (0.1, 0.5)

def get_m3u_urls():
    try:
        res = requests.get(API_URL, timeout=10)
        res.raise_for_status()
        files = res.json()
        return [f"{RAW_BASE}/{f['name']}" for f in files if f["name"].endswith(".m3u")]
    except Exception as e:
        print(f"❌ 获取 m3u 列表失败: {e}")
        return []

def download_and_parse(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        content = r.text.splitlines()
        channels = {}
        current = None
        for line in content:
            if line.startswith("#EXTINF"):
                current = line.strip()
            elif current and line.startswith("http"):
                if line not in channels.values():
                    channels[current] = line.strip()
                current = None
        return channels
    except Exception as e:
        print(f"❌ 下载失败 {url}: {e}")
        return {}

def merge_all_channels():
    urls = get_m3u_urls()
    all_channels = {}
    for url in urls:
        print(f"📥 正在读取：{url}")
        ch = download_and_parse(url)
        all_channels.update(ch)

    with open(MERGE_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for info, url in all_channels.items():
            f.write(f"{info}\n{url}\n")
    print(f"✅ 合并完成：{MERGE_FILE}，共 {len(all_channels)} 条频道")

    return list(all_channels.items())

def check_valid(info, url):
    try:
        time.sleep(random.uniform(*DELAY_RANGE))
        r = requests.head(url, timeout=TIMEOUT)
        return (info, url, r.status_code == 200)
    except:
        return (info, url, False)

def filter_valid_channels(channels):
    valid = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(check_valid, info, url) for info, url in channels]
        for f in tqdm(as_completed(futures), total=len(futures), desc="🔍 检查频道可用性"):
            info, url, ok = f.result()
            if ok:
                valid.append((info, url))

    with open(VALID_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for info, url in valid:
            f.write(f"{info}\n{url}\n")
    print(f"✅ 有效频道保存到：{VALID_FILE}，共 {len(valid)} 条")

if __name__ == "__main__":
    all_channels = merge_all_channels()
    filter_valid_channels(all_channels)
