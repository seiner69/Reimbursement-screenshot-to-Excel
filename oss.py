# -*- coding: utf-8 -*-
"""OSS模块 (带强签名校验，北京节点专属版)"""
import os
import uuid
import time
import base64
import hmac
import hashlib
import urllib.request
import urllib.error
from email.utils import formatdate
import logging

def get_env(key, default=None):
    return os.environ.get(key, default)

# 1. 暴力写死 Bucket 配置（防止读取错乱）
OSS_ACCESS_KEY_ID = get_env('OSS_ACCESS_KEY_ID')          # 必须在环境变量中配置好
OSS_ACCESS_KEY_SECRET = get_env('OSS_ACCESS_KEY_SECRET')  # 必须在环境变量中配置好
OSS_BUCKET_NAME = 'bucket673'
OSS_ENDPOINT = 'oss-cn-beijing.aliyuncs.com'

def upload_oss(file_path, oss_key=None):
    """带原生 HMAC 签名的 OSS 上传"""
    if not OSS_ACCESS_KEY_ID or not OSS_ACCESS_KEY_SECRET:
        raise Exception("AccessKey 缺失！请检查 FC 环境变量")

    if not oss_key:
        oss_key = f'reimburse/{uuid.uuid4().hex}.xlsx'

    with open(file_path, 'rb') as f:
        file_data = f.read()

    # 2. 准备请求头必须的参数
    date_str = formatdate(time.time(), usegmt=True)
    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    # 3. 构造阿里云规定的签名字符串 (StringToSign)
    string_to_sign = f"PUT\n\n{content_type}\n{date_str}\n/{OSS_BUCKET_NAME}/{oss_key}"
    
    # 4. 计算 HMAC-SHA1 签名（没有这个通行证，OSS 绝对不会让你上传）
    h = hmac.new(OSS_ACCESS_KEY_SECRET.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha1)
    signature = base64.b64encode(h.digest()).decode('utf-8')
    auth_header = f"OSS {OSS_ACCESS_KEY_ID}:{signature}"

    # 5. 发起带有身份验证的公网上传请求
    upload_url = f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}/{oss_key}"
    req = urllib.request.Request(upload_url, data=file_data, method='PUT')
    req.add_header('Date', date_str)
    req.add_header('Content-Type', content_type)
    req.add_header('Authorization', auth_header) # 塞入通行证

    # 6. 严格执行并捕获真实错误
    try:
        logging.info(f"正在上传至北京 OSS: {upload_url}")
        urllib.request.urlopen(req, timeout=30)
        logging.info("OSS 文件写入成功！")
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        logging.error(f"OSS 拒绝了上传: {err_msg}")
        raise Exception(f"OSS 上传被拒绝，请确认北京的 bucket673 权限是否正确: {e.code}")
    except Exception as e:
        logging.error(f"网络异常: {e}")
        raise Exception(f"上传 OSS 失败: {e}")

    # 上传成功后，直接返回这个公网地址给前端
    return upload_url