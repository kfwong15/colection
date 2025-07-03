import requests
import re

# ✅ 下载 M3U 文件内容
def download_m3u(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ 下载失败：{url}：{e}")
        return ""

# ✅ 解析 M3U 内容，提取频道信息并去重
def parse_m3u(content):
    channels = {}
    lines = content.splitlines()
    current_channel = None

    for line in lines:
        if line.startswith("#EXTINF"):
            current_channel = line.strip()
        elif current_channel and line.startswith("http"):
            if line not in channels.values():  # 去除重复 URL
                channels[current_channel] = line.strip()
            current_channel = None

    return channels

# ✅ 获取 GitHub 上的 M3U 文件列表（你的仓库）
def get_m3u_urls_from_github(repo_url):
    raw_base = "https://raw.githubusercontent.com/kfwong15/colection/main/source/m3u/"
    api_url = "https://api.github.com/repos/kfwong15/colection/contents/source/m3u"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        files = response.json()
        return [raw_base + file["name"] for file in files if file["name"].endswith(".m3u")]
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取 GitHub 文件列表失败: {e}")
        return []

# ✅ 保存合并后的 M3U 文件
def save_m3u(channels, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write("#EXTM3U\n")
        for info, url in channels.items():
            file.write(f"{info}\n{url}\n")
    print(f"✅ 合并完成，保存为：{filename}")

# ✅ 主程序执行
if __name__ == "__main__":
    # 获取你仓库下所有 M3U 文件 URL
    urls = get_m3u_urls_from_github("https://github.com/kfwong15/colection/tree/main/source/m3u")

    all_channels = {}
    for url in urls:
        content = download_m3u(url)
        channels = parse_m3u(content)
        all_channels.update(channels)

    # 保存为 merge.m3u
    save_m3u(all_channels, "merge.m3u")
