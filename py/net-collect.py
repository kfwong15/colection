import os
import subprocess
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# ✅ GitHub 設定（你的倉庫）
GITHUB_REPO_URL = "https://github.com/kfwong15/colection.git"
LOCAL_REPO_PATH = "/home/runner/work/colection/colection"
FILE_PATH = os.path.join(LOCAL_REPO_PATH, "source/m3u/1888.m3u")

# ✅ 爬取的目標網址
URLS = {
    "成人/綜合頻道": "https://www.yibababa.com/vod/",
    "台湾直播源 (yibababa)": "https://yibababa.com/tv/#tw",
    "台湾直播源 (aktv)": "https://aktv.top/"
}

# ✅ 步驟 1：確認是否需要 clone 倉庫
if not os.path.exists(LOCAL_REPO_PATH):
    print(f"⚠️ {LOCAL_REPO_PATH} 不存在，開始 Clone...")
    subprocess.run(["git", "clone", GITHUB_REPO_URL, LOCAL_REPO_PATH], check=True)
    print("✅ Clone 完成！")

# ✅ 步驟 2：啟動無頭瀏覽器
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
service = Service(ChromeDriverManager().install())

# ✅ 分類模板與關鍵字
pattern = re.compile(r"(.+?),\s*(http[^\s]+\.m3u8)")

categories = {
    "成人頻道": [], "體育頻道": [], "新聞頻道": [],
    "綜藝頻道": [], "電影頻道": [], "台湾直播源": [], "未分類頻道": []
}

keywords = {
    "成人頻道": ["成人", "直播", "18+", "X", "香蕉", "精", "潘", "松"],
    "體育頻道": ["體育", "足球", "NBA", "ESPN"],
    "新聞頻道": ["新聞", "CCTV", "BBC", "CNBC"],
    "綜藝頻道": ["綜藝", "娛樂", "Mnet"],
    "電影頻道": ["電影", "HBO", "Cinemax", "影視"]
}

# ✅ 步驟 3：逐一擷取直播源
for category, url in URLS.items():
    driver = None
    try:
        print(f"🔍 擷取 {category} 頻道中...")
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        driver.implicitly_wait(10)
        soup = BeautifulSoup(driver.page_source, "html.parser")
    except Exception as e:
        print(f"❌ Selenium 啟動失敗: {e}")
        exit(1)
    finally:
        if driver:
            driver.quit()

    for tag in soup.find_all(["p", "div", "span", "a"]):
        text = tag.get_text(separator="\n")
        matches = pattern.findall(text)
        for match in matches:
            channel_name = match[0].strip()
            stream_url = match[1].strip()

            if "台湾直播源" in category:
                categories["台湾直播源"].append((channel_name, stream_url))
                continue

            assigned = False
            for cat, words in keywords.items():
                if any(word in channel_name for word in words):
                    categories[cat].append((channel_name, stream_url))
                    assigned = True
                    break

            if not assigned:
                categories["未分類頻道"].append((channel_name, stream_url))

# ✅ 步驟 4：組合 m3u 播放格式內容
m3u_content = "#EXTM3U\n"

for category, channels in categories.items():
    if channels:
        m3u_content += f"\n#EXTGRP:{category}\n"
        for name, url in channels:
            m3u_content += f"#EXTINF:-1,{name}\n{url}\n"

# ✅ 步驟 5：Git pull 最新倉庫內容
try:
    subprocess.run(["git", "pull", "origin", "main"], cwd=LOCAL_REPO_PATH, check=True)
except subprocess.CalledProcessError as e:
    print(f"⚠️ `git pull` 失敗: {e}")

# ✅ 步驟 6：寫入 1888.m3u
os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write(m3u_content)

# ✅ 步驟 7：設定 Git 使用者資訊
subprocess.run(["git", "config", "--local", "user.name", "kfwong15"], cwd=LOCAL_REPO_PATH, check=True)
subprocess.run(["git", "config", "--local", "user.email", "actions@kfwong15.com"], cwd=LOCAL_REPO_PATH, check=True)

# ✅ 步驟 8：檢查是否有變更
status_output = subprocess.run(["git", "status", "--porcelain"], cwd=LOCAL_REPO_PATH, capture_output=True, text=True)

if not status_output.stdout.strip():
    print("⚠️ `1888.m3u` 沒有變更，不需要提交！")
    exit(0)

# ✅ 步驟 9：提交並推送到 GitHub
try:
    subprocess.run(["git", "add", FILE_PATH], cwd=LOCAL_REPO_PATH, check=True)
    subprocess.run(["git", "commit", "-m", "📡 更新 1888.m3u，新增分類頻道"], cwd=LOCAL_REPO_PATH, check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=LOCAL_REPO_PATH, check=True)
    print("✅ `1888.m3u` 已成功推送到 GitHub！")
except subprocess.CalledProcessError as e:
    print("❌ Git 操作失敗：", e)
