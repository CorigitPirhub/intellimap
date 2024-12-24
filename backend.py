from flask import Flask, request, jsonify
from flask_cors import CORS
from TourLLMChain import TourLLMChain
from spider import get_image_urls, download_images
from ScenicSpotProcessor import ScenicSpotProcessor
import os
import shutil
import concurrent.futures
import time  # 假设阻塞操作是sleep

app = Flask(__name__)
CORS(app) 

@app.route('/api/get-data', methods=['GET'])
def get_data():
    #获取input
    input = request.args.get('input')
    model_key = "cc862aedd49bca887df25916a75c329c.OiEqowH9EgzL1N1X"
    itinerary_chain = TourLLMChain(input, model_key)
    json_itinerary = itinerary_chain.generate_json_itinerary()
    city = itinerary_chain.extract_city()
    # 构造返回的JSON数据,此处需要根据用户输入input询问大模型，让大模型生成JSON数组，格式如下
    res_json = {
        "城市": city,
        "计划": json_itinerary
    }
    return jsonify(res_json)

@app.route('/api/post-data', methods=['POST'])
def post_data():
    json_data = []
    # 处理POST请求
    data = request.get_json() # data一定是个JSON数组
    city = data['城市']
    data = data['计划']
    num_images = 1  # 设置为1，只获取一张照片
    save_dir = "./images"
    delete_images(save_dir)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        for day in data:
            # 由于每个元素都是一个字典，并且只有一个键，我们可以这样获取键和值
            day_key, day_value = next(iter(day.items()))
            for attraction in day_value:
                query = attraction['景点']
                future = executor.submit(get_spot_info, query,city,num_images,save_dir)
                futures.append(future)
        
        # 等待所有任务完成
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            json_data.append(result)
    
    return jsonify(json_data)


def get_spot_info(query,city,num_images,save_dir):
    image_urls = get_image_urls(query, num_images)
    if image_urls:
        download_images(image_urls, save_dir, query)  # 传入 j=0，因为只有一张照片
        print("成功下载第一张图片！",query)
        processor = ScenicSpotProcessor(api_key="cc862aedd49bca887df25916a75c329c.OiEqowH9EgzL1N1X")
        description = processor.get_scenic_description(city, query)
        this_data = {
            "景点": query,
            "图片": f"{save_dir}/image_{query}.jpg",
            "介绍": description
        }
        return this_data
    else:
        print("未找到任何图片。",query)
        return None



def delete_images(save_dir):
    if not os.path.exists(save_dir):
        return
    for filename in os.listdir(save_dir):
        file_path = os.path.join(save_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def start_server():
    global app
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5001)

if __name__ == '__main__':
    start_server()
