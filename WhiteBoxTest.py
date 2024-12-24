from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# 替换为你的本地 HTML 文件路径（确保路径正确）
file_path = "file:///C:/classes/software_test/软件质量/intellimap/gaodemap.html"

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
    input_values = ["测试输入1", "测试输入2", "测试输入3", "测试输入4"]

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
