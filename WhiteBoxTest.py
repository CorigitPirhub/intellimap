import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from TestLLMChain import TestLLMChain

# 本地 HTML 文件路径
file_path = "E:/git/TourAssistant/intellimap/gaodemap.html"

# 初始化 WebDriver
driver = webdriver.Chrome()

# 打开本地 HTML 文件
driver.get(file_path)
driver.set_window_size(1200, 800)
# 等待页面加载
time.sleep(2)

# 示例：逐步输入数组内容并等待用户确认
try:
    # 定位 input 和按钮
    input_element = driver.find_element(By.ID, "footerText")
    submit_button = driver.find_element(By.ID, "footerButton")
    model_key = "cc862aedd49bca887df25916a75c329c.OiEqowH9EgzL1N1X"

    # 初始化 TestLLMChain
    test_chain = TestLLMChain(model_key)

    # 执行测试生成用例
    invalid_seeds, invalid_variants = test_chain.generate_test_cases(
        test_chain.invalid_seed_chain, test_chain.invalid_variant_chain, "无效测试用例"
    )
    print(invalid_seeds)
    print(invalid_variants)
    combined = invalid_seeds + invalid_variants

    # 准备记录测试结果
    results = []

    for value in combined:
        # 清空输入框
        input_element.clear()

        # 输入当前测试用例
        input_element.send_keys(value)
        print(f"Inputting: {value}")

        # 点击提交按钮
        submit_button.click()

        # 等待用户观察生成结果
        print("Waiting for user confirmation... Type 'y' for pass or 'n' for fail.")
        while True:
            user_input = input("Type 'y' for pass or 'n' for fail: ").strip().lower()
            if user_input in ["y", "n"]:
                # 记录测试用例和结果
                is_pass = "通过" if user_input == "y" else "未通过"
                results.append({"测试用例": value, "是否通过": is_pass})
                break
            else:
                print("Invalid input. Please type 'y' for pass or 'n' for fail.")

        # 等待一小段时间后继续（可选）
        time.sleep(1)

    print("All inputs processed! Saving results to CSV...")

    # 保存结果到 CSV 文件
    output_file = "test_results.csv"
    with open(output_file, mode="w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["测试用例", "是否通过"])
        writer.writeheader()
        writer.writerows(results)

    print(f"Results saved to {output_file}")

except Exception as e:
    print("An error occurred:", e)

# 关闭浏览器
driver.quit()