# 闲鱼秒拍工具

闲鱼秒拍，只为快人一步

## 项目说明

该项目是一个用于闲鱼平台的自动化工具，主要功能包括自动秒杀商品。工具通过Selenium控制Chrome浏览器实现闲鱼平台的自动操作。

### 主要功能

1. **自动登录**：自动打开闲鱼网站并检查登录状态，首次使用需手动登录，后续会保存Cookie自动登录
2. **收藏商品管理**：自动获取用户收藏的商品列表，并进行筛选
3. **日期识别**：从商品标题中自动识别秒杀时间，并按时间进行分组
4. **自动秒杀**：在指定时间自动进行秒杀操作，提高抢购成功率
5. **智能重试**：遇到网络问题时自动重试，保证操作的可靠性

## 环境准备

1. Python 3.6或更高版本
2. Chrome浏览器
3. 必要的Python依赖包
4. 适合您Chrome版本的ChromeDriver (如果选择本地驱动模式)

## 安装依赖

```bash
pip install selenium
```

## 目录结构

```
automation/
├── cache/               # 存储Cookies和缓存文件
├── config/              # 配置文件目录
│   └── config.json      # 主配置文件
├── js/                  # JavaScript文件目录
├── service/             # 核心服务模块
│   └── execute_task/    # 任务执行模块
│       ├── execute.py   # 主入口文件
│       ├── manage.py    # 任务管理类
│       ├── task.py      # 任务定义类
│       └── request_config.py # 请求配置类
└── utool/               # 工具类目录
    └── sokcet_connect.py # 网络连接工具

drivers/                 # ChromeDriver存放目录
```

## ChromeDriver 设置

项目支持两种方式使用ChromeDriver:

### 1. 使用本地驱动 (推荐)

1. 从 [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/) 下载与您Chrome浏览器版本匹配的驱动
2. 解压得到的`chromedriver`文件，放入项目的`drivers`目录下
3. 确保脚本中的`USE_LOCAL_DRIVER`设置为`True`

```python
# 配置项 - 修改这里以适应您的环境
USE_LOCAL_DRIVER = True  # 是否使用本地ChromeDriver
LOCAL_DRIVER_PATH = os.path.join(os.getcwd(), "drivers", "chromedriver")  # 本地ChromeDriver路径
```

### 2. 使用自动下载驱动 (需要网络访问)

如果您可以正常访问Google的资源，可以使用自动下载功能:

1. 修改脚本中的配置:

```python
USE_LOCAL_DRIVER = False  # 设置为False使用自动下载
```

## 运行方式

```bash
python -m automation.service.execute_task.execute
```

## 运行流程

1. **启动**：程序自动打开Chrome浏览器并访问闲鱼网站
2. **登录**：
   - 首次运行需要手动登录
   - 登录成功后，会自动保存Cookie，下次运行时自动使用
3. **获取收藏**：
   - 程序自动获取您收藏的商品列表
   - 按商品状态进行筛选，只处理有效商品
4. **解析时间**：
   - 从商品标题中提取日期时间信息 (格式: XXXX年XX月XX日XX点XX分)
   - 按日期时间分组，相同时间的商品会被一起处理
5. **秒杀准备**：
   - 程序会计算距离秒杀时间的时间差
   - 如果时间差较大，会进入等待模式
6. **执行秒杀**：
   - 在秒杀时间点附近启动秒杀任务
   - 使用高效的网络请求方式提高秒杀成功率
7. **结果反馈**：
   - 实时反馈秒杀结果和状态

## 配置说明

配置文件位于：`automation/config/config.json`

您可以在配置文件中修改以下参数：

```json
{
  "headers": {
    // 浏览器请求头配置
  },
  "apiConfig": {
    "secKillConfig": {
      // 秒杀API配置
    },
    "collectConfig": {
      // 收藏商品API配置
    }
  }
}
```

## 商品标题日期格式

在收藏商品时，为了让系统能正确识别秒杀时间，商品标题应包含特定格式的日期时间，例如：

```
闲鱼秒杀测试商品 2024年10月31日10点30分
```

日期时间格式必须为：`XXXX年XX月XX日XX点XX分`，系统会自动识别这种格式并安排秒杀任务。

如果商品标题中没有包含上述格式的日期时间，系统会使用当前时间作为默认值。

## 常见问题

### 1. ChromeDriver版本不匹配

如果遇到以下错误:
```
This version of ChromeDriver only supports Chrome version XX
Current browser version is YY
```

请确保下载与您Chrome浏览器版本匹配的ChromeDriver。

### 2. 配置文件路径错误

如果遇到以下错误:
```
No such file or directory: config.json
```

这通常是由路径问题引起的。项目已经修复了相对路径的问题，使用绝对路径来引用配置文件和缓存文件。

### 3. 浏览器崩溃问题

如果遇到以下错误：
```
Message: 
Stacktrace:
0   chromedriver...
```

可能是因为浏览器崩溃。解决方法：

1. 确保使用了最新版本的代码，已添加更健壮的错误处理和元素定位
2. 尝试以下Chrome启动选项：
   - 添加 `--no-sandbox` 参数 (已在最新代码中添加)
   - 添加 `--disable-dev-shm-usage` 参数 (已在最新代码中添加)
   - 添加 `--disable-gpu` 参数 (已在最新代码中添加)
3. 如果崩溃仍然发生，尝试增加程序中的等待时间（sleep）

### 4. 登录问题

首次运行时需要手动登录闲鱼账号，登录后程序会保存Cookie供后续使用。如果登录遇到问题，程序会提示您手动完成登录并按回车继续。

### 5. 操作超时问题

如果在使用过程中遇到操作超时的问题（如元素无法找到），可以尝试：

1. 在代码中增加等待时间：
```python
WebDriverWait(driver, 20)  # 增加等待时间到20秒
```

2. 在关键操作前添加短暂延迟：
```python
time.sleep(5)  # 添加5秒延迟
```

## 技术实现

### 1. 浏览器自动化

使用Selenium WebDriver控制Chrome浏览器，实现页面导航、元素定位、点击和输入等操作。

### 2. 网络请求优化

使用自定义的Socket连接方式进行秒杀请求，比标准的requests库更快，提高秒杀成功率。

### 3. 智能日期识别

使用正则表达式从商品标题中提取日期时间信息，支持多种格式的日期时间表示。

### 4. 并发处理

使用线程池管理多个秒杀任务，提高并发性能，增加秒杀成功率。

### 5. 错误处理

全面的异常捕获和处理机制，确保程序在各种异常情况下都能保持运行，增强稳定性。

## 更新日志

### 2024-10-31
- 移除了旧版本（automation_v1）相关代码
- 修复了配置文件路径问题
- 增强了登录过程的稳定性
- 添加了更详细的调试信息输出
- 改进了元素定位方式，提高了页面识别的稳定性
- 添加了异常捕获和错误处理，防止程序意外退出
- 增加了Chrome浏览器启动参数，提高稳定性

## 注意事项

该工具主要用于学习和研究，请合理使用，避免违反闲鱼平台的使用条款。使用本工具产生的一切后果由使用者自行承担。
