import socket
import ssl
import time
import urllib.parse

# 目标 IPv6 地址和端口 (需提前通过CDN绕过获取真实IP)
# TARGET_IPV6 = "2408:4001:f00::198"
# TARGET_IPV6 = "2408:4001:f00::b9"
TARGET_IPV6 = "59.82.58.67:443"
PORT = 443

params = {
    'jsv': '2.7.2',
    'appKey': '34839810',
    't': '1743786299671',
    'sign': 'edc1bf3082f76b07028481e854b1698b',
    'v': '5.0',
    'type': 'json',
    'accountSite': 'xianyu',
    'dataType': 'json',
    'timeout': '20000',
    'api': 'mtop.taobao.idle.trade.order.create',
    'valueType': 'string',
    'sessionOption': 'AutoLoginOnly',
    'spm_cnt': 'a21ybx.create-order.0.0',
    'spm_pre': 'a21ybx.item.buy.1.64703da6I1Az29',
    'log_id': '64703da6I1Az29',
}

data = {
    'data': '{"params":"[{\\"adjust\\":\\"true\\",\\"buyQuantity\\":\\"1\\",\\"changeMeanTimeItem\\":\\"false\\",\\"deliverId\\":\\"23425317326\\",\\"deliverType\\":\\"1\\",\\"disable\\":\\"false\\",\\"freeze\\":\\"none\\",\\"inventory\\":\\"1\\",\\"itemId\\":\\"906214469002\\",\\"mainItem\\":\\"true\\",\\"price\\":\\"10.00\\",\\"renderVersion\\":\\"DIALOG\\",\\"urlParams\\":\\"{}\\"}]"}',
}



headers = {
    'Host': 'h5api.m.goofish.com',  # 必须保留 Host 头
    'Accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Cookie': 'cna=/uJKIKW0f1oBASQIggx1N9LR; t=790c30c049107ece93b04143b23d09f3; tracknick=tb101963821; unb=2204659669476; _hvn_lgc_=77; havana_lgc2_77=eyJoaWQiOjIyMDQ2NTk2Njk0NzYsInNnIjoiMzA5YWI5M2RlZGUwOWU3Zjc2NWVmZTdiN2I0ZWM0YjYiLCJzaXRlIjo3NywidG9rZW4iOiIxeHctZE96Y1lYcE9CNEl4dHAtTWFuQSJ9; havana_lgc_exp=1773402975899; xlly_s=1; isg=BHFxK0SIsu8Zrh7XPyFtMuNPgP0LXuXQF1IHjFOGAzhXepDMm66koM3TnA4cin0I; _samesite_flag_=true; sgcookie=E100vjGMRZzTvdxflq9tbJX2Vc1ZLaIdoEuPRcVmbya4zcTyzly1d7YbizVESOmDsJdsYdxXaYpxItdt5Yhe1BJX84U7%2B7nb%2FlLuBJZnjcv9Nj0%3D; cookie2=2b378ba11625705258c580b027196c66; csg=7ea3b43b; _tb_token_=e71a3f8be517a; sdkSilent=1743862470726; mtop_partitioned_detect=1; _m_h5_tk=0883d69d738939498a56755ea313909b_1743786752405; _m_h5_tk_enc=b5019127da3590afbc23f06a881aeb0d; tfstk=gFf-tY_r8oqoUeRgZ7wmKQ5H9hzcw6Qrrg7stHxodiIA5Nokd_AlvvIl8MvQ4QfdDQ5cEXxu4BQCjBEgj5VGzaRyOlqgOf-a5BTQtHwDFnMY2VZgj5V0FqOL2ljkiIA8Me-XPeTWVr3X5eAIdLsBcKT6S0OBOMavceLIO0GIOKMXSntBOBsClrLnpBZpc4tn9O5fPLg_ynlIOsLJF-bWcXTVMUpJfa_KOXgeyLK1PnZNfzhwhwJdT2lpVa6NYFsSVo-hIZfWHBeiYHBhP_fJT2kAkpClLpCz5c-OFZCpZgEtLh6llItPFkDWV_7MM99YP7_vw3INNgFTcG9OZ9JdaPiwXT_A9Qf8-Y8PhgRvu6qqNHBfd_vyT0Z2xObcNKd14b5G6K9mjhLnFrUxLvJWulEM8TW_AsUBkh489vke3r8vjrUxLvJWuEKgyyHELKzV.',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
}


# ------------------- 核心逻辑 -------------------
def send_http_over_ipv6():
    try:
        # 1. 创建 IPv6 TCP Socket
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.settimeout(10)

        # 2. 连接目标服务器
        sock.connect((TARGET_IPV6, PORT, 0, 0))
        # 3. 封装为 SSL/TLS 连接（HTTPS）
        context = ssl.create_default_context()
        context.check_hostname = False  # 跳过主机名验证（加速）
        context.verify_mode = ssl.CERT_NONE  # 跳过证书验证
        ssock = context.wrap_socket(sock, server_hostname=TARGET_IPV6)

        # 4. 构造 HTTP 请求报文
        query_str = '&'.join([f"{k}={v}" for k, v in params.items()])
        path = f"/h5/mtop.taobao.idle.trade.order.create/5.0/?{query_str}"

        # 对 data 进行 URL 编码
        data_encoded = urllib.parse.urlencode(data)
        content_length = len(data_encoded.encode('utf-8'))
        request = (
            f"POST {path} HTTP/1.1\r\n"
            f"Host: {headers['Host']}\r\n"
            f"User-Agent: {headers['User-Agent']}\r\n"
            f"Content-Type: {headers['Content-Type']}\r\n"
            f"Cookie: {headers['Cookie']}\r\n"
            f"Content-Length: {content_length}\r\n"
            "\r\n"
            f"{data_encoded}"
        ).encode('utf-8')

        start_time = time.perf_counter()  # **更精准计时**
        ssock.sendall(request)
        # 读取响应数据
        buffer = ssock.recv(1400).decode('utf-8')
        print(buffer)


        end_time = time.perf_counter()
        print(f'请求耗时：{end_time - start_time:.3f} 秒  ')
    except Exception as e:
        print(f"请求失败: {e}")
    finally:
        ssock.close()


# 执行请求
send_http_over_ipv6()
