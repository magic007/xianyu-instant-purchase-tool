import json
import time
import pickle


# import execjs


class RequestConfig:
    headers: dict
    cookies: dict

    def __init__(self):
        with open("./../../config/config.json", "r", encoding="utf-8") as file:
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

    # def createRequestParams(self, params: dict, data: dict, timestamp: str = str(round(time.time() * 1000))) -> dict:
    #     params['sign'] = self.createSign(
    #         self.cookies['_m_h5_tk'].split('_')[0] + "&" + timestamp + "&" + params['appKey'] + "&" + data['data'])
    #     params['t'] = timestamp
    #     return params

    def createRequestParams(self, params: dict, data: dict,
                            timestamp: str = str(round(time.time() * 1000) )) -> dict:
        params['sign'] = self.CustomMD5.md5(
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
    def cache_cookies(self, driver, file_path: str = './../../cache/cookies.pkl'):
        with open(file_path, 'wb') as file:
            pickle.dump(driver.get_cookies(), file)

    def load_cookies(self, driver, file_path: str = './../../cache/cookies.pkl'):
        with open(file_path, 'rb') as file:
            try:
                cookies = pickle.load(file)
            except EOFError:
                return
            for cookie in cookies:
                driver.add_cookie(cookie)
        driver.refresh()  # 刷新页面应用Cookies

    # 创建签名
    # @staticmethod
    # def createSign(data: str) -> str:
    #     with open(file="./js/xianyu.js", encoding="utf-8") as fp:
    #         js_code = fp.read()
    #         ctx = execjs.compile(js_code)
    #     return ctx.call("i", data)

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

    # 获取格式化后的cookes
    def getCookie(self) -> dict:
        return self.cookies

    # 获取请求头
    def getHeaders(self) -> dict:
        return self.headers
