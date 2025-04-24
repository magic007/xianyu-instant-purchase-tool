import pickle
import time
import os
import sys
from requests import Session
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


class AutoAddCommodity:
    # 加密参数
    class CustomMD5:
        @staticmethod
        def md5(a):
            def left_rotate(x, c):
                return (x << c | x >> (32 - c)) & 0xFFFFFFFF

            def add_unsigned(a, b):
                a &= 0xFFFFFFFF
                b &= 0xFFFFFFFF
                return (a + b) & 0xFFFFFFFF

            def F(x, y, z):
                return (x & y) | (~x & z)

            def G(x, y, z):
                return (x & z) | (y & ~z)

            def H(x, y, z):
                return x ^ y ^ z

            def I(x, y, z):
                return y ^ (x | ~z)

            def transform(func, a, b, c, d, x, s, ac):
                a = add_unsigned(a, add_unsigned(func(b, c, d), add_unsigned(x, ac)))
                a = left_rotate(a, s)
                return add_unsigned(a, b)

            def preprocess(input_string):
                input_bytes = bytearray(input_string, "utf-8")
                original_len_in_bits = len(input_bytes) * 8
                input_bytes.append(0x80)

                while len(input_bytes) % 64 != 56:
                    input_bytes.append(0)

                input_bytes += original_len_in_bits.to_bytes(8, byteorder="little")
                return input_bytes

            def to_hex(value):
                return "".join(["{:02x}".format((value >> (8 * i)) & 0xFF) for i in range(4)])

            def md5_core(input_bytes):
                A = 0x67452301
                B = 0xEFCDAB89
                C = 0x98BADCFE
                D = 0x10325476

                S = [
                    7, 12, 17, 22,
                    5, 9, 14, 20,
                    4, 11, 16, 23,
                    6, 10, 15, 21
                ]

                K = [
                    0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee,
                    0xf57c0faf, 0x4787c62a, 0xa8304613, 0xfd469501,
                    0x698098d8, 0x8b44f7af, 0xffff5bb1, 0x895cd7be,
                    0x6b901122, 0xfd987193, 0xa679438e, 0x49b40821,
                    0xf61e2562, 0xc040b340, 0x265e5a51, 0xe9b6c7aa,
                    0xd62f105d, 0x02441453, 0xd8a1e681, 0xe7d3fbc8,
                    0x21e1cde6, 0xc33707d6, 0xf4d50d87, 0x455a14ed,
                    0xa9e3e905, 0xfcefa3f8, 0x676f02d9, 0x8d2a4c8a,
                    0xfffa3942, 0x8771f681, 0x6d9d6122, 0xfde5380c,
                    0xa4beea44, 0x4bdecfa9, 0xf6bb4b60, 0xbebfbc70,
                    0x289b7ec6, 0xeaa127fa, 0xd4ef3085, 0x04881d05,
                    0xd9d4d039, 0xe6db99e5, 0x1fa27cf8, 0xc4ac5665,
                    0xf4292244, 0x432aff97, 0xab9423a7, 0xfc93a039,
                    0x655b59c3, 0x8f0ccc92, 0xffeff47d, 0x85845dd1,
                    0x6fa87e4f, 0xfe2ce6e0, 0xa3014314, 0x4e0811a1,
                    0xf7537e82, 0xbd3af235, 0x2ad7d2bb, 0xeb86d391
                ]

                blocks = [input_bytes[i:i + 64] for i in range(0, len(input_bytes), 64)]

                for block in blocks:
                    X = [int.from_bytes(block[i:i + 4], byteorder="little") for i in range(0, 64, 4)]

                    AA, BB, CC, DD = A, B, C, D

                    for i in range(64):
                        if 0 <= i <= 15:
                            A = transform(F, A, B, C, D, X[i], S[i % 4], K[i])
                        elif 16 <= i <= 31:
                            A = transform(G, A, B, C, D, X[(1 + 5 * i) % 16], S[4 + i % 4], K[i])
                        elif 32 <= i <= 47:
                            A = transform(H, A, B, C, D, X[(5 + 3 * i) % 16], S[8 + i % 4], K[i])
                        elif 48 <= i <= 63:
                            A = transform(I, A, B, C, D, X[(7 * i) % 16], S[12 + i % 4], K[i])

                        A, B, C, D = D, A, B, C

                    A = add_unsigned(A, AA)
                    B = add_unsigned(B, BB)
                    C = add_unsigned(C, CC)
                    D = add_unsigned(D, DD)

                return to_hex(A) + to_hex(B) + to_hex(C) + to_hex(D)

            input_bytes = preprocess(a)
            return md5_core(input_bytes)

    cookies: dict
    headers: dict = {
        "accept": "application/json",
        "accept-language": "zh-CN,zh;q=0.9",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://www.goofish.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://www.goofish.com/",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    }
    driver: WebDriver

    def __init__(self):
        chrome_options = Options()
        # 设置为浏览器持久化
        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # 添加更多选项以提高稳定性
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        # 使用本地ChromeDriver
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        driver_path = os.path.join(project_root, "drivers", "chromedriver")
        service = Service(executable_path=driver_path)
        
        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")  # 进一步隐藏
            driver.get("https://www.goofish.com")
            
            # 根据cookie判断是否是登录状态
            self.isLogin(driver)
            
            # 更健壮的元素检测
            try:
                # 尝试查找登录状态的用户名（这里可能需要根据实际页面元素调整）
                print("正在检查登录状态...")
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "一只九尾猫") or contains(@class, "user-name")]')))
                    print("已经登录")
                    self.initCookie(driver=driver)
                except (TimeoutException, NoSuchElementException):
                    # 尝试点击登录按钮
                    print("未检测到登录状态，尝试登录...")
                    login_btn = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, '//*[contains(text(), "登录") or contains(@class, "login")]')))
                    login_btn.click()
                    
                    # 等待登录框加载并切换
                    try:
                        WebDriverWait(driver, 15).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "alibaba-login-box")))
                        # 尝试点击快速进入按钮
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "快速进入")]'))).click()
                    except (TimeoutException, NoSuchElementException) as e:
                        print(f"登录界面元素未找到: {e}")
                        print("请手动完成登录过程...")
                        input("完成登录后按回车继续...")
                        
                    # 切回主框架
                    driver.switch_to.default_content()
                    self.initCookie(driver=driver)
                
                self.driver = driver
                
            except Exception as e:
                print(f"登录过程出错: {e}")
                input("请手动完成登录，操作完成后按回车继续...")
                driver.get("https://www.goofish.com")
                self.initCookie(driver=driver)
                self.driver = driver
                
        except WebDriverException as e:
            print(f"Chrome浏览器启动失败: {e}")
            print("可能原因:")
            print("1. ChromeDriver版本与Chrome浏览器版本不匹配")
            print("2. ChromeDriver没有正确的执行权限")
            print("请确保使用正确版本的ChromeDriver，并确保它有执行权限(chmod +x)")
            raise

    def isLogin(self, driver):
        try:
            self.load_cookies(driver=driver)
            cookies = self.initCookie(driver)
            if len(cookies) < 8:
                print("Cookie无效或已过期，需要重新登录")
                driver.get("https://www.goofish.com/login?spm=a21ybx.seo.sitemap.1")
                input("请登录后按回车\n")
                driver.get("https://www.goofish.com")
                # 重新加载登录后的Cookie
                self.initCookie(driver)
                self.cache_cookies(driver=driver)
                print("登录成功，Cookie已保存")
            else:
                print("Cookie有效，已成功登录")
        except Exception as e:
            print(f"登录过程发生错误: {e}")
            driver.get("https://www.goofish.com/login?spm=a21ybx.seo.sitemap.1")
            input("请登录后按回车\n")
            driver.get("https://www.goofish.com")
            self.initCookie(driver)
            self.cache_cookies(driver=driver)

    def cache_cookies(self, driver, file_path: str = None):
        if file_path is None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
            file_path = os.path.join(project_root, "automation", "cache", "cookies.pkl")
            
        # 确保缓存目录存在
        cache_dir = os.path.dirname(file_path)
        if not os.path.exists(cache_dir):
            print(f"创建缓存目录: {cache_dir}")
            os.makedirs(cache_dir, exist_ok=True)
            
        try:
            with open(file_path, 'wb') as file:
                pickle.dump(driver.get_cookies(), file)
            print(f"Cookie已保存到: {file_path}")
        except Exception as e:
            print(f"保存Cookie失败: {e}")

    def load_cookies(self, driver, file_path: str = None):
        if file_path is None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
            file_path = os.path.join(project_root, "automation", "cache", "cookies.pkl")
            
        if not os.path.exists(file_path):
            print(f"Cookie文件不存在: {file_path}")
            return
            
        try:
            with open(file_path, 'rb') as file:
                try:
                    cookies = pickle.load(file)
                except EOFError:
                    print("Cookie文件为空或已损坏")
                    return
                for cookie in cookies:
                    driver.add_cookie(cookie)
            driver.refresh()  # 刷新页面应用Cookies
        except Exception as e:
            print(f"加载Cookie失败: {e}")

    def initCookie(self, driver) -> dict:
        cookies = {}
        for cookie in driver.get_cookies():
            cookies[cookie['name']] = cookie['value']
        self.cookies = cookies
        # self.cache_cookies(driver=driver)
        return cookies

    def createRequestParams(self, params: dict, data: dict, timestamp: str = str(round(time.time() * 1000))) -> dict:
        params['sign'] = self.CustomMD5.md5(
            self.cookies['_m_h5_tk'].split('_')[0] + "&" + timestamp + "&" + params['appKey'] + "&" + data['data'])
        params['t'] = timestamp
        return params

    def get_search_list(self, searchName: str = "#卖闲置2025年3月29日", priceRange: str = '1,99',
                        isAttention: bool = False) -> list:
        session = Session()
        session.cookies.update(self.cookies)
        session.headers.update(self.headers)
        r: list = []
        initPageNum: int = 1

        # 是否开启值新增加入关注的人商品
        def is_presell(itemId: str) -> bool:
            data = {
                'data': '{"itemId":"' + itemId + '"}',
            }
            params = self.createRequestParams(params={
                'jsv': '2.7.2',
                'appKey': '34839810',
                't': '',
                'sign': '',
                'v': '7.0',
                'type': 'json',
                'accountSite': 'xianyu',
                'dataType': 'json',
                'timeout': '20000',
                'api': 'mtop.taobao.idle.trade.order.render',
                'valueType': 'string',
                'sessionOption': 'AutoLoginOnly',
                'spm_cnt': 'a21ybx.create-order.0.0',
                'spm_pre': 'a21ybx.item.buy.1.41c93da6MgCSxD',
                'log_id': '41c93da6MgCSxD',
            }, data=data)
            result = session.post('https://h5api.m.goofish.com/h5/mtop.taobao.idle.trade.order.render/7.0/',
                                  params=params, data=data).json()['data']
            if result['commonData'] and ('secKillStart' in result['commonData']):
                secKillStart: int = int(result['commonData']['secKillStart'])
                isScopeTime: bool = time.localtime(secKillStart / 1000).tm_yday == time.localtime().tm_yday
                return isScopeTime
            else:
                return False

        def nextPage(nextPageNum: int) -> bool:
            params = {
                'jsv': '2.7.2',
                'appKey': '34839810',
                't': '1743221664877',
                'sign': '64cb3d42f940c285c482be9a84538f9a',
                'v': '1.0',
                'type': 'originaljson',
                'accountSite': 'xianyu',
                'dataType': 'json',
                'timeout': '20000',
                'api': 'mtop.taobao.idlemtopsearch.pc.search',
                'sessionOption': 'AutoLoginOnly',
                'spm_cnt': 'a21ybx.search.0.0',
                'spm_pre': 'a21ybx.search.searchInput.0',
            }
            data = {
                'data': '{"pageNumber":' + str(
                    nextPageNum) + ',"keyword":"' + searchName + '","fromFilter":true,"rowsPerPage":30,"sortValue":"","sortField":"","customDistance":"","gps":"","propValueStr":{"searchFilter":"priceRange:' + priceRange + ';"},"customGps":"","searchReqFromPage":"pcSearch","extraFilterValue":"{}","userPositionJson":"{}"}',
            }
            params = self.createRequestParams(params=params, data=data)
            res = session.post("https://h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search/1.0/",
                               params=params,
                               data=data).json()['data']
            for item in res['resultList']:
                itemData = item['data']
                if itemData:
                    itemMain = itemData['item']['main']
                    if itemMain:
                        itemExContent = itemMain['exContent']
                        if isAttention:
                            if '你关注过的人' in str(itemExContent['fishTags']) and is_presell(itemExContent['itemId']):
                                self.add_attention_list(itemExContent['itemId'])
                                r.append(itemMain)
                        else:
                            if is_presell(itemExContent['itemId']):
                                self.add_attention_list(itemExContent['itemId'])
                                r.append(itemMain)
            return res['resultInfo']['hasNextPage']

        while nextPage(nextPageNum=initPageNum):
            initPageNum = initPageNum + 1

        return r
        # 判断商品是否是当天预售商品

    # 将商品加入收藏列表
    def add_attention_list(self, itemId: str):
        session = Session()
        session.cookies.update(self.cookies)
        session.headers.update(self.headers)
        params = {
            'jsv': '2.7.2',
            'appKey': '34839810',
            't': '',
            'sign': '',
            'v': '1.0',
            'type': 'originaljson',
            'accountSite': 'xianyu',
            'dataType': 'json',
            'timeout': '20000',
            'needLoginPC': 'true',
            'api': 'mtop.taobao.idle.collect.item',
            'sessionOption': 'AutoLoginOnly',
            'spm_cnt': 'a21ybx.item.0.0',
            'spm_pre': 'a21ybx.search.searchFeedList.3.59ed3dc7BjQvEO',
            'log_id': '59ed3dc7BjQvEO',
        }

        data = {
            'data': '{"itemId":"' + itemId + '"}',
        }
        self.createRequestParams(params=params, data=data)
        response = session.post(
            'https://h5api.m.goofish.com/h5/mtop.taobao.idle.collect.item/1.0/',
            params=params,
            data=data,
        )
        if response.status_code == 200:
            print(response.json())
            print(f'商品编号：{itemId}加入收藏列表成功！')

    def send_post(self, params, data, url):
        session = Session()
        session.cookies.update(self.cookies)
        session.headers.update(self.headers)
        return session.post(
            url,
            params=self.createRequestParams(params=params, data=data),
            data=data,
        )

    def delete_attention_list(self):
        def delete(itemId: str):
            r = self.send_post(params={
                'jsv': '2.7.2',
                'appKey': '34839810',
                't': '',
                'sign': '',
                'v': '1.0',
                'type': 'originaljson',
                'accountSite': 'xianyu',
                'dataType': 'json',
                'timeout': '20000',
                'needLoginPC': 'true',
                'api': 'com.taobao.idle.unfavor.item',
                'sessionOption': 'AutoLoginOnly',
                'spm_cnt': 'a21ybx.item.0.0',
                'spm_pre': 'a21ybx.collection.feeds.1.44545141ydzfTY',
                'log_id': '44545141ydzfTY',
            }, data={'data': '{"itemId":"' + itemId + '"}'},
                url='https://h5api.m.goofish.com/h5/com.taobao.idle.unfavor.item/1.0/')
            if r.status_code == 200:
                print(f'成功将商品id为{itemId},移除收藏')

        data = self.send_post(params={
            'jsv': '2.7.2',
            'appKey': '34839810',
            't': '',
            'sign': '',
            'v': '1.0',
            'type': 'originaljson',
            'accountSite': 'xianyu',
            'dataType': 'json',
            'timeout': '20000',
            'api': 'mtop.taobao.idle.web.favor.item.list',
            'sessionOption': 'AutoLoginOnly',
            'spm_cnt': 'a21ybx.collection.0.0',
            'spm_pre': 'a21ybx.personal.menu.4.4f6d6ac2FOzYeI',
            'log_id': '4f6d6ac2FOzYeI',
        }, data={
            'data': '{"pageNumber":1,"rowsPerPage":99,"type":"DEFAULT"}',
        }, url='https://h5api.m.goofish.com/h5/mtop.taobao.idle.web.favor.item.list/1.0/').json()['data']
        if 'items' in data:
            for item in data['items']:
                delete(item['id'])


if __name__ == "__main__":
    print('---脚本开始运行---')
    startTime = time.time()
    try:
        auto = AutoAddCommodity()
        option = input(
            '请选择操作:\n1.清空收藏\n2.搜寻今日秒拍商品并加入收藏\n3.搜寻商品，但只加入关注的up商品\n4.根据名称搜索\n输入错误时不做任何操作退出\n')
        if option == '1':
            auto.delete_attention_list()
        elif option == '2':
            searchName = '#卖闲置' + str(
                str(f"{time.strftime('%Y')}年{time.strftime('%m').lstrip('0')}月{time.strftime('%d').lstrip('0')}日"))
            print(f'默认搜索商品名称：{searchName}')
            print(f' 共新增商品：{len(auto.get_search_list(searchName=searchName, isAttention=False))} 条')
        elif option == '3':
            searchName = '#卖闲置' + str(
                str(f"{time.strftime('%Y')}年{time.strftime('%m').lstrip('0')}月{time.strftime('%d').lstrip('0')}日"))
            print(f'默认搜索商品名称：{searchName}')
            print(f' 共新增商品：{len(auto.get_search_list(searchName=searchName, isAttention=True))} 条')
        elif option == '4':
            searchName = str(input('输入要搜寻的商品名称\n'))
            print(f' 共新增商品：{len(auto.get_search_list(searchName=searchName, isAttention=False))} 条')
        endTime = time.time()
        print(f'---脚本运行结束运行  耗时{(endTime - startTime)} 秒---')
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"脚本运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print('---脚本执行结束---')
