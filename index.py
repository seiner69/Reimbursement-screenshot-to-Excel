# -*- coding: utf-8 -*-
"""
阿里云FC 3.0 - 报销截图转Excel API (支持批量多线程并发)
"""

import os
import sys
import json
import base64
import logging
import uuid
import concurrent.futures
import time
sys.path.insert(0, os.path.dirname(__file__))

from ocr import call_ocr
from deepseek import extract_info
from excel import create_excel
from oss import upload_oss

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def process_single_image(img_b64):
    """处理单张图片"""
    # 关键：第三方免费 API 严禁高频，强制每张图处理前歇一歇
    import time
    time.sleep(2) 

    try:
        # 1. 调用你刚写好的第三方 OCR
        ocr_result = call_ocr(img_b64)
        
        # 2. 【核心】解析 OCR.space 特有的数据结构
        raw_text = ""
        if ocr_result and 'ParsedResults' in ocr_result:
            results = ocr_result.get('ParsedResults', [])
            if results:
                raw_text = results[0].get('ParsedText', '')
        
        # 3. 容错处理：如果 API 返回了错误消息
        if not raw_text:
            err_msg = ocr_result.get('ErrorMessage', '未知错误')
            if isinstance(err_msg, list): err_msg = err_msg[0]
            raise Exception(f"API未识别到文字: {err_msg}")

        # 4. 将文字交给 DeepSeek 处理
        info = extract_info(raw_text)
        # ... 后续逻辑不变 ...
        return info

    except Exception as e:
        # 报错信息会直接显示在 Excel 里
        return {'date': '识别失败', 'amount': 0, 'merchant': str(e), 'item': 'API异常', 'order_id': ''}
        
def handle_upload(body_bytes, content_type):
    """处理并发任务"""
    if not body_bytes:
        return {'statusCode': 400, 'body': json.dumps({'error': 'FC 收到的请求体为空，解析被拦截'})}

    try:
        request_data = json.loads(body_bytes.decode('utf-8'))
        
        # 兼容老版和新版前端
        images = request_data.get('images', [])
        if not images and request_data.get('image'):
            images = [request_data['image']]

        if not images:
            return {'statusCode': 400, 'body': '{"error": "未找到图片数据"}'}

        logger.info(f"🚀 开始并发处理，共收到 {len(images)} 张图片")
        data_list = []

        # 4. 多线程并发调度（5图齐开）
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            results = list(executor.map(process_single_image, images))
            data_list.extend(results)

        # 5. 打包 Excel 并上传
        tmp_dir = '/tmp' if os.path.exists('/tmp') else os.path.dirname(__file__)
        excel_path = os.path.join(tmp_dir, f'reimburse_batch_{uuid.uuid4().hex}.xlsx')
        create_excel(data_list, excel_path)
        oss_url = upload_oss(excel_path)

        # 6. 清理服务器垃圾
        try:
            os.remove(excel_path)
            for d in data_list:
                if d.get('image_path') and os.path.exists(d['image_path']):
                    os.remove(d['image_path'])
        except:
            pass

        return {'statusCode': 200, 'body': json.dumps({'status': 'ok', 'download_url': oss_url, 'count': len(data_list)})}

    except Exception as e:
        import traceback
        logger.error(f"批量处理崩溃: {traceback.format_exc()}")
        return {'statusCode': 500, 'body': json.dumps({'error': f'处理失败: {str(e)}'})}

def handler(event, context):
    """最外层 HTTP 触发器，完美兼容所有数据类型"""
    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With'
    }

    try:
        # 核心修复：精准识别字典、字节和字符串类型
        if isinstance(event, dict):
            event_dict = event
        elif isinstance(event, bytes):
            try:
                event_dict = json.loads(event.decode('utf-8', errors='ignore'))
            except Exception:
                event_dict = {}
        elif isinstance(event, str):
            try:
                event_dict = json.loads(event)
            except Exception:
                event_dict = {}
        else:
            event_dict = {}

        http_method = event_dict.get('httpMethod')
        if not http_method:
            http_method = event_dict.get('requestContext', {}).get('http', {}).get('method', 'POST')
        http_method = http_method.upper()

        if http_method == 'OPTIONS':
            return {'statusCode': 200, 'headers': cors_headers, 'body': ''}

        # 提取真实的图片流数据
        if 'httpMethod' in event_dict or 'requestContext' in event_dict:
            raw_body = event_dict.get('body', '')
            if event_dict.get('isBase64Encoded'):
                body_bytes = base64.b64decode(raw_body)
            else:
                body_bytes = raw_body.encode('utf-8') if isinstance(raw_body, str) else b''
        else:
            # 极端情况：FC 直接透传数据
            if isinstance(event, bytes):
                body_bytes = event
            elif isinstance(event, str):
                body_bytes = event.encode('utf-8')
            else:
                body_bytes = json.dumps(event).encode('utf-8')

        if http_method == 'POST':
            res_dict = handle_upload(body_bytes, 'application/json')
            return {
                'statusCode': res_dict.get('statusCode', 200),
                'headers': cors_headers,
                'body': res_dict.get('body', '{}'),
                'isBase64Encoded': False
            }

        return {'statusCode': 200, 'headers': cors_headers, 'body': '{"status": "API is running!"}'}

    except Exception as e:
        return {'statusCode': 500, 'headers': cors_headers, 'body': f'{{"error": "系统解析异常: {str(e)}" }}'}