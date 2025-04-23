import json
import time
from abc import abstractmethod, ABC
from selenium.webdriver.chrome.webdriver import WebDriver
from automation.port.task import XyTask
from requests import Session
from automation.request_config import RequestConfig


# 定义接口规范
class XyApi(ABC):  # 定义接口（抽象基类）
    __appKey: str = '34839810'
    session: Session
    headers: dict
    rConfig: RequestConfig
    task: XyTask = XyTask()

    @abstractmethod
    def config(self):
        pass

    def __init__(self, rConfig: RequestConfig):
        with open("./config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
        self.headers = config['headers']
        self.headers['sec-ch-ua'] = '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"'
        self.rConfig = rConfig

    @abstractmethod
    def sent(self):
        pass


class SecKillApi(XyApi):
    apiConfig: dict

    def __init__(self, rConfig: RequestConfig):
        super().__init__(rConfig)
        with open("./config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
        self.apiConfig = config['apiConfig']['secKillConfig']
        self.session = Session()
        self.session.headers.update(self.headers)
        self.session.cookies.update(self.rConfig.cookies)

    def config(self) -> dict:
        return self.apiConfig

    def sent(self, taskList: list, driver: WebDriver):
        driver.get(f'https://www.goofish.com/create-order?itemId=' + taskList[0]['id'])
        x5sec = input("请点击购买后通过滑块验证，获取并且输入x5sec后回车\n")
        self.rConfig.initCookie(driver)
        self.rConfig.cookies['x5sec'] = x5sec
        self.session.cookies.update(self.rConfig.cookies)
        for e in taskList:
            params = {
                'jsv': '2.7.2',
                'appKey': '34839810',
                # 't': '1742102765011',
                # 'sign': '9e2684644d10fc3b609cd6af0da7e436',
                'v': '7.0',
                'type': 'json',
                'accountSite': 'xianyu',
                'dataType': 'json',
                'timeout': '20000',
                'api': 'mtop.taobao.idle.trade.order.render',
                'valueType': 'string',
                'sessionOption': 'AutoLoginOnly',
                'spm_cnt': 'a21ybx.create-order.0.0',
                'spm_pre': 'a21ybx.item.buy.1.115d3da6TWicmz',
                'log_id': '115d3da6TWicmz',
            }

            data = {
                'data': '{"itemId":"' + e.get('id') + '"}',
            }
            # 生成sign和时间戳
            params = self.rConfig.createRequestParams(params=params, data=data)
            response = self.session.post(
                'https://h5api.m.goofish.com/h5/mtop.taobao.idle.trade.order.render/7.0/',
                params=params,
                cookies=self.rConfig.cookies,
                headers=self.rConfig.headers,
                data=data,
            )
            if response.json().get('data'):
                r_data: dict = response.json().get('data')
                if r_data.get('commonData'):
                    r_commonData: dict = r_data.get('commonData')
                    secKillStart: int = int(r_commonData.get('secKillStart'))
                    r_params_data: dict = r_commonData.get('itemBuyInfo')[0]
                    if secKillStart - (time.time_ns() // 1_000_000) > (3600000 // 2):
                        print(
                            f'商品{e}  还有{(secKillStart - (time.time_ns() // 1_000_000)) / (1000 * 60 * 60)}小时后 ...\n')
                        continue

                    self.task.submit_task(func=self.startTask, data=r_params_data, secKillStart=secKillStart,title=e.get('title'))

    def startTask(self, data: dict, secKillStart: int,title:str):
        id = data.get('itemId')
        latency_time = 30
        session = Session()
        session.headers.update(self.headers)
        session.cookies.update(self.rConfig.cookies)
        data = {"data": json.dumps({"params": [data]})}

        while True:
            # 当前秒级时间戳
            await_time = secKillStart -(time.time_ns() // 1_000_000)
            # 是否在开始范围内
            start_scope = (await_time / 1000 <= latency_time and await_time > 0)
            # 是否在结束范围内
            end_scope = (await_time < 0 and await_time / 1000 >= -latency_time)

            if start_scope or end_scope:
            # if True:
                start_time  =time.time()
                params = self.rConfig.createRequestParams(params=self.apiConfig['params'], data=data)
                result =session.post(self.apiConfig.get('api'), params=params, data=data).json()
                end_time  =time.time()
                print(f'商品title：{title}-{id}-请求耗时：{start_time - end_time}秒-{result}')
            elif ((await_time / 1000) > (latency_time * 1.5)):
                print(f'{title}-{id}  休眠{latency_time}秒后 重新进入抢购...\n')
                time.sleep(latency_time)
            # elif ((await_time/1000) > (latency_time -10)):
            #     # 需要等待多少秒
            #     latency_time = (await_time /1000) -latency_time
            #     print(f'{title}-{id}还需等待{latency_time //60}分钟后 抢购中....\n')
            #     time.sleep(latency_time)
            elif (await_time < 0 and await_time / 1000 < -latency_time):
                print("抢购结束")
                break
class CollectApi(XyApi):
    apiConfig: dict

    def __init__(self, rConfig: RequestConfig):
        super().__init__(rConfig)
        with open("./config.json", "r", encoding="utf-8") as file:
            configApi = json.load(file)
        self.apiConfig = configApi['apiConfig']['collectConfig']
        self.session = Session()
        self.session.headers.update(self.headers)
        self.session.cookies.update(self.rConfig.cookies)

    def config(self) -> dict:
        return self.apiConfig

    def sent(self) -> dict:
        params: dict = self.apiConfig['params']
        data: dict = {
            "data": json.dumps(self.apiConfig['data'])
        }
        return self.session.post(self.apiConfig['api'],
                                 params=self.rConfig.createRequestParams(params=params, data=data), data=data).json()
