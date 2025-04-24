import re
import time
import traceback
from selenium.webdriver.chrome.webdriver import WebDriver
from automation.service.execute_task.request_config import RequestConfig
from automation.service.execute_task.task import CollectApi, SecKillApi
from collections import defaultdict


class Manage:
    __driver: WebDriver  # 私有变量，存储WebDriver实例
    __config: RequestConfig  # 私有变量，存储RequestConfig实例
    cookies: dict  # 字典，存储cookies

    handlers: dict  # 字典，存储任务处理器

    def __init__(self, driver: WebDriver, config: RequestConfig):
        try:
            print("初始化管理器...")
            self.cookies = config.getCookie()  # 获取cookies
            self.__driver = driver  # 初始化WebDriver
            self.__config = config  # 初始化RequestConfig

            self.handlers = {
                'collect': CollectApi(config),  # 初始化CollectApi处理器
                'secKillApi': SecKillApi(config),  # 初始化SecKillApi处理器
            }
            
            # 获取收藏列表
            try:
                print("正在获取收藏商品列表...")
                collect: CollectApi = self.handlers.get('collect')  # 获取CollectApi处理器
                time.sleep(10)  # 等待10秒，确保页面加载完成
                taskList = collect.sent()  # 发送请求，获取任务列表
                
                print(f"API返回数据: {taskList}")
                
                data: dict = taskList.get('data')  # 获取数据
                
                if not data:
                    print("警告: 未能获取到商品数据，请检查接口返回")
                    return
                    
                items = data.get('items', [])
                if not items:
                    print("警告: 未找到收藏的商品，请确保您已收藏了想要秒杀的商品")
                    return
                
                print(f"找到 {len(items)} 个收藏商品")
                
                # 过滤商品
                filtered_task_list = []
                for item in items:
                    if item.get('itemStatus') == 0:
                        print(f"添加商品: {item.get('title', '未知标题')} (ID: {item.get('id', '未知ID')})")
                        filtered_task_list.append({
                            "id": item.get('id', ''),
                            'title': item.get('title', '')
                        })
                
                if not filtered_task_list:
                    print("警告: 没有符合条件的商品")
                    return
                
                print(f"过滤后剩余 {len(filtered_task_list)} 个商品")
                
                # 执行秒杀任务
                secKill: SecKillApi = self.handlers.get('secKillApi')  # 获取SecKillApi处理器
                
                if filtered_task_list:
                    try:
                        # 进行日期排序
                        print("按日期对商品进行排序...")
                        sorted_list = sorted(filtered_task_list, key=lambda x: x['title'])
                        
                        # 为每个任务添加日期
                        for s in sorted_list:
                            try:
                                s['date'] = self.search_date(s['title'])  # 为每个任务添加日期
                                print(f"商品 '{s['title']}' 的日期为: {s['date']}")
                            except Exception as e:
                                print(f"警告: 处理商品日期时出错: {e}")
                                # 使用默认日期
                                import datetime
                                now = datetime.datetime.now()
                                s['date'] = f"{now.year}年{now.month}月{now.day}日{now.hour}点{now.minute}分"
                                print(f"使用默认日期: {s['date']}")
                        
                        # 按日期分组
                        grouped_list = self.group_to_2d_list(sorted_list, 'date')
                        if not grouped_list:
                            print("警告: 分组后没有商品")
                            return
                            
                        print(f"商品已按日期分为 {len(grouped_list)} 组")
                        
                        # 发送秒杀任务
                        print(f"发送第一组商品进行秒杀，共 {len(grouped_list[0])} 个商品")
                        secKill.sent(grouped_list[0], driver=driver)  # 发送秒杀任务
                        
                    except Exception as e:
                        print(f"秒杀过程中出错: {e}")
                        traceback.print_exc()
                else:
                    print("没有找到需要秒杀的商品")
                    
            except Exception as e:
                print(f"获取收藏商品列表失败: {e}")
                traceback.print_exc()
                
        except Exception as e:
            print(f"管理器初始化失败: {e}")
            traceback.print_exc()

    # 进行日期分组
    @staticmethod
    def group_to_2d_list(data_list, key):
        try:
            if not data_list:
                print("警告: 要分组的数据列表为空")
                return []
                
            grouped = defaultdict(list)  # 使用defaultdict进行分组
            for item in data_list:
                if key not in item:
                    print(f"警告: 项目中没有找到 '{key}' 键: {item}")
                    continue
                grouped[item[key]].append(item)  # 根据指定的key进行分组
                
            result = list(grouped.values())  # 返回分组后的列表
            print(f"分组结果: {len(result)} 组")
            return result
        except Exception as e:
            print(f"分组时出错: {e}")
            traceback.print_exc()
            return [data_list]  # 出错时返回原始列表作为单一分组

    @staticmethod
    def search_date(s: str):
        # 使用正则表达式搜索日期
        match = re.search(r'\d{4}年\d{1,2}月\d{1,2}日\d{1,2}点\d{1,2}分', s)
        if match:
            return match.group()
        else:
            # 如果没有匹配到日期格式，返回一个默认值或替代方案
            print(f"警告: 无法在商品名称中找到日期格式: {s}")
            # 使用当前时间作为默认值
            import datetime
            now = datetime.datetime.now()
            return f"{now.year}年{now.month}月{now.day}日{now.hour}点{now.minute}分"
