import requests
import time
import random
import os
import re
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置项
CONFIG = {
    "input_file": "merge.m3u",
    "output_file": "valid.m3u",
    "timeout": 6,
    "max_workers": 15,
    "random_delay": (0.1, 0.5),
    "proxy_prefix": "https://myproxy.kfwong15.workers.dev/?url=",  # 自定义代理
    "china_ip_pattern": r"(\.cn|\.china|\.gov\.cn|\.edu\.cn|\.cctv|\.cntv|\.aliyun|\.chinaunicom|\.china(\d+)\.)"
}

def is_china_ip(url):
    return re.search(CONFIG["china_ip_pattern"], url) is not None

def smart_check_url(info_block, url):
    try:
        time.sleep(random.uniform(*CONFIG["random_delay"]))
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        # 如果是 DASH 流
        if url.endswith(".mpd"):
            res = requests.get(url, headers=headers, timeout=CONFIG["timeout"])
            return (info_block, url, res.status_code == 200 and "MPD" in res.text)

        # 如果是 M3U8 流
        elif url.endswith(".m3u8"):
            res = requests.get(url, headers=headers, timeout=CONFIG["timeout"])
            return (info_block, url, res.status_code == 200 and "#EXTM3U" in res.text)

        # 其他链接使用 HEAD 检查
        else:
            res = requests.head(url, headers=headers, timeout=CONFIG["timeout"], allow_redirects=True)
            return (info_block, url, res.status_code == 200)

    except:
        return (info_block, url, False)

def parse_m3u_lines(lines):
    blocks = []
    current_block = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#EXTINF") or stripped.startswith("#KODIPROP") or \
           stripped.startswith("#EXTVLCOPT") or stripped.startswith("#"):
            current_block.append(stripped)
        elif stripped.startswith("http"):
            current_block.append(stripped)
            blocks.append(current_block)
            current_block = []

    return blocks

def filter_and_save(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"❌ 输入文件不存在：{input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    blocks = parse_m3u_lines(lines)
    futures = []
    valid_blocks = []

    with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as executor:
        for block in blocks:
            url = block[-1]
            original_url = url
            if is_china_ip(url):
                url = CONFIG["proxy_prefix"] + url
            futures.append(executor.submit(smart_check_url, block[:-1], url))

        for future in tqdm(as_completed(futures), total=len(futures), desc="正在检测频道有效性"):
            info_lines, final_url, is_valid = future.result()
            if is_valid:
                valid_blocks.append(info_lines + [final_url, ""])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for block in valid_blocks:
            for line in block:
                f.write(line + "\n")

    print(f"\n✅ 检测完成：{len(valid_blocks)} 个频道可用，结果保存至 {output_path}")
