import json
import time
import pickle
import execjs


class RequestConfig:
    headers: dict
    cookies: dict

    def __init__(self):
        with open("./config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
        self.headers = config['headers']
        self.headers['sec-ch-ua'] = '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"'

    def initCookie(self, driver) -> dict:
        cookies = {}
        for cookie in driver.get_cookies():
            cookies[cookie['name']] = cookie['value']
        self.cookies = cookies
        # self.cache_cookies(driver=driver)
        return cookies

    @staticmethod
    def createTimestamp() -> str:
        return str(round(time.time() * 1000))

    def createRequestParams(self, params: dict, data: dict, timestamp: str = str(round(time.time() * 1000))) -> dict:
        params['sign'] = self.createSign(
            self.cookies['_m_h5_tk'].split('_')[0] + "&" + timestamp + "&" + params['appKey'] + "&" + data['data'])
        params['t'] = timestamp
        return params

    def isLogin(self, driver):
        self.load_cookies(driver=driver)
        if len(self.initCookie(driver)) < 1:
            driver.get("https://www.goofish.com/login?spm=a21ybx.seo.sitemap.1")
            input("请登录后按回车\n")
            driver.get("https://www.goofish.com")
            self.isLogin(driver)
        else:
            print("登录成功了！")
            self.cache_cookies(driver=driver)

    # 缓存cookies避免下次程序重启需要重新登录
    def cache_cookies(self, driver, file_path: str = './cache/cookies.pkl'):
        with open(file_path, 'wb') as file:
            pickle.dump(driver.get_cookies(), file)

    def load_cookies(self, driver, file_path: str = './cache/cookies.pkl'):
        with open(file_path, 'rb') as file:
            try:
                cookies = pickle.load(file)
            except EOFError:
                return
            for cookie in cookies:
                driver.add_cookie(cookie)
        driver.refresh()  # 刷新页面应用Cookies
    # 创建签名
    @staticmethod
    def createSign(data: str) -> str:
        with open(file="./js/xianyu.js", encoding="utf-8") as fp:
            js_code = fp.read()
            ctx = execjs.compile(js_code)
        return ctx.call("i", data)

    # 获取格式化后的cookes
    def getCookie(self) -> dict:
        return self.cookies

    # 获取请求头
    def getHeaders(self) -> dict:
        return self.headers
