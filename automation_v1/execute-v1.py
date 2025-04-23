from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from automation_v1.port.manage import Manage
from automation_v1.request_config import RequestConfig
from webdriver_manager.chrome import ChromeDriverManager

chrome_options = Options()
# 设置用户数据目录
# chrome_options.add_argument(r'--user-data-dir=C:\Users\Tzk\AppData\Local\Google\Chrome\User Data')
# 设置缓存目录
# chrome_options.add_argument(r'--disk-cache-dir=C:\Users\Tzk\AppData\Local\Google\Chrome\User Data')
# 设置为浏览器持久化
chrome_options.add_experimental_option("detach", True)
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)
chrome_options.add_argument("--disable-blink-features=AutomationControlled")


with webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options) as driver:
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")  # 进一步隐藏
    wait =WebDriverWait(driver, 10)
    request_config = RequestConfig()
    driver.get("https://www.goofish.com")
    # 根据请cookie判断是否是登录状态
    request_config.isLogin(driver)
    # 等待 <i> 标签出现（最多等待 10 秒）
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "一只九尾猫")]')))
        print("已经登录")
        request_config.initCookie(driver=driver)
    except:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "登录")]'))).click()
        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "alibaba-login-box")))
        driver.find_element(By.XPATH, '//button[contains(text(), "快速进入")]').click()
        request_config.initCookie(driver=driver)

    print("可以开始操作了")
    Manage(driver=driver,config=request_config)
