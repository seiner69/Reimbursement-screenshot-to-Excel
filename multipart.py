# -*- coding: utf-8 -*-
"""Multipart解析模块"""
import re
import logging

logger = logging.getLogger()


def parse_multipart(body, content_type):
    """解析multipart/form-data"""
    boundary_match = re.search(r'boundary=(.+)', content_type)
    if not boundary_match:
        logger.warning(f"未找到boundary: content_type={content_type}")
        return None, None

    boundary = boundary_match.group(1).strip()
    if isinstance(body, str):
        body = body.encode('utf-8')
    if isinstance(boundary, str):
        boundary = boundary.encode('utf-8')

    # 尝试多种分隔符组合
    sep_options = [
        (b'--' + boundary + b'\r\n', 'boundary+CRLF'),
        (b'--' + boundary, 'boundary'),
    ]

    parts = None
    for sep, name in sep_options:
        parts = body.split(sep)
        if len(parts) > 1:
            logger.info(f"使用 {name} 分割得到 {len(parts)} 个部分")
            break

    if parts is None or len(parts) <= 1:
        logger.warning(f"分割失败, body长度={len(body)}, boundary长度={len(boundary)}")

        # 尝试搜索图片
        return find_image_fallback(body)

    for i, part in enumerate(parts):
        if not part:
            continue
        if part == b'--' or part == b'--\r\n' or part == b'--\n':
            continue

        if part.startswith(b'\r\n'):
            part = part[2:]
        elif part.startswith(b'\n'):
            part = part[1:]

        # 查找header分隔
        header_end = -1
        for sep in [b'\r\n\r\n', b'\n\n', b'\r\n', b'\n']:
            if sep in part:
                header_end = part.index(sep)
                break

        if header_end > 0:
            header = part[:header_end].decode('utf-8', errors='ignore')
            sep_len = len(part[header_end:header_end+4]) if header_end + 4 <= len(part) else 2
            content = part[header_end + sep_len:]
        else:
            if len(part) > 100:
                if part[:2] in [b'\xff\xd8', b'\x89', b'BM']:
                    logger.info(f"part[{i}] 检测到图片: {part[:10].hex()}")
                    return part, 'image.jpg'
            continue

        if 'filename=' in header or 'name="image"' in header or 'name="file"' in header:
            logger.info(f"part[{i}] 找到图片字段")
            if len(content) > 100:
                logger.info(f"图片content长度={len(content)}")
                return content, 'image.jpg'

    logger.warning("未在multipart中找到图片")
    return find_image_fallback(body)


def find_image_fallback(body):
    """备用方案：直接搜索图片头"""
    logger.info("尝试备用方案：搜索图片头")

    # 找JPEG
    jpeg_idx = body.find(b'\xff\xd8')
    if jpeg_idx > 0:
        image_data = body[jpeg_idx:]
        end_idx = image_data.find(b'\xff\xd9')
        if end_idx > 0:
            image_data = image_data[:end_idx + 2]
            logger.info(f"JPEG找到，长度={len(image_data)}")
            return image_data, 'image.jpg'

    # 找PNG
    png_idx = body.find(b'\x89PNG\r\n\x1a\n')
    if png_idx > 0:
        logger.info(f"找到PNG")
        return body[png_idx:], 'image.jpg'

    # 找BMP
    bmp_idx = body.find(b'BM')
    while bmp_idx > 0:
        if len(body) >= bmp_idx + 14:
            file_size = int.from_bytes(body[bmp_idx+2:bmp_idx+6], 'little')
            data_offset = int.from_bytes(body[bmp_idx+10:bmp_idx+14], 'little')
            if (1000 < file_size < 10000000 and
                50 < data_offset < 100000 and
                file_size <= len(body) - bmp_idx):
                image_data = body[bmp_idx:bmp_idx + file_size]
                logger.info(f"BMP验证成功，长度={len(image_data)}")
                return image_data, 'image.jpg'
        bmp_idx = body.find(b'BM', bmp_idx + 1)

    logger.warning("未找到有效图片")
    return None, None
