# 咸鱼接口配置说明

## 通用请求头 (headers)

这些是发送到咸鱼接口的请求头信息，用于模拟浏览器行为：

- **accept**: 接受的内容类型，设置为 application/json
- **accept-language**: 接受的语言，设置为中文优先
- **content-type**: 请求内容类型，设置为表单格式
- **origin**: 请求来源网站
- **referer**: 引用页面
- **user-agent**: 模拟的浏览器标识
- 其他安全相关头部信息

## API 配置 (apiConfig)

### 秒杀配置 (secKillConfig)

用于执行咸鱼商品秒杀/下单操作：

- **api**: 下单接口地址
- **params**: 接口请求参数
  - jsv: JS 版本
  - appKey: 应用标识
  - t: 时间戳（动态生成）
  - sign: 签名（动态生成）
  - api: 接口名称
  - 其他必要参数

- **data**: 接口请求主体数据
  - params 数组包含商品信息：
    - buyQuantity: 购买数量
    - itemId: 商品 ID
    - price: 商品价格
    - deliverId: 配送 ID
    - deliverType: 配送类型

### 收藏配置 (collectConfig)

用于获取用户收藏的商品列表：

- **api**: 收藏列表接口地址
- **params**: 接口请求参数
  - 与秒杀配置类似，但针对收藏功能
  - spm_cnt 和 log_id 为追踪参数

- **data**: 接口请求主体数据
  - pageNumber: 页码
  - rowsPerPage: 每页展示数量
  - type: 列表类型

## 使用说明

此配置文件用于自动化工具与咸鱼平台交互，主要支持商品秒杀和收藏管理功能。使用时需要确保 cookie 和登录状态有效，接口参数中的时间戳和签名通常需要动态生成。 