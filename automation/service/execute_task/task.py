import json
import time
import os
from abc import abstractmethod, ABC
from asyncio import Future
from concurrent.futures import ThreadPoolExecutor

from selenium.webdriver.chrome.webdriver import WebDriver
from requests import Session
from automation.service.execute_task.request_config import RequestConfig
from automation.utool.sokcet_connect import Ipv6Connect


class XyTask:

    def __init__(self, max_workers=15):
        """
        初始化线程池
        :param max_workers: 最大并发线程数
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.futures = []  # 用于存储任务的 Future 对象

    def submit_task(self, func, data, secKillStart, title: str) -> Future:
        """
        提交任务到线程池
        :param func: 任务函数
        :param args: 任务函数的位置参数
        :param kwargs: 任务函数的关键字参数
        :return: Future 对象（可用于获取任务执行结果）
        """
        future = self.executor.submit(func, data, secKillStart, title)
        # self.futures.append(future)
        return future

    def get_results(self, wait=True):
        """
        获取所有任务的执行结果
        :param wait: 是否等待所有任务完成
        :return: 任务执行结果的列表
        """
        results = []
        for future in self.futures:
            if wait:
                results.append(future.result())  # 阻塞等待结果
            elif future.done():
                results.append(future.result())  # 仅获取已完成的任务
        return results

    def shutdown(self):
        """ 关闭线程池，释放资源 """
        self.executor.shutdown(wait=True)


# 定义接口规范
class XyApi(ABC):  # 定义接口（抽象基类）
    __appKey: str = '34839810'
    session: Session
    headers: dict
    rConfig: RequestConfig
    task: XyTask = XyTask()
    
    # 获取配置文件的绝对路径
    @staticmethod
    def get_config_path():
        # 获取当前工作目录（项目根目录）
        root_dir = os.getcwd()
        config_path = os.path.join(root_dir, "automation", "config", "config.json")
        print(f"配置文件路径: {config_path}")
        return config_path

    @abstractmethod
    def config(self):
        pass

    def __init__(self, rConfig: RequestConfig):
        config_path = self.get_config_path()
        print(f"尝试读取配置文件：{config_path}")
        with open(config_path, "r", encoding="utf-8") as file:
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
        config_path = self.get_config_path()
        with open(config_path, "r", encoding="utf-8") as file:
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
                    if r_commonData.get('secKillStart'):
                        secKillStart: int = int(r_commonData.get('secKillStart'))
                        r_params_data: dict = r_commonData.get('itemBuyInfo')[0]
                        if secKillStart - (time.time_ns() // 1_000_000) > (3600000 // 2):
                            print(
                                f'商品{e}  还有{(secKillStart - (time.time_ns() // 1_000_000)) / (1000 * 60 * 60)}小时后 ...\n')
                            continue
                        self.task.submit_task(func=self.startTask, data=r_params_data, secKillStart=secKillStart,
                                              title=e.get('title'))

    def startTask(self, data: dict, secKillStart: int, title: str):
        id = data.get('itemId')
        latency_time = 15
        ipv6 = Ipv6Connect()
        data = {"data": json.dumps({"params": [data]})}
        cookies = self.rConfig.cookies
        params = self.apiConfig['params']
        api = '/h5/mtop.taobao.idle.trade.order.create/5.0/'
        while True:
            # 当前秒级时间戳
            await_time = secKillStart - (time.time_ns() // 1_000_000)
            # 是否在开始范围内
            start_scope = (await_time / 1000 <= latency_time and await_time > 0)
            # 是否在结束范围内
            end_scope = (await_time < 0 and await_time / 1000 >= -latency_time)
            # 抢购但是不读取返回值，值发送请求
            if start_scope or end_scope:
                start_time = time.perf_counter()
                ipv6.sent_seckill_request(api=api, cookies=cookies, params=params, data=data)
                end_time = time.perf_counter()
                print(f'商品title：{title}-{id}-请求耗时：{start_time - end_time}秒')
            elif (await_time < 0 and await_time / 1000 < -latency_time):
                print("抢购结束")
                break


class CollectApi(XyApi):
    apiConfig: dict

    def __init__(self, rConfig: RequestConfig):
        super().__init__(rConfig)
        config_path = self.get_config_path()
        with open(config_path, "r", encoding="utf-8") as file:
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
        print("请求参数:", self.apiConfig['api'], params, data)
        return self.session.post(self.apiConfig['api'],
                                 params=self.rConfig.createRequestParams(params=params, data=data), data=data).json()
