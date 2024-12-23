import json
import re
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory


class TourLLMChain:
    def __init__(self, user_input, model_key):
        # 初始化用户输入和LLM模型
        self.user_input = user_input
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        
        self.llm_response = ChatOpenAI(
            temperature=0.95,
            model="glm-4-plus",
            openai_api_key=model_key,
            openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
        )

        self.llm_formatter = ChatOpenAI(
            temperature=0.95,
            model="glm-4-plus",
            openai_api_key=model_key,
            openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
        )
        
        # 定义输入校验的 prompt
        self.validation_prompt1 = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template("你是一个输入校验专家，负责判断用户输入是否与旅游相关。"),
                HumanMessagePromptTemplate.from_template(
                    "请判断以下内容是否与旅游相关：\n\n{user_input}\n\n"
                    "如果与旅游相关，请返回'相关'；如果无关，请返回'无关'，不要包含其他文字。"
                )
            ]
        )

        # 定义审查规则的 prompt
        self.validation_prompt2 = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(
                    "你是一个严格的输入审查专家，需要根据以下规则审查用户输入：\n"
                    "1. 输入能且仅能包含一个城市或同一个城市中的景点，不能出现两个城市或分别在两个城市的景点。\n"
                    "2. 输入必须合理，比如旅游时间不能太长或太短（时间范围为1到30天），一个很小的地方旅游时间应该更短（如北京理工大学旅行3天就不合理，但旅行1天就合理）。\n\n"
                    "根据规则，判断以下用户输入是否符合要求，返回如下内容：\n"
                    "- 如果符合规则，请仅返回“符合规则”。\n"
                    "- 如果违反规则1，返回“仅能规划一个城市！”。\n"
                    "- 如果违反规则2，返回“请提出合理的要求！”。\n"
                    "- 如果违反多条规则，返回“请提出合理的要求！”\n"
                ),
                HumanMessagePromptTemplate.from_template("{user_input}")
            ]
        )

        

        # 定义生成初步行程的 prompt
        self.initial_prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(
                    "你是一个专业的旅游规划师，为用户提供详细的旅游行程。"
                ),
                HumanMessagePromptTemplate.from_template(
                    f"{user_input}\n\n请根据以下要求生成旅游行程：\n"
                    "1. 请确保回复内容仅包含景点名称和游览时长，不要包含任何其他无关内容。\n"
                    "2. 行程应包括合理的游玩时间，按每天的景点安排,留足充足的休息时间\n"
                    "3. 大型景点游玩时间约为4-8小时，小型景点为1-3小时。\n"
                    "4. 每天的行程清单应包含景点名和预计游览时长，预计游览时长为明确的数字。\n"
                    "5. 如果用户旅游的地点较小，可以输出3个以内的地名\n"
                    "6. 考虑景点间的交通时间，并按时间顺序安排。\n"
                    
                    """
示例：
第1天：
鼓浪屿：6小时
厦门大学：2小时
南普陀寺：2小时
"""
                )
            ]
        )
        
        # 定义格式化的 prompt
        self.format_prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template("你是一个旅游行程内容的格式化专家。"),
                HumanMessagePromptTemplate.from_template(
                    "请将以下行程内容重新格式化为指定格式：\n\n"
                    "第1天：\n"
                    "景点名：xxx x小时\n"
                    "景点名：yyy y小时\n"
                    "请确保回复内容仅包含第N天、景点名称、冒号和游览时长，**不要包含任何其他文字或字符**。\n\n"
                    "需要格式化的内容如下：\n{formatted_content}"
                )
            ]
        )

        # 定义提取城市名的 prompt
        self.city_extraction_prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(
                    "你是一个旅游专家，能够从用户的需求中提取出涉及的城市名。"
                    "请从以下用户输入中提取最可能涉及的一个城市名，并仅返回城市名。"
                ),
                HumanMessagePromptTemplate.from_template("{user_input}")
            ]
        )
        
        # 创建提取城市名的链
        self.city_extraction_chain = LLMChain(
            llm=self.llm_response,
            prompt=self.city_extraction_prompt,
            memory=self.memory,
            verbose=True
        )

        
        # 创建校验链
        self.validation_chain1 = LLMChain(
            llm=self.llm_response,
            prompt=self.validation_prompt1,
            memory=self.memory,
            verbose=True
        )

        # 创建审查链
        self.validation_chain2 = LLMChain(
            llm=self.llm_response,
            prompt=self.validation_prompt2,
            memory=self.memory,
            verbose=True
        )

        # 创建初步行程生成链
        self.response_chain = LLMChain(
            llm=self.llm_response,
            prompt=self.initial_prompt,
            memory=self.memory,
            verbose=True
        )
        
        # 创建格式化链
        self.formatter_chain = LLMChain(
            llm=self.llm_formatter,
            prompt=self.format_prompt,
            memory=self.memory,
            verbose=True
        )

    def extract_city(self):
        """使用大模型提取用户输入中的城市名称"""
        city = self.city_extraction_chain.invoke({"user_input": self.user_input})
        return city['text'].strip()
    
    def validate_input1(self):
        """校验用户输入是否与旅游相关"""
        validation_response = self.validation_chain1.invoke({"user_input": self.user_input})
        validation_result = validation_response['text'].strip()
        if validation_result == "相关":
            return True
        return False
    
    def validate_input2(self):
        """使用大模型审查用户输入"""
        validation_response = self.validation_chain2.invoke({"user_input": self.user_input})
        validation_result = validation_response['text'].strip()
        return validation_result

    def generate_itinerary(self):
        """生成初步行程"""
        response = self.response_chain.invoke({"question": self.user_input})
        initial_content = response['text'].strip()
        print(f"初步行程内容：\n{initial_content}\n")
        return initial_content

    def format_itinerary(self, initial_content):
        """格式化行程内容"""
        formatted_response = self.formatter_chain.invoke({"formatted_content": initial_content})
        formatted_content = formatted_response['text'].strip()
        print(f"格式化后的行程内容：\n{formatted_content}\n")
        return formatted_content

    def parse_to_json(self, formatted_text):
        """将格式化内容解析为 JSON 结构，处理重复项和括号内容，支持 x-x小时 格式并计算平均值"""
        # 检查并删除 "格式化后的行程内容：" 这一部分
        if "格式化后的行程内容：\n" in formatted_text:
            formatted_text = formatted_text.split("格式化后的行程内容：\n")[1].strip()  # 删除该部分
        formatted_text = re.sub(r"[（(].*?[）)]", "", formatted_text)
        json_structure = []
        seen = set()  # 用于去重
        day_schedule = []  # 用于存储每天的行程
        current_day = None  # 当前处理的天数

        for line in formatted_text.splitlines():
            # 判断是否是“第x天”的行程
            day_match = re.match(r"第(\d+)天：", line)
            if day_match:
                # 保存上一天的行程（如果有的话）
                if current_day is not None:
                    json_structure.append({f"第{current_day}天": day_schedule})
                # 新的一天开始，重置 day_schedule
                current_day = day_match.group(1)
                day_schedule = []  # 清空之前的行程

            # 匹配格式化内容中的景点和时长，包括括号和 x-x小时 格式
            attraction_match = re.match(r"([\u4e00-\u9fa5a-zA-Z0-9（）(),/]+)：?\s*(\d+(\.\d*)?)小时", line)
            if attraction_match:
                name = attraction_match.group(1).strip()  # 景点名
                duration_range = attraction_match.group(2)  # 时长（可能是范围）

                # 处理 x-x小时 格式，计算平均值
                if '-' in duration_range:
                    start, end = map(float, duration_range.split('-'))
                    duration = f"{(start + end) / 2:.1f}小时"  # 平均值保留1位小数
                else:
                    duration = f"{float(duration_range):.1f}小时"  # 单一时长

                # 去重：避免重复景点
                if name not in seen:
                    seen.add(name)
                    day_schedule.append({"景点": name, "时长": duration})

        # 添加最后一天的行程（如果有的话）
        if current_day is not None:
            json_structure.append({f"第{current_day}天": day_schedule})

        if not json_structure:
            raise ValueError("无法解析为有效的 JSON 格式")

        return json_structure

    def generate_json_itinerary(self):
        """生成并格式化行程 JSON"""
        attempts = 0
        max_attempts = 3
        json_result = None

        # 校验输入
        if not self.validate_input1():
            return "请输入和旅游相关的信息"
        
        # 审查输入
        validation_result = self.validate_input2()
        if validation_result != "符合规则":
            return validation_result

        # 生成并格式化行程，尝试将格式化内容转换为 JSON
        while json_result is None and attempts < max_attempts:
            try:
                initial_content = self.generate_itinerary()
                formatted_content = self.format_itinerary(initial_content)
                json_result = self.parse_to_json(formatted_content)
                print("转换为 JSON 格式成功：")
                print(json.dumps(json_result, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"转换为 JSON 格式失败，尝试重新生成行程。错误信息: {e}")
                attempts += 1

        if json_result is None:
            print("多次尝试后，未能成功生成有效的 JSON 格式行程。")
        return json_result

if __name__ == "__main__":
    # 使用示例
    user_input = "我要去北京旅游5天，推荐一下"
    model_key = "cc862aedd49bca887df25916a75c329c.OiEqowH9EgzL1N1X"

    itinerary_chain = TourLLMChain(user_input, model_key)
    json_itinerary = itinerary_chain.generate_json_itinerary()
    print(json_itinerary)
    city = itinerary_chain.extract_city()
    print(city)