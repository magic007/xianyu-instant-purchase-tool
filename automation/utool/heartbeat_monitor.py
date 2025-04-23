import socket
import time


def heartbeat_connection_ipv4(host, port, timeout=10, interval=60):
    sock = None
    try:
        # 创建 IPv4 TCP Socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        # 正确连接方式：AF_INET 只需 (host, port)
        sock.connect((host, port))  # 关键修复：移除多余的参数
        print(f"TCP 连接成功：{host}:{port}")

        # 心跳循环
        while True:
            try:
                # 发送心跳数据（需匹配目标服务器的协议）
                request = (
                    f"HEAD / HTTP/1.1\r\n"
                    f"Host: {host}\r\n"  # 关键：Host头必须为目标域名（非IP）
                    f"\r\n"
                ).encode('utf-8')

                sock.send(request)
                response = sock.recv(1024)
                print(f"心跳响应：{response.decode('utf-8', errors='ignore')}")

                time.sleep(interval)

            except (socket.timeout, ConnectionResetError) as e:
                print(f"心跳异常：{e}, 尝试重连...")
                # 重建连接
                sock.close()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                sock.connect((host, port))
            except KeyboardInterrupt:
                print("用户终止连接")
                break

    except Exception as e:
        print(f"连接错误: {e}")
    finally:
        if sock:
            sock.close()
            print("连接已关闭")
def heartbeat_connection_ipv6(host, port, timeout=10, interval=60):
    sock = None
    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        sock.settimeout(timeout)
        sock.connect((host, port, 0, 0))
        print(f"TCP 连接成功：{host}:{port}")

        # 心跳循环
        while True:
            try:
                # 发送心跳数据（示例：HTTP HEAD 请求）
                request = b"HEAD / HTTP/1.1\r\nHost: example.com\r\n\r\n"
                sock.send(request)
                response = sock.recv(1024)
                print(f"心跳响应：{response.decode('utf-8', errors='ignore')}")

                # 等待间隔
                time.sleep(interval)

            except socket.error as e:
                print(f"心跳失败：{e}")
                break
            except KeyboardInterrupt:
                print("用户终止连接")
                break

    except Exception as e:
        print(f"错误：{e}")
    finally:
        if sock:
            sock.close()
            print("连接已关闭")


# 调用示例（IPv4 地址）
heartbeat_connection_ipv4("59.82.58.67", 443, interval=1)

heartbeat_connection_ipv6("2408:4001:f00::198", 443, interval=1)
