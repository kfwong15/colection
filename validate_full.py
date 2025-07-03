import requests, time, random, os, re
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

CONFIG = {
    "input_file": "merge.m3u",
    "output_file": "valid.m3u",
    "timeout": 6,
    "max_workers": 15,
    "random_delay": (0.1, 0.5),
    "proxy_prefix": "https://myproxy.kfwong15.workers.dev/?url=",
    "china_ip_pattern": r"(\.cn|\.china|\.gov\.cn|\.edu\.cn|\.cctv|\.cntv|\.aliyun|\.chinaunicom|\.china(\d+)\.)"
}

def is_china_ip(url):
    return re.search(CONFIG["china_ip_pattern"], url) is not None

def smart_check_url(info_block, url):
    time.sleep(random.uniform(*CONFIG["random_delay"]))
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        if url.endswith(".mpd"):
            r = requests.get(url, headers=headers, timeout=CONFIG["timeout"])
            return (info_block, url, r.status_code == 200 and "MPD" in r.text)
        elif url.endswith(".m3u8"):
            r = requests.get(url, headers=headers, timeout=CONFIG["timeout"])
            return (info_block, url, r.status_code == 200 and "#EXTM3U" in r.text)
        else:
            r = requests.head(url, headers=headers, timeout=CONFIG["timeout"], allow_redirects=True)
            return (info_block, url, r.status_code == 200)
    except:
        return (info_block, url, False)

def parse_m3u_lines(lines):
    blocks, curr = [], []
    for line in lines:
        s = line.strip()
        if s.startswith("#"):
            curr.append(s)
        elif s.startswith("http"):
            curr.append(s)
            blocks.append(curr)
            curr = []
    return blocks

def filter_and_save(input_path, output_path):
    if not os.path.exists(input_path):
        print("❌ 输入文件不存在:", input_path)
        return
    lines = open(input_path, encoding="utf‑8").readlines()
    blocks = parse_m3u_lines(lines)
    valid = []
    with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as exe:
        futures = []
        for blk in blocks:
            u = blk[-1]
            if is_china_ip(u):
                u = CONFIG["proxy_prefix"] + u
            futures.append(exe.submit(smart_check_url, blk[:-1], u))
        for f in tqdm(as_completed(futures), total=len(futures), desc="检测中"):
            info, final_url, ok = f.result()
            if ok:
                valid.append(info + [final_url, ""])
    with open(output_path, "w", encoding="utf‑8") as out:
        out.write("#EXTM3U\n")
        for blk in valid:
            for ln in blk:
                out.write(ln + "\n")
    print(f"✅ {len(valid)} 个频道有效，保存到 {output_path}")

if __name__ == "__main__":
    filter_and_save(CONFIG["input_file"], CONFIG["output_file"])
