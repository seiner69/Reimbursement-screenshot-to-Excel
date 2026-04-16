# -*- coding: utf-8 -*-
"""Excel模块"""
import os
import xlsxwriter
from PIL import Image


def create_excel(data_list, output_path):
    """创建带图片的Excel"""
    workbook = xlsxwriter.Workbook(output_path)
    ws = workbook.add_worksheet()

    header_fmt = workbook.add_format({
        'bold': True, 'bg_color': '#4472C4', 'font_color': 'white',
        'align': 'center', 'valign': 'vcenter', 'border': 1
    })

    headers = ['支付日期', '金额', '收款方', '商品描述', '交易单号', '截图']
    for col, h in enumerate(headers):
        ws.write(0, col, h, header_fmt)

    ws.set_column('A:A', 12)
    ws.set_column('B:B', 10)
    ws.set_column('C:C', 35)
    ws.set_column('D:D', 35)
    ws.set_column('E:E', 25)
    ws.set_column('F:F', 20)

    for row_idx, data in enumerate(data_list, start=1):
        ws.write(row_idx, 0, str(data.get('date', '')))
        ws.write(row_idx, 1, str(data.get('amount', '')))
        ws.write(row_idx, 2, str(data.get('merchant', '')))
        ws.write(row_idx, 3, str(data.get('item', '')))
        ws.write(row_idx, 4, str(data.get('order_id', '')))

        img_path = data.get('image_path')
        if img_path and os.path.exists(img_path):
            try:
                img = Image.open(img_path)
                w, h = img.size
                scale = min(150 / w, 100 / h, 1)
                new_h = int(h * scale)
                ws.set_row(row_idx, new_h)
                ws.insert_image(row_idx, 5, img_path, {
                    'x_scale': scale, 'y_scale': scale,
                    'x_offset': 0, 'y_offset': 0,
                    'object_position': 1
                })
            except:
                pass

    workbook.close()
