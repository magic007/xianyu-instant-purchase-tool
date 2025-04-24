from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import os
import sys
import time
from automation.service.execute_task.manage import Manage
from automation.service.execute_task.request_config import RequestConfig

# 配置项 - 修改这里以适应您的环境
USE_LOCAL_DRIVER = True  # 是否使用本地ChromeDriver
LOCAL_DRIVER_PATH = os.path.join(os.getcwd(), "drivers", "chromedriver")  # 本地ChromeDriver路径

chrome_options = Options()
# 设置为浏览器持久化
chrome_options.add_experimental_option("detach", True)
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
# 添加更多稳定性选项
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-infobars")

# 初始化Chrome浏览器
try:
    if USE_LOCAL_DRIVER:
        # 检查本地驱动是否存在
        if not os.path.exists(LOCAL_DRIVER_PATH):
            print(f"错误: 未找到本地ChromeDriver: {LOCAL_DRIVER_PATH}")
            print("请下载适合您Chrome版本的驱动并放在drivers目录下")
            print("下载地址: https://googlechromelabs.github.io/chrome-for-testing/")
            sys.exit(1)
        service = Service(executable_path=LOCAL_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        # 使用自动下载驱动功能
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")  # 进一步隐藏
    driver.implicitly_wait(10)  # 添加隐式等待
    wait = WebDriverWait(driver, 15)  # 增加等待时间
    request_config = RequestConfig()
    
    try:
        driver.get("https://www.goofish.com")
        print("正在打开闲鱼网站...")
        time.sleep(3)  # 给页面加载一些时间
        
        # 根据请cookie判断是否是登录状态
        try:
            request_config.isLogin(driver)
            print("正在检查登录状态...")
            
            # 检查登录状态的更健壮方式
            try:
                # 这里使用更通用的定位方式，避免特定用户名的依赖
                login_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "header") or contains(@class, "top")]//div[contains(@class, "login") or contains(@class, "user") or contains(@class, "avatar")]'))
                )
                print("检测到用户元素：", login_element.text)
                request_config.initCookie(driver=driver)
                print("成功获取Cookie")
            except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
                print(f"未检测到登录元素，可能需要登录: {e}")
                try:
                    # 尝试点击登录按钮
                    login_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '//div[contains(text(), "登录") or contains(@class, "login")]'))
                    )
                    login_button.click()
                    print("正在打开登录界面...")
                    
                    # 等待登录框出现
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.frame_to_be_available_and_switch_to_it((By.ID, "alibaba-login-box"))
                        )
                        print("已切换到登录框")
                        
                        # 尝试点击快速登录按钮
                        try:
                            quick_login = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "快速进入")]'))
                            )
                            quick_login.click()
                            print("点击了快速登录按钮")
                        except:
                            print("未找到快速登录按钮，请手动登录")
                            pass
                            
                    except:
                        print("未能切换到登录框，可能界面已变化")
                        pass
                        
                    # 等待用户手动登录
                    input("请在浏览器中完成登录后按回车继续...\n")
                    driver.get("https://www.goofish.com")  # 重新加载页面
                    time.sleep(2)
                    request_config.initCookie(driver=driver)
                    
                except Exception as e:
                    print(f"尝试登录过程中出错: {e}")
                    input("请手动登录后按回车继续...\n")
                    driver.get("https://www.goofish.com")
                    time.sleep(2)
                    request_config.initCookie(driver=driver)
        except Exception as e:
            print(f"登录过程中出现错误: {e}")
            input("请手动完成登录后按回车继续...\n")
            driver.get("https://www.goofish.com")
            time.sleep(2)
            request_config.initCookie(driver=driver)
        
        print("准备执行主任务...")
        time.sleep(2)  # 给一点时间确保页面稳定
        
        # 包装主任务执行部分
        try:
            print("开始执行主任务...")
            Manage(driver=driver, config=request_config)
            print("主任务执行完成")
        except Exception as e:
            print(f"主任务执行失败: {e}")
            
    except Exception as e:
        print(f"运行过程中出现错误: {e}")
        
except Exception as e:
    print(f"启动失败: {e}")
    sys.exit(1)
finally:
    try:
        print("程序即将结束...")
        # 如果不需要保持浏览器，取消以下注释
        # driver.quit()
    except:
        pass