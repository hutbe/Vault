#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mosquitto MQTT 测试客户端
支持普通连接和 SSL 连接
兼容 Paho MQTT 2.0+
"""

import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
import ssl
import time
import argparse


def on_connect(client, userdata, flags, reason_code, properties):
    """连接回调 - MQTT 2.0 版本"""
    if reason_code == 0:
        print("✓ 连接成功!")
        client.subscribe("test/#")
        print("✓ 订阅主题: test/#")
    else:
        print(f"✗ 连接失败，错误码: {reason_code}")


def on_message(client, userdata, msg):
    """消息接收回调 - 签名未变"""
    print(f"收到消息 [{msg.topic}]: {msg.payload.decode()}")


def on_publish(client, userdata, mid, reason_code, properties):
    """发布回调 - MQTT 2.0 版本"""
    print(f"✓ 消息发布成功 (ID: {mid})")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    """断开连接回调 - MQTT 2.0 版本"""
    print(f"断开连接 (原因: {reason_code})")


def test_connection(host, port, username, password, use_ssl=False, ca_cert=None):
    """测试 MQTT 连接"""

    print(f"MQTT 连接 host: {host} port: {port} username: {username} password: {password}")

    # 创建客户端 - 使用新的 API 版本
    client = mqtt.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
        client_id="test-client"
    )

    # 设置回调
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect

    # 设置认证
    client.username_pw_set(username, password)

    # SSL 配置
    if use_ssl:
        print(f"使用 SSL 连接...")
        if ca_cert:
            client.tls_set(
                ca_certs=ca_cert,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS_CLIENT
            )
        else:
            # 不验证证书 (仅测试用)
            client.tls_set(cert_reqs=ssl.CERT_NONE)
            client.tls_insecure_set(True)

    try:
        # 连接
        print(f"连接到 {host}:{port}...")
        client.connect(host, port, 60)

        # 启动循环
        client.loop_start()

        # 发布测试消息
        time.sleep(2)
        print("\n发布测试消息...")
        result = client.publish("test/message", "Hello from Python client!")

        # 保持连接
        print("\n监听消息中...  (按 Ctrl+C 退出)")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n断开连接...")
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"\n✗ 错误: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Mosquitto MQTT 测试客户端')
    parser.add_argument('--host', default='127.0.0.1', help='MQTT broker 地址')
    parser.add_argument('--port', type=int, default=1883, help='端口号')
    parser.add_argument('--ssl', action='store_true', help='使用 SSL')
    parser.add_argument('--ca-cert', help='CA 证书路径')
    parser.add_argument('-u', '--username', default='test', help='用户名')
    parser.add_argument('-p', '--password', default='hut123456', help='密码')

    args = parser.parse_args()

    # SSL 端口默认为 8883
    port = args.port
    if args.ssl and port == 1883:
        port = 8883

    test_connection(
        args.host,
        port,
        args.username,
        args.password,
        args.ssl,
        args.ca_cert
    )