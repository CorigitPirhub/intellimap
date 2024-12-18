from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

@app.route('/api/get-data', methods=['GET'])
def get_data():
    #获取input
    input = request.args.get('input')
    print("input:", input)
    # 构造返回的JSON数据,此处需要根据用户输入input询问大模型，让大模型生成JSON数组，格式如下
    json_data = [
        {"景点": "黄河游览区", "时长": "4.0小时"},
        {"景点": "郑州黄河风景名胜区", "时长": "3.0小时"},
        {"景点": "河南博物院", "时长": "3.0小时"},
        {"景点": "郑州动物园", "时长": "3.0小时"},
        {"景点": "少林寺", "时长": "6.0小时"},
    ]
    res_json = {
        "城市": "郑州",
        "计划": json_data
    }
    return jsonify(res_json)

@app.route('/api/post-data', methods=['POST'])
def post_data():
    # 处理POST请求
    data = request.json # data一定是个JSON数组
    
    # 在此处处理POST请求的数据，进行爬虫并且生成对应景点的介绍

    # 最后生成一个JSON数组返回，格式如下
    json_data = [
        {"景点": "黄河游览区","图片": "test.jpg", "介绍": "黄河游览区位于郑州市，是一个集旅游、文化、娱乐为一体的综合性景区。景区内有黄河大桥、黄河风景区、黄河博物馆等景点，是郑州市的一大旅游景点。"},
        {"景点": "郑州黄河风景名胜区", "图片": "test.jpg","介绍": "郑州黄河风景名胜区位于郑州市，是一个以黄河为主题的风景名胜区。景区内有黄河大桥、黄河风景区、黄河博物馆等景点，是郑州市的一大旅游景点。"},
        {"景点": "河南博物院", "图片": "test.jpg", "介绍": "河南博物院位于郑州市，是一个集文物收藏、陈列展览、学术研究为一体的综合性博物馆。博物馆内有众多珍贵文物，是郑州市的一大旅游景点。"},
        {"景点": "郑州动物园", "图片": "test.jpg", "介绍": "郑州动物园位于郑州市，是一个集动物观赏、科普教育、休闲娱乐为一体的综合性动物园。动物园内有众多珍稀动物，是郑州市的一大旅游景点。"},
        {"景点": "少林寺", "图片": "test.jpg", "介绍": "少林寺位于郑州市，是一个具有悠久历史和深厚文化底蕴的佛教寺庙。寺庙内有众多古迹和文物，是郑州市的一大旅游景点。"},
    ]
    return jsonify(json_data)



def start_server():
    global app
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5001)

if __name__ == '__main__':
    start_server()
