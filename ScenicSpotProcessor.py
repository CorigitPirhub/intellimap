from zhipuai import ZhipuAI

class ScenicSpotProcessor:
    def __init__(self, api_key):
        self.api_key = api_key

        # 初始化 ZhipuAI 模型
        self.model = ZhipuAI(api_key=api_key)

    def get_scenic_description(self, city, spot):
        """调用大语言模型生成景点介绍"""
        prompt = f"请介绍{city}的{spot}景点。简单介绍，几句话即可。"
        response = self.model.chat.completions.create(
            model="GLM-4-Flash",
            messages=[{"role": "user", "content": prompt}]
        )

        # 检查返回值
        if hasattr(response, "choices") and len(response.choices) > 0:
            return response.choices[0].message.content.strip()

        # 如果未能成功获取内容，返回默认提示
        return "无法获取景点介绍，请稍后重试"

if __name__ == "__main__":
    # JSON 数据
    json_data = [
        {"城市": "北京", "景点": "天安门"},
    ]
    # 初始化类并处理景点
    processor = ScenicSpotProcessor(api_key="cc862aedd49bca887df25916a75c329c.OiEqowH9EgzL1N1X")
    print(processor.get_scenic_description("北京", "天安门"))
