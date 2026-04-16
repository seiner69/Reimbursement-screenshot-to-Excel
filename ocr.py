# -*- coding: utf-8 -*-
import json
import urllib.request
import urllib.parse
import os

def call_ocr(image_base64):
    """调用 OCR.space API (极限兼容版)"""
    # 优先从环境变量拿 Key，没有就用默认的
    api_key = os.environ.get('OCR_SPACE_API_KEY', 'helloworld')
    url = 'https://api.ocr.space/parse/image'
    
    # 1. 彻底清理 Base64，只要核心编码
    clean_b64 = image_base64
    if ',' in image_base64:
        clean_b64 = image_base64.split(',')[-1]
    
    # 2. 构造符合官方要求的 DataURL 格式
    # 注意：参数名必须是全小写 base64image
    payload = {
        'apikey': api_key,
        'base64image': f'data:image/jpg;base64,{clean_b64}',
        'language': 'chs',
        'isOverlayRequired': 'false',
        'OCREngine': '2',
        'scale': 'true'
    }
    
    # 3. 转换为标准的 Form-Data 格式
    encoded_data = urllib.parse.urlencode(payload).encode('utf-8')
    
    req = urllib.request.Request(url, data=encoded_data, method='POST')
    # 核心：必须声明这个 Content-Type，否则对方收不到参数
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')

    try:
        resp = urllib.request.urlopen(req, timeout=40)
        result = json.loads(resp.read().decode('utf-8'))
        
        # 4. 解析结果
        if result.get('OCRExitCode') == 1:
            full_text = ""
            parsed_results = result.get('ParsedResults', [])
            if parsed_results:
                full_text = parsed_results[0].get('ParsedText', '')
            
            # 返回 index.py 需要的格式
            return {'text': full_text, 'prism_wordsInfo': [{'text': full_text}]}
        else:
            # 捕获对方返回的真实错误信息
            err = result.get('ErrorMessage', 'API内部解析失败')
            if isinstance(err, list): err = err[0]
            raise Exception(err)
            
    except Exception as e:
        raise Exception(f"OCR请求异常: {str(e)}")