import os, re, time, random, requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

CONFIG = {
    "timeout": 6, "max_workers": 15,
    "random_delay": (0.1, 0.5),
    "proxy_prefix": "https://myproxy.kfwong15.workers.dev/?url=",
    "china_ip_pattern": r"(\.cn|\.gov\.cn|\.edu\.cn|\.cctv|\.cntv|\.aliyun|\.chinaunicom|\.sm-hk)"
}

def is_china_source(url):
    return re.search(CONFIG["china_ip_pattern"], url) is not None

def smart_check(info_lines, url):
    time.sleep(random.uniform(*CONFIG["random_delay"]))
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        if url.endswith(".mpd"):
            r = requests.get(url, headers=headers, timeout=CONFIG["timeout"])
            ok = r.status_code == 200 and "MPD" in r.text
        elif url.endswith(".m3u8"):
            r = requests.get(url, headers=headers, timeout=CONFIG["timeout"])
            ok = r.status_code == 200 and "#EXTM3U" in r.text
        else:
            r = requests.head(url, headers=headers, timeout=CONFIG["timeout"], allow_redirects=True)
            ok = r.status_code == 200
    except:
        ok = False
    return (info_lines, url, ok)

def parse_blocks(lines):
    blocks = []; curr = []
    for line in lines:
        s = line.strip()
        if s.startswith("#"):
            curr.append(s)
        elif s.startswith("http"):
            curr.append(s)
            blocks.append(curr)
            curr = []
    return blocks

def process_file(src_path, dst_path):
    if not os.path.exists(src_path):
        print(f"⚠️ 跳过不存在：{src_path}")
        return 0
    lines = open(src_path, encoding="utf-8").readlines()
    blocks = parse_blocks(lines)
    results = []

    with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as exe:
        futures = []
        for block in blocks:
            url = block[-1]
            if is_china_source(url):
                url = CONFIG["proxy_prefix"] + url
            futures.append(exe.submit(smart_check, block[:-1], url))
        for f in tqdm(as_completed(futures), total=len(futures), desc=os.path.basename(src_path)):
            info_lines, final_url, ok = f.result()
            if ok:
                results.append(info_lines + [final_url, ""])
    if results:
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        with open(dst_path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for blk in results:
                for ln in blk:
                    f.write(ln + "\n")
    return len(results)

def main():
    base = os.getcwd()
    src_dir = os.path.join(base, "channels")
    dst_dir = os.path.join(base, "dist")
    total = {}

    for fname in os.listdir(src_dir):
        if fname.lower().endswith(".m3u"):
            src = os.path.join(src_dir, fname)
            dst = os.path.join(dst_dir, fname)
            count = process_file(src, dst)
            total[fname] = count

    print("✅ 检测完成，各分类有效频道数：")
    for k,v in total.items():
        print(f"   • {k}: {v}")

if __name__ == "__main__":
    main()
