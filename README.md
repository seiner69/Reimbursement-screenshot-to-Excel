# 报销截图转Excel - 阿里云FC版（网页工具）

通过网页上传报销截图，自动识别并生成带图片的Excel表格。

## 功能

- **网页上传**：通过浏览器直接上传图片
- **OCR识别**：调用OCR.space免费API
- **信息提取**：调用DeepSeek API提取财务信息
- **物理嵌入图片**：Excel包含原始截图，离线可查看
- **OSS存储**：生成下载链接

## 项目结构

```
报销截图FC/
├── index.py          # 主程序入口
├── requirements.txt # Python依赖
├── s.yml            # FC配置
└── README.md        # 说明文档
```

## 部署步骤

### 1. 安装依赖

```bash
cd 报销截图FC
pip install -t . xlsxwriter
pip install -t . Pillow
```

### 2. 配置环境变量

| 环境变量 | 说明 |
|---------|------|
| DEEPSEEK_API_KEY | DeepSeek API Key |
| OSS_ACCESS_KEY_ID | OSS AccessKey ID |
| OSS_BUCKET_NAME | OSS Bucket名称 |
| OSS_ENDPOINT | OSS Endpoint |
| OCR_SPACE_API_KEY | OCR.space API Key (可选，默认helloworld) |

### 3. 部署

将整个文件夹打包为ZIP，上传到FC控制台。

### 4. 配置HTTP触发器

在FC控制台为函数添加「HTTP触发器」：
- 勾选「启用GET」和「POST」
- 勾选「响应HTML」

## OSS权限配置

上传Excel需要OSS Bucket有以下配置之一：

**方案1：公共读权限**
- 在OSS控制台设置Bucket ACL为「公共读」

**方案2：使用RAM用户**
- 配置具有OSS写入权限的RAM用户

## 使用方法

1. 访问函数URL
2. 上传报销截图（PNG/JPG）
3. 点击「开始处理」
4. 点击下载链接获取Excel

## 核心特性

- **无需企业微信**：直接在网页使用
- **物理嵌入图片**：Excel文件本身包含图片数据
- **Serverless**：按量收费