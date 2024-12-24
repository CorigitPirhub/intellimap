from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from TestLLMChain import TestLLMChain


# 替换为你的本地 HTML 文件路径（确保路径正确）
file_path = "gaodemap.html"

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
combined = invalid_seeds+invalid_variants
# 初始化 WebDriver
driver = webdriver.Chrome()

# 打开本地 HTML 文件
driver.get(file_path)

# 等待页面加载
time.sleep(2)

# 示例：逐步输入数组内容并等待用户确认
try:
    # 定位 input 和按钮
    input_element = driver.find_element(By.ID, "footerText")
    submit_button = driver.find_element(By.ID, "footerButton")

    # 输入数组内容
    input_values = invalid_variants

    for value in input_values:
        # 清空输入框
        input_element.clear()

        # 输入当前值
        input_element.send_keys(value)
        print(f"Inputting: {value}")

        # 点击提交按钮
        submit_button.click()

        # 等待用户观察生成结果
        print("Waiting for user confirmation... Type 'yes' to continue.")
        while True:
            user_input = input("Type 'yes' to proceed to the next input: ").strip().lower()
            if user_input == "yes":
                break
            else:
                print("Invalid input. Please type 'yes' to proceed.")

        # 等待一小段时间后继续（可选）
        time.sleep(1)

    print("All inputs processed!")

except Exception as e:
    print("An error occurred:", e)

# 关闭浏览器
driver.quit()