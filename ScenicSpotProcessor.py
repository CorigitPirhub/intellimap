import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
import json
from zhipuai import ZhipuAI


class ScenicSpotProcessor:
    def __init__(self, api_key, output_dir="景点图片", num_images=1):
        self.api_key = api_key
        self.output_dir = output_dir  # 图片保存目录
        self.num_images = num_images  # 需要下载的图片数量（这里只保存一张）
        self.headers = {"User-Agent": "Mozilla/5.0"}

        # 初始化 ZhipuAI 模型
        self.model = ZhipuAI(api_key=api_key)

        # 创建图片保存目录
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _get_image_links(self, search_term):
        """通过 Selenium 获取图片链接"""
        print(f"启动浏览器爬取: {search_term}...")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # 无头模式运行
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        # 构建百度图片搜索 URL
        base_url = f"https://image.baidu.com/search/index?tn=baiduimage&word={quote(search_term)}"
        driver.get(base_url)
        time.sleep(2)  # 确保页面初步加载

        # 滚动加载页面（限制滚动次数）
        max_scrolls = 1
        for _ in range(max_scrolls):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # 等待页面加载完成

        # 使用 BeautifulSoup 解析页面，获取图片链接
        soup = BeautifulSoup(driver.page_source, "html.parser")
        img_tags = soup.find_all("img", class_="main_img", limit=self.num_images)

        image_links = []
        for img in img_tags:
            img_url = img.get("data-imgurl") or img.get("src")
            if img_url:
                image_links.append(img_url)

        driver.quit()
        print(f"{search_term}: 获取到 {len(image_links)} 个图片链接")
        return image_links

    def _download_image(self, img_url, city, spot):
        """下载单张图片"""
        file_name = f"{city}_{spot}.jpg"
        file_path = os.path.join(self.output_dir, file_name)

        # 如果文件已存在，直接返回路径
        if os.path.exists(file_path):
            print(f"{file_path} 已存在，跳过下载")
            return file_path

        # 下载图片
        try:
            print(f"正在下载图片: {img_url}")
            response = requests.get(img_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"图片下载完成: {file_path}")
                return file_path
            else:
                print(f"图片下载失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"图片下载出错: {e}")

        return None

    def get_scenic_description(self, city, spot):
        """调用大语言模型生成景点介绍"""
        prompt = f"请介绍{city}的{spot}景点。"
        response = self.model.chat.completions.create(
            model="GLM-4-Flash",
            messages=[{"role": "user", "content": prompt}]
        )

        # 检查返回值
        if hasattr(response, "choices") and len(response.choices) > 0:
            return response.choices[0].message.content.strip()

        # 如果未能成功获取内容，返回默认提示
        return "无法获取景点介绍，请稍后重试。"

    def process_spot(self, city, spot):
        """处理单个景点的主流程"""
        print(f"\n开始处理景点: {city} {spot}")

        # 搜索关键词
        search_term = f"{city} {spot}"

        # 获取图片链接
        image_links = self._get_image_links(search_term)
        if not image_links:
            print(f"{search_term}: 未获取到任何图片链接")
            return None

        # 下载第一张图片
        image_path = self._download_image(image_links[0], city, spot)

        # 获取景点介绍
        description = self.get_scenic_description(city, spot)

        # 构建结果
        result = {
            "景点": spot,
            "城市": city,
            "图片": image_path,  # 只保存一张图片的路径
            "介绍": description
        }
        return result

    def process_all_spots(self, json_data, output_file="scenic_data.json"):
        """处理多个景点并保存结果为 JSON"""
        results = []

        # 并行处理多个景点
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(self.process_spot, entry["城市"], entry["景点"])
                for entry in json_data
            ]
            for future in futures:
                result = future.result()
                if result:
                    results.append(result)

        # 保存结果为 JSON 文件
        print(result)
        # with open(output_file, "w", encoding="utf-8") as f:
        #     json.dump(results, f, ensure_ascii=False, indent=4)

        print(f"\n所有景点处理完成，结果保存为 {output_file}")


if __name__ == "__main__":
    # JSON 数据
    json_data = [
        {"城市": "北京", "景点": "天安门"},
    ]

    # 初始化类并处理景点
    processor = ScenicSpotProcessor(api_key="cc862aedd49bca887df25916a75c329c.OiEqowH9EgzL1N1X")
    processor.process_all_spots(json_data)
