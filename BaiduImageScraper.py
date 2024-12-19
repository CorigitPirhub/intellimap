import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

class BaiduImageScraper:
    def __init__(self, keyword, output_dir="images", num_images=3):
        self.keyword = keyword
        self.output_dir = os.path.join(output_dir, keyword)  # 为每个景点创建文件夹
        self.num_images = num_images
        self.base_url = f"https://image.baidu.com/search/index?tn=baiduimage&word={quote(self.keyword)}"
        self.headers = {"User-Agent": "Mozilla/5.0"}

        # 创建输出目录
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _get_image_links(self):
        print(f"启动浏览器爬取景点: {self.keyword}...")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # 无头模式运行
        options.add_argument("--disable-gpu")
        options.page_load_strategy = "eager"
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        driver.get(self.base_url)
        time.sleep(2)  # 确保页面初步加载

        # 滚动加载页面
        max_scrolls = 3  # 限制滚动次数
        for _ in range(max_scrolls):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # 等待每次滚动加载完成

        # 提取图片链接
        soup = BeautifulSoup(driver.page_source, "html.parser")
        img_tags = soup.find_all("img", class_="main_img", limit=self.num_images)

        image_links = []
        for img in img_tags:
            img_url = img.get("data-imgurl") or img.get("src")
            if img_url:
                image_links.append(img_url)

        driver.quit()
        print(f"{self.keyword}: 获取到 {len(image_links)} 个图片链接")
        return image_links

    def _download_image(self, img_url, index):
        """单张图片下载"""
        file_path = os.path.join(self.output_dir, f"{self.keyword}_{index + 1}.jpg")
        if os.path.exists(file_path):
            print(f"{file_path} 已存在，跳过下载")
            return

        try:
            print(f"正在下载图片 {index + 1}: {img_url}")
            response = requests.get(img_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"图片 {index + 1} 下载完成: {file_path}")
            else:
                print(f"图片 {index + 1} 下载失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"图片 {index + 1} 下载出错: {e}")

    def scrape_images(self):
        """主流程：获取图片链接并下载图片"""
        image_links = self._get_image_links()
        if not image_links:
            print(f"{self.keyword}: 未获取到任何图片链接")
            return

        print(f"{self.keyword}: 开始下载图片")
        with ThreadPoolExecutor(max_workers=5) as executor:  # 并行下载
            for index, img_url in enumerate(image_links):
                executor.submit(self._download_image, img_url, index)

        print(f"{self.keyword}: 图片爬取完成")

if __name__ == "__main__":
    # JSON 数据
    json_data = [
        {"景点": "黄河游览区", "时长": "4.0小时"},
        {"景点": "郑州黄河风景名胜区", "时长": "3.0小时"},
        {"景点": "河南博物院", "时长": "3.0小时"},
        {"景点": "郑州动物园", "时长": "3.0小时"},
        {"景点": "少林寺", "时长": "6.0小时"},
    ]

    output_dir = "景点图片"  # 图片保存总目录
    num_images_per_spot = 1  # 每个景点下载的图片数量

    def process_spot(entry):
        """处理单个景点"""
        keyword = entry["景点"]
        print(f"\n开始处理景点: {keyword}")
        scraper = BaiduImageScraper(keyword=keyword, output_dir=output_dir, num_images=num_images_per_spot)
        scraper.scrape_images()

    # 使用线程池并行处理多个景点
    with ThreadPoolExecutor(max_workers=3) as executor:  # 并行处理景点
        executor.map(process_spot, json_data)
