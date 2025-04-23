import re
import time
from selenium.webdriver.chrome.webdriver import WebDriver
from automation.service.execute_task.request_config import RequestConfig
from automation.service.execute_task.task import CollectApi, SecKillApi
from collections import defaultdict


class Manage:
    __driver: WebDriver
    __config: RequestConfig
    cookies: dict

    handlers: dict

    def __init__(self, driver: WebDriver, config: RequestConfig):
        self.cookies = config.getCookie()
        self.__driver = driver
        self.__config = config

        self.handlers = {
            'collect': CollectApi(config),
            'secKillApi': SecKillApi(config),
        }
        collect: CollectApi = self.handlers.get('collect')
        time.sleep(10)
        taskList = collect.sent()
        data: dict = taskList.get('data')
        if data:
            filtered_task_list = [
                {"id": item["id"], 'title': item['title']} for item in data.get('items', [])
                if item['itemStatus'] == 0
            ]
        secKill: SecKillApi = self.handlers.get('secKillApi')
        if filtered_task_list:
            # 进行日期排序
            sorted_list = sorted(filtered_task_list, key=lambda x: x['title'])
            for s in sorted_list:
                s['date'] = self.search_date(s['title'])

            secKill.sent(self.group_to_2d_list(sorted_list, 'date')[0], driver=driver)


    # 进行日期分组
    @staticmethod
    def group_to_2d_list(data_list, key):
        grouped = defaultdict(list)
        for item in data_list:
            grouped[item[key]].append(item)
        return list(grouped.values())


    @staticmethod
    def search_date(s: str):
        return re.search(r'\d{4}年\d{1,2}月\d{1,2}日\d{1,2}点\d{1,2}分', s).group()
