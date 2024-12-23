import requests
from bs4 import BeautifulSoup
import os

def get_image_urls(query, num_images):
    url = f"https://www.bing.com/images/async?q={query}&first=0&count={num_images}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    image_tag = soup.find("img", class_="mimg")
    if image_tag:
        image_url = image_tag["src"]
        return [image_url]
    else:
        return []


def download_images(image_urls, save_dir,j):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    for i, url in enumerate(image_urls):
        response = requests.get(url)
        with open(f"{save_dir}/image_{j}_{i}.jpg", "wb") as f:
            f.write(response.content)

if __name__ == "__main__":
    query = "天安门"
    num_images = 1  # 设置为1，只获取一张照片
    save_dir = "images"

    image_urls = get_image_urls(query, num_images)
    if image_urls:
        download_images(image_urls, save_dir, 0)  # 传入 j=0，因为只有一张照片
        print("成功下载第一张图片！")
    else:
        print("未找到任何图片。")
