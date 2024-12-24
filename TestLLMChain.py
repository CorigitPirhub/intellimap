import logging
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI
from TourLLMChain import TourLLMChain
import pandas as pd
import re


class TestLLMChain:
    def __init__(self, model_key, max_seeds=5, max_variants_per_seed=5):
        self.model_key = model_key
        self.max_seeds = max_seeds  # 种子最大数量
        self.max_variants_per_seed = max_variants_per_seed  # 每个种子的最大变异数量

        # 初始化种子生成链
        self.valid_seed_chain = self._create_chain(
            "有效测试用例生成器",
            """
# 有效测试用例生成器

## 测试目标
生成一系列 **有效的测试用例**，以测试大模型在生成旅游行程时的能力。

## 测试要求 
1. **有效性**：测试用例必须符合 LLMChain 的生成要求，能够生成合理的旅游行程。  
2. **全面性**：测试用例应尽可能全面，包含各种可能的输入场景。  
3. **独特性**：每次生成的测试用例应与之前生成的测试用例截然不同，具体表现为：
   - **主题差异**：测试用例的目标（如旅游地点、行程偏好等）必须不同。  
   - **表达差异**：测试用例的语言表达应避免重复使用同样的句式或关键词。  
   - **结构差异**：测试用例的内容结构应尽量多样化，避免固定的格式或顺序。 
4. **多样性**：测试用例应涵盖多种旅游主题。
5. **格式**：**生成结果仅包含测试用例，不包含任何其他内容。**每条测试用例以换行符分隔。

## 被测试任务
为用户提供详细的旅游行程。

### 生成旅游行程的具体要求：
1. 回复内容应仅包含 **景点名称** 和 **游览时长**，不得包含任何其他无关内容。  
2. 行程应包括合理的游玩时间，按每天的景点安排，并留足充足的休息时间。  
3. **大型景点** 游玩时间约为 **4-8小时**，**小型景点** 游玩时间约为 **1-3小时**。  
4. 每天的行程清单应包含景点名和预计游览时长，并明确以数字表示时长。  
5. 考虑景点间的交通时间，并按时间顺序合理安排。  

## 示例测试用例
我想去北京旅游，请帮我规划一个两日游行程。
西安，我计划三天两夜，请推荐一些适合年轻人的景点。
我想花一周的时间好好体验一下内蒙古的草原。

请根据以上要求生成有效的测试用例。请重点满足**独特性**和**格式**要求"""
        )
        self.invalid_seed_chain = self._create_chain(
            "无效测试用例生成器",
            """
# 无效测试用例生成器

## 被测试任务
为用户提供详细的旅游行程

## 测试目标
生成一系列 **无效的测试用例**，以测试模型在处理无效测试用例时的行为。

## 无效测试用例定义
满足以下任意条件的输入为无效测试用例,每条测试用例应该只满足其中一条：
1. 与旅行无关的输入
2. 多城市的输入
3. 城市为国外的输入
4. 旅游时间过长的输入（旅行超过30天）
5. 旅游时间过短的输入（旅行小于1天）

## 测试要求
1. **无效性**：生成的测试用例应为无效测试用例。
2. **多样性**：测试用例应涵盖多种与旅游无关的输入场景（如财务分析、烹饪指南等）。  
3. **独特性**：每次生成的测试用例应与之前生成的测试用例截然不同，具体表现为：
   - **主题差异**：测试用例的目标（如旅游地点、行程偏好等）必须不同。  
   - **表达差异**：测试用例的语言表达禁止重复使用同样的句式或关键词。  
   - **结构差异**：测试用例的内容结构应尽量多样化，避免固定的格式或顺序。 
4. **格式**：**生成结果仅包含测试用例，不包含任何其他内容。**每条测试用例以换行符分隔。
5. 部分用例应该测试边界条件，如不容易界定是否为无效的输入

请根据以上要求生成无效的测试用例。请重点满足**独特性**和**格式**要求
            """
        )
        self.valid_variant_chain = self._create_chain(
            "有效测试用例变异器",
            """
# 有效测试用例变异器

## 测试目标
基于给定的 **有效测试用例**，生成其变异版本。

## 种子输入
{seed}

## 被测试任务
为用户提供详细的旅游行程。

## 变异要求
1. **基于原始输入**：变异内容需以原始有效测试用例为基础，进行修改、扩展或替换。  
2. **逻辑合理**：变异后的内容需符合 LLMChain 的生成要求，保持测试用例的有效性。
3. **格式**：**生成结果仅包含测试用例，不包含任何其他内容。**每条测试用例以换行符分隔。

## 示例变异
- 原始输入为 "北京，计划两日游，目标是涵盖多个文化遗址"
变异为：
西安，规划一日游，聚焦自然景点。  
上海，安排两日游，重点考察人文景观，如高楼大厦。

请按照以上要求，基于种子生成变异版本。请注意，**生成结果仅包含测试用例，测试用例之间以换行符分隔，确保我的程序可以直接读取并使用，不包含任何其他内容或符号，不要有“以下是根据您的要求生成的有效测试用例：”这种开头。**请严格满足格式要求。
            """
        )
        self.invalid_variant_chain = self._create_chain(
            "无效测试用例变异器",
            """
# 无效测试用例变异器

## 测试目标
基于给定的 **无效测试用例**，生成其变异版本。

## 种子输入
{seed}

## 变异要求
1. **基于原始输入**：变异内容需以原始无效测试用例为基础，进行修改、扩展或替换。  
2. **保持无效性**：变异后的内容仍需与旅游主题无关。
3. **格式**：**生成结果仅包含测试用例，不包含任何其他内容**。每条测试用例以换行符分隔。
4. 部分用例应该测试边界条件，如不容易界定是否和旅游相关的输入

## 示例变异
- 原始输入为 "请帮我分析一份财务报表"，  
变异为：
生成关于家庭预算的详细计划。  
请帮我考察这些财务信息的真实性。

请按照以上要求，基于种子生成变异版本。请注意，**生成结果仅包含测试用例，测试用例之间以换行符分隔，确保我的程序可以直接读取并使用，不包含任何其他内容或符号，不要有“以下是根据您的要求生成的有效测试用例：”这种开头。**请严格满足格式要求。
            """
        )

        # 设置日志记录
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s',
            filename='test_log.log',
            filemode='w'  # 每次运行覆盖日志文件
        )
        self.logger = logging.getLogger(__name__)

    def _create_chain(self, title, prompt_content):
        """创建测试链"""
        prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(f"你是一个{title}。"),
                HumanMessagePromptTemplate.from_template(prompt_content)
            ]
        )
        llm = ChatOpenAI(
            temperature=0.95,
            model="glm-4",
            openai_api_key=self.model_key,
            openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
        )
        return LLMChain(llm=llm, prompt=prompt, verbose=True)

    def _filter_chinese_lines(self, text):
        """筛选包含中文的行，并去掉第一行和最后一行"""
        lines = text.splitlines()  # 分行处理
        # 跳过第一行和最后一行，保留中间的有效内容
        filtered_lines = [line for line in lines[1:-1] if re.search(r'[\u4e00-\u9fa5]', line)]
        return filtered_lines
    
    def generate_seeds_and_variants(self, seed_chain, variant_chain, description):
        """生成测试用例及变异，返回两个一维数组：seeds 和 variants"""
        print(f"开始生成 {description} 种子...")

        # 生成种子并筛选有效内容
        seed_response = seed_chain.invoke({"seed": "开始生成测试用例"})['text'].strip()
        seeds = self._filter_chinese_lines(seed_response)[:self.max_seeds]  # 限制数量
        print(f"{description} 种子生成完成，共生成 {len(seeds)} 个（最多取前 {self.max_seeds} 个）。")

        # 对每个种子生成变异
        variants = []
        for seed in seeds:
            print(f"生成种子: {seed} 的变异...")
            variant_response = variant_chain.invoke({"seed": seed})['text'].strip()
            variant_list = self._filter_chinese_lines(variant_response)[:self.max_variants_per_seed]  # 限制数量
            if not variant_list:
                print(f"种子 {seed} 没有生成任何有效的变异测试用例！")
            else:
                variants.extend(variant_list)  # 将当前种子的变异添加到扁平化的列表中
            print(f"种子 {seed} 变异完成，生成了 {len(variant_list)} 个变异。")

        return seeds, variants


    def generate_test_cases(self, seed_chain, variant_chain, description):
        """生成测试用例及变异"""
        print(f"开始生成 {description} 种子...")

        # 生成种子并筛选有效内容
        seed_response = seed_chain.invoke({"seed": "开始生成测试用例"})['text'].strip()
        seeds = self._filter_chinese_lines(seed_response)[:self.max_seeds]  # 限制数量
        print(f"{description} 种子生成完成，共生成 {len(seeds)} 个（最多取前 {self.max_seeds} 个）。")

        # 对每个种子生成变异
        variants = []
        for seed in seeds:
            print(f"生成种子: {seed} 的变异...")
            variant_response = variant_chain.invoke({"seed": seed})['text'].strip()
            variant_list = self._filter_chinese_lines(variant_response)[:self.max_variants_per_seed]  # 限制数量
            if not variant_list:
                print(f"种子 {seed} 没有生成任何有效的变异测试用例！")
            variants.append({"seed": seed, "variants": variant_list})
            print(f"种子 {seed} 变异完成，生成了 {len(variant_list)} 个变异。")

        return seeds, variants


    def test_tour_chain(self):
        """执行测试"""
        print("生成有效测试用例及变异...")
        valid_seeds, valid_variants = self.generate_test_cases(
            self.valid_seed_chain, self.valid_variant_chain, "有效测试用例"
        )
        print("生成无效测试用例及变异...")
        invalid_seeds, invalid_variants = self.generate_test_cases(
            self.invalid_seed_chain, self.invalid_variant_chain, "无效测试用例"
        )

        # 测试并记录日志
        self.logger.info("测试开始")
        self._log_test_results("有效测试用例", valid_variants, self.model_key)
        self._log_test_results("无效测试用例", invalid_variants, self.model_key)

    def _log_test_results(self, category, test_cases, model_key):
        """记录测试结果到表格中"""
        results_data = []

        self.logger.info(f"\n类别: {category}")
        for case in test_cases:
            seed = case["seed"]
            self.logger.info(f"种子测试用例: {seed}")
            for variant in case["variants"]:
                self.logger.info(f"变异测试用例: {variant}")

                # 每次重新实例化 TourLLMChain，并传入当前测试用例
                tour_chain = TourLLMChain(user_input=variant, model_key=model_key)
                result = tour_chain.generate_json_itinerary()
                formatted_result = result if result else '无行程生成'

                # 添加测试用例及结果到列表
                results_data.append({
                    "类别": category,
                    "种子测试用例": seed,
                    "变异测试用例": variant,
                    "生成结果": formatted_result
                })

                self.logger.info(f"生成结果: {formatted_result}")

        # 保存结果到 CSV
        results_df = pd.DataFrame(results_data)
        filename = f"{category}_测试结果.csv"
        results_df.to_csv(filename, index=False, encoding='utf-8-sig')

        print(f"测试结果已保存到文件: {filename}")
    
    def demo_test_case(self, seed_chain, variant_chain, model_key):
        """运行一次性演示，生成一个种子及其变异，并测试结果"""
        print("开始Demo测试...")

        # 生成一个种子
        seed_response = seed_chain.invoke({"input": "开始生成测试用例"})['text'].strip()
        seeds = self._filter_chinese_lines(seed_response)[:1]  # 只取第一个种子
        if not seeds:
            print("未生成任何有效种子！")
            return
        seed = seeds[0]
        print(f"生成的种子: {seed}")

        # 基于种子生成变异
        variant_response = variant_chain.invoke({"seed": seed})['text'].strip()
        variants = self._filter_chinese_lines(variant_response)[:3]  # 只取前3个变异
        if not variants:
            print("未生成任何有效的变异测试用例！")
            return
        print(f"种子的变异测试用例: {variants}")

        # 测试变异
        results_data = []
        for variant in variants:
            # 每次重新实例化 TourLLMChain，并传入变异测试用例
            tour_chain = TourLLMChain(user_input=variant, model_key=model_key)
            result = tour_chain.generate_json_itinerary()
            formatted_result = result if result else '请输入和旅游相关的信息'

            # 收集结果
            results_data.append({
                "种子测试用例": seed,
                "变异测试用例": variant,
                "生成结果": formatted_result
            })

        # 将结果展示为表格
        results_df = pd.DataFrame(results_data)
        print("测试结果：")
        print(results_df)

        # 保存结果到 CSV 文件
        results_df.to_csv("demo_test_results.csv", index=False, encoding='utf-8-sig')
        print("Demo测试结果已保存到文件: demo_test_results.csv")



# 使用示例
if __name__ == "__main__":
    model_key = "cc862aedd49bca887df25916a75c329c.OiEqowH9EgzL1N1X"

    # 初始化 TestLLMChain
    test_chain = TestLLMChain(model_key)

    # 执行测试
    # test_chain.test_tour_chain()
    invalid_seeds, invalid_variants = test_chain.generate_seeds_and_variants(
            test_chain.invalid_seed_chain, test_chain.invalid_variant_chain, "无效测试用例"
        )
    print(invalid_seeds)
    print(invalid_variants)

    # # 调用 demo 测试
    # test_chain.demo_test_case(
    #     seed_chain=test_chain.valid_seed_chain,
    #     variant_chain=test_chain.valid_variant_chain,
    #     model_key=model_key
    # )