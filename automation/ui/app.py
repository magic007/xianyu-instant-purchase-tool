import sys
import os
import json
import re
import time
from datetime import datetime, timedelta

# 添加项目根目录到路径，以便导入其他模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from flask import Flask, render_template, request, jsonify
from automation.service.auto_add_commodity.AutoAddCommodity import AutoAddCommodity
from requests import Session

# 确保静态文件和模板路径正确
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))

app = Flask(__name__, 
            template_folder=template_dir,
            static_folder=static_dir,
            static_url_path='/static')

auto_add_commodity = None

# 允许跨域访问的设置
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    """测试路由，用于确认应用正常运行"""
    app_info = {
        'app_name': '闲鱼秒拍搜索工具',
        'static_folder': static_dir,
        'template_folder': template_dir,
        'routes': [str(rule) for rule in app.url_map.iter_rules()],
        'static_files': os.listdir(static_dir) if os.path.exists(static_dir) else [],
        'template_files': os.listdir(template_dir) if os.path.exists(template_dir) else []
    }
    return jsonify(app_info)

@app.route('/test-page')
def test_page():
    """测试HTML页面，用于测试静态文件加载"""
    return render_template('test.html')

@app.route('/search', methods=['POST'])
def search():
    global auto_add_commodity
    
    try:
        # 如果还没有初始化，则创建实例
        if auto_add_commodity is None:
            auto_add_commodity = AutoAddCommodity()
        
        # 获取搜索参数
        search_name = request.form.get('search_name', '#卖闲置2025年3月29日')
        min_price = request.form.get('min_price', '1')
        max_price = request.form.get('max_price', '99')
        is_attention = request.form.get('is_attention', 'false').lower() == 'true'
        
        # 创建价格范围
        price_range = f'{min_price},{max_price}'
        
        # 调用搜索方法
        result = auto_add_commodity.get_search_list(
            searchName=search_name,
            priceRange=price_range,
            isAttention=is_attention
        )
        
        # 打印第一个结果的结构用于调试
        if result and len(result) > 0:
            print("传统搜索 - 第一个结果的结构详细情况:")
            print(json.dumps(result[0], indent=2, ensure_ascii=False)[:1000] + "...")
        
        # 处理结果数据，提取需要在前端显示的信息
        items = []
        for item in result:
            try:
                # 提取商品标题 - 直接从主数据中获取
                title = item.get("title", "")
                if not title or not title.strip():
                    # 尝试从exContent中获取
                    ex_content = item.get("exContent", {})
                    title = ex_content.get("title", "未知商品")
                
                # 提取商品价格
                price_text = ""
                # 尝试从clickParam中获取价格
                if "clickParam" in item and isinstance(item["clickParam"], dict) and "args" in item["clickParam"]:
                    click_args = item["clickParam"]["args"]
                    if "price" in click_args:
                        price_text = click_args["price"]
                
                # 如果clickParam中没有价格，尝试其他方法获取
                if not price_text:
                    if "price" in item and isinstance(item["price"], list):
                        # 遍历价格列表，找到整数部分
                        for price_part in item["price"]:
                            if price_part.get("type") == "integer":
                                price_text = price_part.get("text", "")
                                break
                    else:
                        # 尝试从detailParams中获取价格
                        detail_params = item.get("detailParams", {})
                        if "soldPrice" in detail_params:
                            price_text = detail_params["soldPrice"]
                        elif "price" in item and isinstance(item["price"], dict):
                            price_text = item["price"].get("priceDesc", "")
                        
                    # 如果还是没有价格，尝试从exContent获取
                    if not price_text:
                        ex_content = item.get("exContent", {})
                        price_text = ex_content.get("priceText", "")
                
                # 添加货币符号
                if price_text and not price_text.startswith("¥"):
                    price_text = f"¥{price_text}"
                elif not price_text:
                    price_text = "未知价格"
                
                # 提取图片URL
                image_url = ""
                
                # 尝试从picUrl直接获取
                image_url = item.get("picUrl", "")
                
                # 如果没有picUrl，尝试从exContent.pic获取
                if not image_url or not image_url.strip():
                    ex_content = item.get("exContent", {})
                    image_url = ex_content.get("pic", "")
                
                # 如果没有exContent.pic，尝试从图片列表获取第一张
                if not image_url or not image_url.strip():
                    images = item.get("images", [])
                    if images and len(images) > 0:
                        image_url = images[0]
                
                # 如果从clickParam中提取
                if not image_url or not image_url.strip():
                    if "clickParam" in item and isinstance(item["clickParam"], dict) and "args" in item["clickParam"]:
                        click_args = item["clickParam"]["args"]
                        if "pic" in click_args:
                            image_url = click_args["pic"]
                
                # 确保图片URL是完整的
                if image_url and not image_url.startswith(('http://', 'https://')):
                    image_url = f"https:{image_url}" if image_url.startswith('//') else f"https://{image_url}"
                
                # 提取地区信息
                location = ""
                
                # 尝试从clickParam中获取地区
                if "clickParam" in item and isinstance(item["clickParam"], dict) and "args" in item["clickParam"]:
                    click_args = item["clickParam"]["args"]
                    if "location" in click_args:
                        location = click_args["location"]
                
                # 如果clickParam中没有地区，尝试从area获取
                if not location or not location.strip():
                    location = item.get("area", "")
                
                # 如果area中没有地区，尝试从exContent获取
                if not location or not location.strip():
                    ex_content = item.get("exContent", {})
                    location = ex_content.get("provCity", "")
                
                # 提取商品ID
                item_id = item.get("itemId", "")
                if not item_id:
                    # 尝试从detailParams中获取
                    detail_params = item.get("detailParams", {})
                    item_id = detail_params.get("itemId", "")
                
                # 如果还没有商品ID，尝试从exContent中获取
                if not item_id:
                    ex_content = item.get("exContent", {})
                    item_id = ex_content.get("itemId", "")
                
                # 如果还没有商品ID，尝试从clickParam中获取
                if not item_id and "clickParam" in item and isinstance(item["clickParam"], dict) and "args" in item["clickParam"]:
                    click_args = item["clickParam"]["args"]
                    if "id" in click_args:
                        item_id = click_args["id"]
                
                # 提取用户昵称
                user_nick = ""
                # 尝试从userNickName获取
                user_nick = item.get("userNickName", "")
                
                # 如果没有userNickName，尝试从detailParams中获取
                if not user_nick:
                    detail_params = item.get("detailParams", {})
                    user_nick = detail_params.get("userNick", "")
                
                # 如果没有detailParams.userNick，尝试从exContent中获取
                if not user_nick:
                    ex_content = item.get("exContent", {})
                    user_nick = ex_content.get("userNick", "")
                
                # 如果没有exContent.userNick，尝试从clickParam中获取
                if not user_nick and "clickParam" in item and isinstance(item["clickParam"], dict) and "args" in item["clickParam"]:
                    click_args = item["clickParam"]["args"]
                    user_nick = click_args.get("seller_nick", "")
                
                # 如果没有地区但有用户昵称，则使用用户昵称
                if (not location or not location.strip()) and user_nick:
                    location = user_nick
                
                # 提取发布时间
                post_time = ""
                # 尝试从clickParam中获取
                if "clickParam" in item and isinstance(item["clickParam"], dict) and "args" in item["clickParam"]:
                    click_args = item["clickParam"]["args"]
                    if "publishTime" in click_args:
                        timestamp = click_args["publishTime"]
                        post_time = format_post_time(timestamp)
                
                # 如果clickParam中没有发布时间，尝试从exContent中获取
                if not post_time:
                    ex_content = item.get("exContent", {})
                    timestamp = ex_content.get("createdTime", "")
                    if timestamp:
                        post_time = format_post_time(timestamp)
                
                item_data = {
                    'title': title,
                    'price': price_text,
                    'image': image_url,
                    'itemId': item_id,
                    'location': location or user_nick,
                    'postTime': post_time or "",
                }
                
                # 打印调试信息
                print(f"处理商品: {title}")
                print(f"  - 价格: {price_text}")
                print(f"  - 图片URL: {image_url}")
                print(f"  - 位置: {location}")
                print(f"  - 发布时间: {post_time}")
                
                items.append(item_data)
            except Exception as e:
                print(f"处理商品数据时出错: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return jsonify({
            'success': True,
            'message': f'找到 {len(items)} 个商品',
            'items': items
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'搜索出错: {str(e)}'
        })

@app.route('/advanced_search', methods=['POST'])
def advanced_search():
    global auto_add_commodity
    
    try:
        # 如果还没有初始化，则创建实例
        if auto_add_commodity is None:
            auto_add_commodity = AutoAddCommodity()
        
        # 获取基本搜索参数
        search_name = request.form.get('search_name', '')
        min_price = request.form.get('min_price', '0')
        max_price = request.form.get('max_price', '9999999')
        
        # 获取高级搜索参数
        location = request.form.get('location', '')  # 地区
        post_time = request.form.get('post_time', '')  # 发布时间
        sort_type = request.form.get('sort_type', 'default')  # 排序方式
        condition = request.form.get('condition', '')  # 商品成色
        shipping_option = request.form.get('shipping_option', '')  # 运费方式
        is_attention = request.form.get('is_attention', 'false').lower() == 'true'  # 是否只看关注的人
        
        # 构建高级搜索过滤条件
        filter_values = []
        
        # 添加价格范围
        if min_price or max_price:
            filter_values.append(f"priceRange:{min_price},{max_price}")
        
        # 添加地区过滤
        if location:
            filter_values.append(f"location:{location}")
        
        # 添加发布时间过滤
        if post_time:
            filter_values.append(f"postTime:{post_time}")
        
        # 添加商品成色过滤
        if condition:
            filter_values.append(f"itemCondition:{condition}")
        
        # 添加运费方式过滤
        if shipping_option:
            filter_values.append(f"shippingOption:{shipping_option}")
        
        # 合并过滤条件
        filter_str = ";".join(filter_values)
        
        # 调用高级搜索方法
        result = advanced_search_items(
            auto_add_commodity=auto_add_commodity,
            keyword=search_name,
            filters=filter_str,
            sort_type=sort_type,
            is_attention=is_attention
        )
        
        # 打印第一个结果的结构用于调试
        if result and len(result) > 0:
            print("高级搜索 - 第一个结果的结构详细情况:")
            print(json.dumps(result[0], indent=2, ensure_ascii=False)[:1000] + "...")
        
        # 处理结果数据
        items = []
        for item in result:
            try:
                # 提取商品标题 - 直接从主数据中获取
                title = item.get("title", "")
                if not title or not title.strip():
                    # 尝试从exContent中获取
                    ex_content = item.get("exContent", {})
                    title = ex_content.get("title", "未知商品")
                
                # 提取商品价格
                price_text = ""
                # 尝试从clickParam中获取价格
                if "clickParam" in item and isinstance(item["clickParam"], dict) and "args" in item["clickParam"]:
                    click_args = item["clickParam"]["args"]
                    if "price" in click_args:
                        price_text = click_args["price"]
                
                # 如果clickParam中没有价格，尝试其他方法获取
                if not price_text:
                    if "price" in item and isinstance(item["price"], list):
                        # 遍历价格列表，找到整数部分
                        for price_part in item["price"]:
                            if price_part.get("type") == "integer":
                                price_text = price_part.get("text", "")
                                break
                    else:
                        # 尝试从detailParams中获取价格
                        detail_params = item.get("detailParams", {})
                        if "soldPrice" in detail_params:
                            price_text = detail_params["soldPrice"]
                        elif "price" in item and isinstance(item["price"], dict):
                            price_text = item["price"].get("priceDesc", "")
                        
                    # 如果还是没有价格，尝试从exContent获取
                    if not price_text:
                        ex_content = item.get("exContent", {})
                        price_text = ex_content.get("priceText", "")
                
                # 添加货币符号
                if price_text and not price_text.startswith("¥"):
                    price_text = f"¥{price_text}"
                elif not price_text:
                    price_text = "未知价格"
                
                # 提取图片URL
                image_url = ""
                
                # 尝试从picUrl直接获取
                image_url = item.get("picUrl", "")
                
                # 如果没有picUrl，尝试从exContent.pic获取
                if not image_url or not image_url.strip():
                    ex_content = item.get("exContent", {})
                    image_url = ex_content.get("pic", "")
                
                # 如果没有exContent.pic，尝试从图片列表获取第一张
                if not image_url or not image_url.strip():
                    images = item.get("images", [])
                    if images and len(images) > 0:
                        image_url = images[0]
                
                # 如果从clickParam中提取
                if not image_url or not image_url.strip():
                    if "clickParam" in item and isinstance(item["clickParam"], dict) and "args" in item["clickParam"]:
                        click_args = item["clickParam"]["args"]
                        if "pic" in click_args:
                            image_url = click_args["pic"]
                
                # 确保图片URL是完整的
                if image_url and not image_url.startswith(('http://', 'https://')):
                    image_url = f"https:{image_url}" if image_url.startswith('//') else f"https://{image_url}"
                
                # 提取地区信息
                location = ""
                
                # 尝试从clickParam中获取地区
                if "clickParam" in item and isinstance(item["clickParam"], dict) and "args" in item["clickParam"]:
                    click_args = item["clickParam"]["args"]
                    if "location" in click_args:
                        location = click_args["location"]
                
                # 如果clickParam中没有地区，尝试从area获取
                if not location or not location.strip():
                    location = item.get("area", "")
                
                # 如果area中没有地区，尝试从exContent获取
                if not location or not location.strip():
                    ex_content = item.get("exContent", {})
                    location = ex_content.get("provCity", "")
                
                # 提取商品ID
                item_id = item.get("itemId", "")
                if not item_id:
                    # 尝试从detailParams中获取
                    detail_params = item.get("detailParams", {})
                    item_id = detail_params.get("itemId", "")
                
                # 如果还没有商品ID，尝试从exContent中获取
                if not item_id:
                    ex_content = item.get("exContent", {})
                    item_id = ex_content.get("itemId", "")
                
                # 如果还没有商品ID，尝试从clickParam中获取
                if not item_id and "clickParam" in item and isinstance(item["clickParam"], dict) and "args" in item["clickParam"]:
                    click_args = item["clickParam"]["args"]
                    if "id" in click_args:
                        item_id = click_args["id"]
                
                # 提取用户昵称
                user_nick = ""
                # 尝试从userNickName获取
                user_nick = item.get("userNickName", "")
                
                # 如果没有userNickName，尝试从detailParams中获取
                if not user_nick:
                    detail_params = item.get("detailParams", {})
                    user_nick = detail_params.get("userNick", "")
                
                # 如果没有detailParams.userNick，尝试从exContent中获取
                if not user_nick:
                    ex_content = item.get("exContent", {})
                    user_nick = ex_content.get("userNick", "")
                
                # 如果没有exContent.userNick，尝试从clickParam中获取
                if not user_nick and "clickParam" in item and isinstance(item["clickParam"], dict) and "args" in item["clickParam"]:
                    click_args = item["clickParam"]["args"]
                    user_nick = click_args.get("seller_nick", "")
                
                # 如果没有地区但有用户昵称，则使用用户昵称
                if (not location or not location.strip()) and user_nick:
                    location = user_nick
                
                # 提取发布时间
                post_time = ""
                # 尝试从clickParam中获取
                if "clickParam" in item and isinstance(item["clickParam"], dict) and "args" in item["clickParam"]:
                    click_args = item["clickParam"]["args"]
                    if "publishTime" in click_args:
                        timestamp = click_args["publishTime"]
                        post_time = format_post_time(timestamp)
                
                # 如果clickParam中没有发布时间，尝试从exContent中获取
                if not post_time:
                    ex_content = item.get("exContent", {})
                    timestamp = ex_content.get("createdTime", "")
                    if timestamp:
                        post_time = format_post_time(timestamp)
                
                item_data = {
                    'title': title,
                    'price': price_text,
                    'image': image_url,
                    'itemId': item_id,
                    'location': location or user_nick,
                    'postTime': post_time or "",
                }
                
                # 打印调试信息
                print(f"处理高级搜索商品: {title}")
                print(f"  - 价格: {price_text}")
                print(f"  - 图片URL: {image_url}")
                print(f"  - 位置: {location}")
                print(f"  - 发布时间: {post_time}")
                
                items.append(item_data)
            except Exception as e:
                print(f"处理高级搜索商品数据时出错: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return jsonify({
            'success': True,
            'message': f'找到 {len(items)} 个商品',
            'items': items
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'高级搜索出错: {str(e)}'
        })

@app.route('/simple_search', methods=['POST'])
def simple_search():
    """全新的独立搜索函数，不依赖于预售"""
    global auto_add_commodity
    
    try:
        # 如果还没有初始化，则创建实例
        if auto_add_commodity is None:
            auto_add_commodity = AutoAddCommodity()
        
        # 获取搜索参数
        search_name = request.form.get('search_name', '')
        min_price = request.form.get('min_price', '0')
        max_price = request.form.get('max_price', '9999999')
        is_attention = request.form.get('is_attention', 'false').lower() == 'true'
        
        # 创建价格范围
        price_range = f'{min_price},{max_price}'
        
        # 调用自定义搜索方法
        result = search_items_simple(
            auto_add_commodity=auto_add_commodity,
            keyword=search_name,
            price_range=price_range,
            is_attention=is_attention
        )
        
        # 打印第一个结果的结构用于调试
        if result and len(result) > 0:
            print("第一个结果的结构详细情况:")
            print(json.dumps(result[0], indent=2, ensure_ascii=False)[:1000] + "...")
        
        # 处理结果数据
        items = []
        for item in result:
            try:
                # 提取商品标题
                title = item.get("title", "")
                if not title or not title.strip():
                    # 尝试从exContent中获取
                    ex_content = item.get("exContent", {})
                    title = ex_content.get("title", "未知商品")
                
                # 使用处理过的价格
                price_text = item.get("processed_price", "未知价格")
                
                # 添加货币符号
                if price_text and not price_text.startswith("¥"):
                    price_text = f"¥{price_text}"
                
                # 使用处理过的图片URL
                image_url = item.get("processed_image", "")
                
                # 使用处理过的地区
                location = item.get("processed_location", "")
                
                # 使用处理过的用户昵称
                user_nick = item.get("processed_user_nick", "")
                
                # 使用处理过的发布时间
                post_time = item.get("processed_post_time", "")
                
                # 提取商品ID
                item_id = item.get("itemId", "")
                if not item_id:
                    # 尝试从detailParams中获取
                    ex_content = item.get("exContent", {})
                    detail_params = ex_content.get("detailParams", {})
                    item_id = detail_params.get("itemId", "")
                
                item_data = {
                    'title': title,
                    'price': price_text,
                    'image': image_url,
                    'itemId': item_id,
                    'location': location,
                    'userName': user_nick,
                    'postTime': post_time,
                }
                
                # 打印调试信息
                print(f"处理商品: {title}")
                print(f"  - 价格: {price_text}")
                print(f"  - 图片URL: {image_url}")
                print(f"  - 位置: {location}")
                print(f"  - 用户名: {user_nick}")
                print(f"  - 发布时间: {post_time}")
                
                items.append(item_data)
            except Exception as e:
                print(f"处理商品数据时出错: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return jsonify({
            'success': True,
            'message': f'找到 {len(items)} 个商品',
            'items': items
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'搜索出错: {str(e)}'
        })

def search_items_simple(auto_add_commodity, keyword, price_range='0,9999999', is_attention=False, page_size=50, page_number=1):
    """
    简单搜索商品，不判断是否预售
    
    参数:
    - keyword: 搜索关键词
    - price_range: 价格范围，格式为"min,max"
    - is_attention: 是否只看关注的人
    - page_size: 每页显示的商品数量
    - page_number: 页码
    
    返回:
    - 商品列表
    """
    # 借用现有的会话处理
    session = Session()
    session.cookies.update(auto_add_commodity.cookies)
    session.headers.update(auto_add_commodity.headers)
    
    # 获取当前时间戳
    timestamp = str(round(time.time() * 1000))
    
    # 构建请求参数
    params = {
        'jsv': '2.7.2',
        'appKey': '34839810',
        't': timestamp,
        'sign': '',
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
    
    # 构建搜索数据
    search_data = {
        'pageNumber': page_number,
        'keyword': keyword,
        'fromFilter': True,
        'rowsPerPage': page_size,
        'sortValue': '',
        'sortField': '',
        'customDistance': '',
        'gps': '',
        'propValueStr': {'searchFilter': f"priceRange:{price_range};"},
        'customGps': '',
        'searchReqFromPage': 'pcSearch',
        'extraFilterValue': '{}',
        'userPositionJson': '{}'
    }
    
    data = {
        'data': json.dumps(search_data, separators=(',', ':'))
    }
    
    # 添加签名
    params = auto_add_commodity.createRequestParams(params=params, data=data, timestamp=timestamp)
    
    # 发送请求
    try:
        print(f"正在搜索: {keyword}, 价格范围: {price_range}")
        response = session.post(
            "https://h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search/1.0/",
            params=params, 
            data=data
        )
        
        if response.status_code != 200:
            print(f"搜索请求失败: 状态码 {response.status_code}")
            return []
            
        res_json = response.json()
        if 'data' not in res_json:
            print(f"返回数据格式异常: {res_json}")
            return []
            
        res = res_json['data']
        if 'resultList' not in res:
            print(f"没有商品列表数据")
            return []
            
        # 处理搜索结果
        result_items = []
        for item in res['resultList']:
            try:
                # 打印整个项目结构以便调试
                print("原始项目结构:", json.dumps(item, ensure_ascii=False)[:500] + "...")
                
                if 'data' not in item:
                    continue
                    
                item_data = item['data']
                if not item_data or 'item' not in item_data:
                    continue
                    
                item_main = item_data.get('item', {}).get('main')
                if not item_main:
                    continue
                
                # 如果需要只看关注的人
                if is_attention:
                    item_ex_content = item_main.get('exContent', {})
                    fish_tags = str(item_ex_content.get('fishTags', '[]'))
                    if '你关注过的人' not in fish_tags:
                        continue
                
                # 处理价格
                price_text = ""
                # 如果price是列表类型，找到整数部分
                if "price" in item_main and isinstance(item_main["price"], list):
                    for price_part in item_main["price"]:
                        if price_part.get("type") == "integer":
                            price_text = price_part.get("text", "")
                            break
                # 如果price不是列表或没有找到整数部分，尝试从detailParams中获取soldPrice
                if not price_text:
                    ex_content = item_main.get("exContent", {})
                    detail_params = ex_content.get("detailParams", {})
                    price_text = detail_params.get("soldPrice", "")
                
                # 如果没有找到价格，将price字段设为原始值以便调试
                if not price_text:
                    price_text = str(item_main.get("price", "未知价格"))
                
                # 处理图片URL
                image_url = item_main.get("picUrl", "")
                # 从exContent中获取
                if not image_url:
                    ex_content = item_main.get("exContent", {})
                    image_url = ex_content.get("picUrl", "")
                
                # 确保图片URL是完整的
                if image_url and not image_url.startswith(('http://', 'https://')):
                    image_url = f"https:{image_url}" if image_url.startswith('//') else f"https://{image_url}"
                
                # 获取位置信息
                location = get_location(item_main)
                
                # 获取用户名
                user_nick = ""
                ex_content = item_main.get("exContent", {})
                user_nick = ex_content.get("userNickName", "")
                if not user_nick:
                    detail_params = ex_content.get("detailParams", {})
                    user_nick = detail_params.get("userNick", "")
                
                # 获取发布时间
                post_time = ""
                click_param = item_main.get("clickParam", {})
                if click_param and isinstance(click_param, dict) and "args" in click_param:
                    click_args = click_param["args"]
                    if "publishTime" in click_args:
                        timestamp = click_args["publishTime"]
                        post_time = format_post_time(timestamp)
                
                # 如果clickParam中没有发布时间，尝试从fishTags中获取
                if not post_time:
                    fish_tags = ex_content.get("fishTags", {})
                    r2_tags = fish_tags.get("r2", {}).get("tagList", [])
                    for tag in r2_tags:
                        if tag.get("data", {}).get("content", "").endswith("发布"):
                            post_time = tag.get("data", {}).get("content", "")
                            break
                
                # 提取标题
                title = item_main.get("title", "")
                if not title:
                    title = ex_content.get("title", "")
                if not title:
                    detail_params = ex_content.get("detailParams", {})
                    title = detail_params.get("title", "未知商品")
                
                # 提取商品ID
                item_id = item_main.get("itemId", "")
                if not item_id:
                    item_id = ex_content.get("itemId", "")
                
                # 修改item_main以包含处理过的价格、图片URL和地区，便于后续处理
                item_main["processed_price"] = price_text
                item_main["processed_image"] = image_url
                item_main["processed_location"] = location
                item_main["processed_user_nick"] = user_nick
                item_main["processed_post_time"] = post_time
                
                result_items.append(item_main)
            except Exception as e:
                print(f"处理搜索结果项时出错: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"搜索完成，找到 {len(result_items)} 个商品")
        return result_items
    except Exception as e:
        print(f"搜索过程出错: {e}")
        import traceback
        traceback.print_exc()
        return []

def format_post_time(timestamp):
    """格式化发布时间"""
    if not timestamp:
        return ''
    
    try:
        # 尝试转换时间戳为可读时间
        post_time = datetime.fromtimestamp(int(timestamp) / 1000)
        now = datetime.now()
        
        # 计算时间差
        delta = now - post_time
        
        if delta.days == 0:
            # 今天发布的
            if delta.seconds < 3600:
                # 不到一小时
                minutes = delta.seconds // 60
                return f"{minutes}分钟前"
            else:
                # 几小时前
                hours = delta.seconds // 3600
                return f"{hours}小时前"
        elif delta.days == 1:
            # 昨天发布的
            return "昨天"
        elif delta.days < 7:
            # 一周内发布的
            return f"{delta.days}天前"
        else:
            # 一周前发布的
            return post_time.strftime("%Y-%m-%d")
    except:
        return timestamp

def advanced_search_items(auto_add_commodity, keyword, filters="", sort_type="default", is_attention=False):
    """
    高级搜索商品
    
    参数:
    - keyword: 搜索关键词
    - filters: 过滤条件，格式为"filter1:value1;filter2:value2"
    - sort_type: 排序方式，可选值: default(默认), price_asc(价格升序), price_desc(价格降序), time_desc(最新发布)
    - is_attention: 是否只看关注的人
    
    返回:
    - 商品列表
    """
    # 使用Session而不是driver.session
    session = Session()
    session.cookies.update(auto_add_commodity.cookies)
    session.headers.update(auto_add_commodity.headers)
    
    # 获取当前时间戳
    timestamp = str(round(time.time() * 1000))
    
    # 构建排序参数
    sort_field = ""
    sort_value = ""
    if sort_type == "price_asc":
        sort_field = "price"
        sort_value = "1"  # 升序
    elif sort_type == "price_desc":
        sort_field = "price"
        sort_value = "0"  # 降序
    elif sort_type == "time_desc":
        sort_field = "postTime"
        sort_value = "0"  # 最新发布
    
    # 构建请求参数
    params = {
        'jsv': '2.7.2',
        'appKey': '34839810',
        't': timestamp,
        'sign': '',
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
    
    # 构建请求数据
    data = {
        'data': json.dumps({
            'pageNumber': 1,
            'keyword': keyword,
            'fromFilter': True,
            'rowsPerPage': 50,  # 增加每页结果数
            'sortValue': sort_value,
            'sortField': sort_field,
            'customDistance': '',
            'gps': '',
            'propValueStr': {'searchFilter': filters},
            'customGps': '',
            'searchReqFromPage': 'pcSearch',
            'extraFilterValue': '{}',
            'userPositionJson': '{}'
        }, separators=(',', ':'))
    }
    
    # 添加签名
    params = auto_add_commodity.createRequestParams(params=params, data=data, timestamp=timestamp)
    
    # 发送请求
    try:
        print(f"正在搜索: {keyword}, 过滤条件: {filters}, 排序方式: {sort_type}")
        response = session.post(
            "https://h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search/1.0/",
            params=params, 
            data=data
        )
        
        if response.status_code != 200:
            print(f"搜索请求失败: 状态码 {response.status_code}")
            return []
            
        res_json = response.json()
        if 'data' not in res_json:
            print(f"返回数据格式异常: {res_json}")
            return []
            
        res = res_json['data']
        if 'resultList' not in res:
            print(f"没有商品列表数据")
            return []
            
        # 处理搜索结果
        result_items = []
        for item in res['resultList']:
            if 'data' not in item:
                continue
                
            item_data = item['data']
            if not item_data or 'item' not in item_data:
                continue
                
            item_main = item_data.get('item', {}).get('main')
            if not item_main:
                continue
            
            # 如果需要只看关注的人
            if is_attention:
                item_ex_content = item_main.get('exContent', {})
                fish_tags = str(item_ex_content.get('fishTags', '[]'))
                if '你关注过的人' not in fish_tags:
                    continue
            
            result_items.append(item_main)
        
        print(f"搜索完成，找到 {len(result_items)} 个商品")
        return result_items
    except Exception as e:
        print(f"搜索过程出错: {e}")
        return []

@app.route('/add_collection', methods=['POST'])
def add_collection():
    global auto_add_commodity
    
    try:
        # 如果还没有初始化，则创建实例
        if auto_add_commodity is None:
            auto_add_commodity = AutoAddCommodity()
        
        item_id = request.form.get('item_id', '')
        if not item_id:
            return jsonify({'success': False, 'message': '商品ID不能为空'})
        
        # 添加到收藏列表
        auto_add_commodity.add_attention_list(item_id)
        
        return jsonify({
            'success': True,
            'message': '添加收藏成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'添加收藏失败: {str(e)}'
        })

@app.route('/clear_collections', methods=['POST'])
def clear_collections():
    global auto_add_commodity
    
    try:
        # 如果还没有初始化，则创建实例
        if auto_add_commodity is None:
            auto_add_commodity = AutoAddCommodity()
        
        # 清空收藏列表
        auto_add_commodity.delete_attention_list()
        
        return jsonify({
            'success': True,
            'message': '清空收藏列表成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'清空收藏列表失败: {str(e)}'
        })

@app.route('/get_locations', methods=['GET'])
def get_locations():
    """获取热门地区列表"""
    locations = [
        {"code": "330100", "name": "杭州"},
        {"code": "310100", "name": "上海"},
        {"code": "110100", "name": "北京"},
        {"code": "440100", "name": "广州"},
        {"code": "440300", "name": "深圳"},
        {"code": "320100", "name": "南京"},
        {"code": "510100", "name": "成都"},
        {"code": "420100", "name": "武汉"},
        {"code": "500100", "name": "重庆"},
        {"code": "320500", "name": "苏州"},
        {"code": "330200", "name": "宁波"},
        {"code": "350200", "name": "厦门"},
        {"code": "370100", "name": "济南"},
        {"code": "210100", "name": "沈阳"},
        {"code": "320200", "name": "无锡"},
        {"code": "610100", "name": "西安"},
        {"code": "340100", "name": "合肥"},
        {"code": "330300", "name": "温州"},
        {"code": "320400", "name": "常州"},
        {"code": "441900", "name": "东莞"}
    ]
    return jsonify({"success": True, "locations": locations})

def get_location(item):
    """从商品数据中获取位置信息"""
    # 首先检查是否有处理好的location字段
    if "processed_location" in item:
        return item["processed_location"]
    
    # 尝试从exContent中的area字段获取地区
    ex_content = item.get("exContent", {})
    location = ex_content.get("area", "")
    
    # 尝试获取用户昵称
    user_nick = ex_content.get("userNickName", "")
    if not user_nick:
        detail_params = ex_content.get("detailParams", {})
        user_nick = detail_params.get("userNick", "")
    
    # 如果地区和用户名都有，则返回地区
    if location:
        return location
    # 如果只有用户名没有地区，则使用用户名作为位置
    elif user_nick:
        return "未知地区"
    
    # 如果都没有，返回未知位置
    return "未知位置"

if __name__ == '__main__':
    # 使用8080端口避免与MacOS AirPlay冲突
    print(f"静态文件目录: {static_dir}")
    print(f"模板文件目录: {template_dir}")
    app.run(debug=True, host='0.0.0.0', port=8080) 