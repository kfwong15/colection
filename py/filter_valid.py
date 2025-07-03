import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time
import random
from tqdm import tqdm

# 配置
CONFIG = {
    "input_file": "merge.m3u",         # 输入文件
    "output_file": "valid.m3u",        # 输出文件（可播放频道）
    "timeout": 5,                      # 请求超时时间
    "max_workers": 15,                 # 并发线程数
    "random_delay": (0.1, 0.5),        # 请求间隔
}


# 检查频道链接是否有效
def check_url(channel_info, url):
    try:
        time.sleep(random.uniform(*CONFIG["random_delay"]))  # 避免请求过快被封
        response = requests.head(url, timeout=CONFIG["timeout"], allow_redirects=True)
        return (channel_info, url, response.status_code == 200)
    except:
        return (channel_info, url, False)


# 过滤失效频道
def filter_invalid_channels(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"❌ 找不到文件：{input_path}")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    valid_channels = []
    futures = []
    with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as executor:
        for i in range(0, len(lines), 2):
            if i + 1 >= len(lines):
                continue
            info = lines[i].strip()
            url = lines[i + 1].strip()
            futures.append(executor.submit(check_url, info, url))

        for future in tqdm(as_completed(futures), total=len(futures), desc="检测频道有效性"):
            info, url, is_valid = future.result()
            if is_valid:
                valid_channels.append(info + "\n")
                valid_channels.append(url + "\n")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(valid_channels)

    print(f"\n✅ 检测完成，保存有效频道到：{output_path}")


if __name__ == "__main__":
    filter_invalid_channels(CONFIG["input_file"], CONFIG["output_file"])
