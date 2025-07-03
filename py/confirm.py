import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time
import random
import logging
from tqdm import tqdm

# ✅ 日志配置：输出到控制台与 log 文件
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("confirm_channel_filter.log"),
        logging.StreamHandler(),
    ],
)

# ✅ 项目配置（根据你的仓库修改）
CONFIG = {
    "m3u_url": "https://raw.githubusercontent.com/kfwong15/colection/main/merge.m3u",  # 你的合并频道列表
    "save_path": "./merge.m3u",            # 本地保存路径
    "max_workers": 10,                     # 并发线程数
    "request_timeout": 3,                  # 请求超时秒数
    "random_delay": (0.1, 0.5),            # 请求间的延迟范围（防止频繁访问）
}

# ✅ 步骤 1：下载合并频道列表（merge.m3u）
def download_m3u_file(url, save_path):
    try:
        logging.info(f"开始下载 M3U 文件: {url}")
        response = requests.get(url)
        response.raise_for_status()
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        with open(save_path, "wb") as file:
            file.write(response.content)
        logging.info(f"✅ 下载完成: {save_path}")
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ 下载失败: {e}")
        raise

# ✅ 步骤 2：去除重复频道并排序
def remove_duplicates_and_sort(input_file):
    logging.info("🔍 去除重复频道并排序...")
    channels = {}
    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF:"):
            channel_info = lines[i].strip()
            channel_url = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if channel_url not in channels:
                channels[channel_url] = channel_info
            i += 2
        else:
            i += 1

    sorted_channels = sorted(channels.items(), key=lambda x: x[1])

    with open(input_file, "w", encoding="utf-8") as file:
        for url, info in sorted_channels:
            file.write(info + "\n")
            file.write(url + "\n")

    logging.info(f"✅ 完成去重排序，保存至: {input_file}")

# ✅ 步骤 3：检查每个频道是否能访问
def check_channel_validity(channel_info, channel_url):
    try:
        time.sleep(random.uniform(*CONFIG["random_delay"]))
        response = requests.head(channel_url, timeout=CONFIG["request_timeout"])
        return channel_info, channel_url, response.status_code == 200
    except requests.exceptions.RequestException as e:
        logging.debug(f"⛔ 频道检测失败: {channel_info} - {e}")
        return channel_info, channel_url, False

# ✅ 步骤 4：筛选有效频道，移除坏链
def filter_invalid_channels(input_file):
    logging.info("🧪 开始检测频道链接是否有效...")
    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    valid_lines = []
    futures = []

    with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as executor:
        for i in range(0, len(lines), 2):
            if i + 1 >= len(lines):
                break
            channel_info = lines[i].strip()
            channel_url = lines[i + 1].strip()
            futures.append(executor.submit(check_channel_validity, channel_info, channel_url))

        for future in tqdm(as_completed(futures), total=len(futures), desc="🧪 检查中"):
            channel_info, channel_url, is_valid = future.result()
            if is_valid:
                valid_lines.append(channel_info + "\n")
                valid_lines.append(channel_url + "\n")
                logging.info(f"✅ 有效频道: {channel_info}")
            else:
                logging.warning(f"❌ 无效频道: {channel_info}")

    with open(input_file, "w", encoding="utf-8") as file:
        file.writelines(valid_lines)

    logging.info("✅ 频道过滤完成，文件已更新。")

# ✅ 主程序入口
def main():
    try:
        download_m3u_file(CONFIG["m3u_url"], CONFIG["save_path"])
        remove_duplicates_and_sort(CONFIG["save_path"])
        filter_invalid_channels(CONFIG["save_path"])
        logging.info("🎉 所有步骤已完成")
    except Exception as e:
        logging.error(f"❌ 程序出错: {e}")

if __name__ == "__main__":
    main()
