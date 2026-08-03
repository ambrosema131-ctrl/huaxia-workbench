#!/usr/bin/env python3
"""创建品牌市场部工作台智能表格"""
import json
import subprocess
import sys
import os

SKILL_DIR = "/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/resources/builtin-plugins/tencent-docs-plugin/skills/tencent-docs"
PYTHON = sys.executable

def tdoc_call(service, tool, args):
    """调用腾讯文档 MCP 工具"""
    cmd = [PYTHON, "tencentdocs.py", "tdoc_call", service, tool, json.dumps(args, ensure_ascii=False)]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=SKILL_DIR)
    try:
        data = json.loads(result.stdout)
        if "error" in data:
            print(f"ERROR: {json.dumps(data['error'], ensure_ascii=False, indent=2)}")
            return None
        return data.get("result")
    except:
        print(f"RAW: {result.stdout[:500]}")
        return None

def extract_content(result):
    """从 MCP 返回中提取 content 文本"""
    if not result:
        return None
    contents = result.get("content", [])
    for c in contents:
        if c.get("type") == "text":
            try:
                return json.loads(c["text"])
            except:
                return c["text"]
    return result

# ===== Step 1: 创建智能表格文件 =====
print("=" * 60)
print("Step 1: 创建智能表格文件...")
result = tdoc_call("tencent-docs", "manage.create_file", {
    "title": "品牌市场部工作台",
    "file_type": "smartsheet"
})
data = extract_content(result)
if not data:
    print("创建失败，退出")
    sys.exit(1)

print(f"创建结果: {json.dumps(data, ensure_ascii=False, indent=2)}")

# 从返回中提取 file_id
file_id = data.get("file_id") or data.get("docid") or data.get("id")
if not file_id:
    # 尝试从 url 中提取
    url = data.get("url", "")
    print(f"URL: {url}")
    # 从 URL 提取 file_id
    import re
    m = re.search(r'/smartsheet/([A-Za-z0-9_]+)', url)
    if m:
        file_id = m.group(1)
    else:
        # 尝试其他格式
        for key in data:
            val = str(data[key])
            if len(val) > 10 and val.startswith(('e', 'w', 'f')):
                file_id = val
                break

if not file_id:
    print(f"无法提取 file_id，完整返回: {json.dumps(data, ensure_ascii=False)}")
    sys.exit(1)

print(f"file_id: {file_id}")

# ===== Step 2: 获取默认工作表 ID =====
print("\n" + "=" * 60)
print("Step 2: 获取工作表 ID...")
result = tdoc_call("tencent-docs", "smartsheet.list_tables", {"file_id": file_id})
data = extract_content(result)
if not data:
    print("获取工作表失败")
    sys.exit(1)

sheets = data.get("sheets", [])
if not sheets:
    print(f"没有工作表: {json.dumps(data, ensure_ascii=False)}")
    sys.exit(1)

sheet_id = sheets[0]["sheet_id"]
print(f"sheet_id: {sheet_id}")
print(f"工作表名: {sheets[0].get('title', '')}")

# ===== Step 3: 添加字段 =====
print("\n" + "=" * 60)
print("Step 3: 添加字段...")

fields = [
    {
        "field_title": "工作线",
        "field_type": "singleSelect",
        "property_select": {
            "options": [
                {"name": "ToB品牌宣传", "style": "3"},
                {"name": "ToC品牌宣传", "style": "4"},
                {"name": "现场体验优化", "style": "2"},
                {"name": "创新业务拓展", "style": "6"},
                {"name": "自媒体与内容", "style": "5"},
                {"name": "达人BD", "style": "2"},
                {"name": "城市运营", "style": "4"},
                {"name": "新媒体投放", "style": "1"},
            ]
        }
    },
    {
        "field_title": "事项",
        "field_type": "text"
    },
    {
        "field_title": "负责人",
        "field_type": "singleSelect",
        "property_select": {
            "options": [
                {"name": "马龙", "style": "8"},
                {"name": "范振", "style": "3"},
                {"name": "潘科元", "style": "5"},
                {"name": "江波", "style": "4"},
                {"name": "刘永芳", "style": "2"},
                {"name": "宇豪", "style": "6"},
                {"name": "薛易", "style": "4"},
                {"name": "吴姬睿", "style": "2"},
                {"name": "白子琦", "style": "1"},
                {"name": "马乐", "style": "5"},
            ]
        }
    },
    {
        "field_title": "状态",
        "field_type": "singleSelect",
        "property_select": {
            "options": [
                {"name": "待启动", "style": "7"},
                {"name": "进行中", "style": "3"},
                {"name": "已完成", "style": "4"},
                {"name": "阻塞", "style": "1"},
            ]
        }
    },
    {
        "field_title": "进度",
        "field_type": "percentage"
    },
    {
        "field_title": "描述",
        "field_type": "text"
    },
    {
        "field_title": "交付文档",
        "field_type": "url"
    },
    {
        "field_title": "截止时间",
        "field_type": "dateTime",
        "property_date_time": {"format": "yyyy-mm-dd"}
    },
]

result = tdoc_call("tencent-docs", "smartsheet.add_fields", {
    "file_id": file_id,
    "sheet_id": sheet_id,
    "fields": fields
})
data = extract_content(result)
print(f"字段添加结果: {json.dumps(data, ensure_ascii=False, indent=2) if data else '失败'}")

# ===== Step 4: 添加记录 =====
print("\n" + "=" * 60)
print("Step 4: 添加记录...")

# 项目数据
tasks = [
    {"wl": "ToB品牌宣传", "title": "华墨·华夏家博会总裁培训PPT", "assignee": "范振", "status": "进行中", "progress": 70, "desc": "已完成PPT初稿，计划4.20完成PPT设计深化定稿", "doc_name": "总裁培训课件4.20.pptx", "doc_url": "https://drive.weixin.qq.com/s?k=ALEAaAe2AA0wHVAWN4AQ0ANAadANc", "deadline": "2026-04-20"},
    {"wl": "ToB品牌宣传", "title": "TOB内容项目跟进落地（招商函制作、H5制作）", "assignee": "潘科元", "status": "进行中", "progress": 50, "desc": "已完成内容并下brief给设计", "doc_name": "TOB内容资料_0710.pptx", "doc_url": "https://drive.weixin.qq.com/s?k=ALEAaAe2AA0D0YzZVpAaoA6wZnALA", "deadline": "2026-04-15"},
    {"wl": "ToB品牌宣传", "title": "部分城市异业合作和地推", "assignee": "宇豪", "status": "进行中", "progress": 30, "desc": "沟通中", "doc_name": "", "doc_url": "", "deadline": "2026-05-01"},
    {"wl": "ToC品牌宣传", "title": "全国活动方案库", "assignee": "刘永芳", "status": "进行中", "progress": 60, "desc": "持续完善中", "doc_name": "2026全国活动方案库", "doc_url": "https://doc.weixin.qq.com/sheet/e3_AfQADgYdAKkCNd5EOwdkZSdCFJJDU?scode=ALEAaAe2AA02W0CyL9AfQADgYdAKk&tab=BB08J2", "deadline": "2026-12-31"},
    {"wl": "ToC品牌宣传", "title": "Q3营销主题选题选定", "assignee": "马龙", "status": "已完成", "progress": 100, "desc": "已完成", "doc_name": "2026营销主题-选题库", "doc_url": "https://doc.weixin.qq.com/sheet/e3_AZoAOQZQAOACNNqHN4WwzTny6sYZn?scode=ALEAaAe2AA07GZuE3CAfQADgYdAKk&tab=BB08J2", "deadline": "2026-03-20"},
    {"wl": "ToC品牌宣传", "title": "Q3线上线下物料", "assignee": "范振", "status": "已完成", "progress": 100, "desc": "已完成", "doc_name": "Q3季度-营销物料合集", "doc_url": "https://doc.weixin.qq.com/sheet/e3_AZoAOQZQAOACNLeIg0GHfRPyWHijm?scode=ALEAaAe2AA0LDYsJFSAfQADgYdAKk&tab=d5z1x0", "deadline": "2026-03-25"},
    {"wl": "ToC品牌宣传", "title": "福州创新活动方案", "assignee": "刘永芳", "status": "进行中", "progress": 40, "desc": "初稿，内容共识中。案例落地", "doc_name": "福州活动方案", "doc_url": "https://doc.weixin.qq.com/doc/w3_AfQADgYdAKkCNaprwmZWjQkSijMtE?scode=ALEAaAe2AA000QGQLmAfQADgYdAKk", "deadline": "2026-04-30"},
    {"wl": "ToC品牌宣传", "title": "交付流程SOP", "assignee": "刘永芳", "status": "已完成", "progress": 100, "desc": "已完成3.0版本", "doc_name": "展会交付流程3.0", "doc_url": "https://doc.weixin.qq.com/flowchart/f4_AfQADgYdAKkCNPlHQRihTRgKWE5KD?scode=ALEAaAe2AA0s6y5inXAfQADgYdAKk", "deadline": "2026-03-28"},
    {"wl": "现场体验优化", "title": "展会品牌物料升级模板", "assignee": "范振", "status": "已完成", "progress": 100, "desc": "已完成1.0版本交付", "doc_name": "2026年营销物料合集", "doc_url": "https://doc.weixin.qq.com/sheet/e3_AZoAOQZQAOACNJc0r1lTNTRSpgFou?scode=ALEAaAe2AA0VDtirYk", "deadline": "2026-03-30"},
    {"wl": "现场体验优化", "title": "各部门设计需求", "assignee": "潘科元", "status": "进行中", "progress": 50, "desc": "持续制作需求", "doc_name": "2026品牌市场部-需求提交表", "doc_url": "https://doc.weixin.qq.com/sheet/e3_AZoAOQZQAOACNAw7MB6sfR5mtkPlQ?scode=ALEAaAe2AA0yZFSLq8ARYADwYdAKk&tab=BB08J2", "deadline": "2026-12-31"},
    {"wl": "自媒体与内容", "title": "开展宣传PR新闻稿发布", "assignee": "白子琦", "status": "进行中", "progress": 60, "desc": "3月27-29日稿件已发布（10×6篇）", "doc_name": "KA自媒体交付内容-确认表", "doc_url": "https://doc.weixin.qq.com/sheet/e3_AUIAigZ6AGYCNVFDMJVCVR1iSynav?scode=ALEAaAe2AA0YashKjjAUIAigZ6AGY&tab=BB08J2", "deadline": "2026-12-31"},
    {"wl": "自媒体与内容", "title": "账号视觉统一（头像/背景图/简介/菜单栏）", "assignee": "白子琦", "status": "已完成", "progress": 100, "desc": "头像已更新", "doc_name": "自媒体账号基础信息", "doc_url": "https://doc.weixin.qq.com/sheet/e3_AdMADgYdAKkiGeLvGLgQMqa05W38B?scode=ALEAaAe2AA0oNTyLWB", "deadline": "2026-03-15"},
    {"wl": "自媒体与内容", "title": "内容方向与发布节奏调整", "assignee": "白子琦", "status": "进行中", "progress": 70, "desc": "4月10-12日开展内容收集下发，每个城市发布12-15条", "doc_name": "全国自媒体账号数据统计（月度）", "doc_url": "https://doc.weixin.qq.com/sheet/e3_AUIAigZ6AGYCNCMTyM1b8ReqdLy80?scode=ALEAaAe2AA0083AsbvAUIAigZ6AGY&tab=f4yu5z", "deadline": "2026-04-12"},
    {"wl": "自媒体与内容", "title": "新媒体常规事项+创新项目（抖音电商）", "assignee": "薛易", "status": "进行中", "progress": 40, "desc": "抖音项目还在跟进", "doc_name": "新媒体工作文件总目录", "doc_url": "https://doc.weixin.qq.com/sheet/e3_AYAAigb_AL0CNaxrxBBZdQTuoujYy?scode=ALEAaAe2AA0SV9EqdMAYAAigb_AL0&tab=BB08J2", "deadline": "2026-12-31"},
    {"wl": "创新业务拓展", "title": "可置换资源盘点", "assignee": "薛易", "status": "已完成", "progress": 100, "desc": "已完成2025年异业合作盘点", "doc_name": "华夏家博会异业合作规划", "doc_url": "https://doc.weixin.qq.com/doc/w3_AQ0ANAadANcCN07ECtKSzQq6LhO0M?scode=ALEAaAe2AA0ppMDVA4", "deadline": "2026-03-20"},
    {"wl": "创新业务拓展", "title": "合作接触与洽谈（滴滴/天鹅到家/可口可乐）", "assignee": "薛易", "status": "进行中", "progress": 50, "desc": "已对接滴滴打车、天鹅到家、可口可乐", "doc_name": "异业合作信息表", "doc_url": "https://doc.weixin.qq.com/sheet/e3_AQ0ANAadANcCNDuVf00iyReyjeayt?scode=ALEAaAe2AA0pjE5gsV", "deadline": "2026-05-15"},
    {"wl": "达人BD", "title": "达人资源库建设与分级管理", "assignee": "吴姬睿", "status": "进行中", "progress": 45, "desc": "家居/生活方式类达人资源库搭建中，已收录120+达人", "doc_name": "", "doc_url": "", "deadline": "2026-04-30"},
    {"wl": "达人BD", "title": "展会达人合作内容策划", "assignee": "吴姬睿", "status": "进行中", "progress": 30, "desc": "Q3展会达人探展内容策划，覆盖小红书+抖音双平台", "doc_name": "", "doc_url": "", "deadline": "2026-05-01"},
    {"wl": "城市运营", "title": "全国城市线下活动方案标准化", "assignee": "宇豪", "status": "进行中", "progress": 55, "desc": "活动方案模板1.0已完成，正在2个城市试点", "doc_name": "", "doc_url": "", "deadline": "2026-04-20"},
    {"wl": "城市运营", "title": "城市运营活动落地支持", "assignee": "刘永芳", "status": "进行中", "progress": 60, "desc": "宁波展复盘、福州活动跟进、苏州出差调研", "doc_name": "", "doc_url": "", "deadline": "2026-12-31"},
    {"wl": "新媒体投放", "title": "Q3新媒体投放策略制定", "assignee": "马乐", "status": "进行中", "progress": 50, "desc": "小红书+抖音+朋友圈投放策略制定中", "doc_name": "", "doc_url": "", "deadline": "2026-04-15"},
    {"wl": "新媒体投放", "title": "投放素材制作与效果监测", "assignee": "马乐", "status": "进行中", "progress": 40, "desc": "朋友圈九宫格投放素材制作中，ROI监测体系搭建", "doc_name": "", "doc_url": "", "deadline": "2026-04-20"},
]

import time
from datetime import datetime

def date_to_timestamp(date_str):
    """将日期字符串转为毫秒级时间戳"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return str(int(dt.timestamp() * 1000))
    except:
        return ""

records = []
for task in tasks:
    field_values = [
        {"field": "工作线", "option_value": {"items": [{"text": task["wl"]}]}},
        {"field": "事项", "text_value": {"items": [{"text": task["title"], "type": "text"}]}},
        {"field": "负责人", "option_value": {"items": [{"text": task["assignee"]}]}},
        {"field": "状态", "option_value": {"items": [{"text": task["status"]}]}},
        {"field": "进度", "number_value": task["progress"]},
        {"field": "描述", "text_value": {"items": [{"text": task["desc"], "type": "text"}]}},
    ]
    if task["doc_url"]:
        field_values.append({"field": "交付文档", "url_value": {"items": [{"text": task["doc_name"], "link": task["doc_url"], "type": "url"}]}})
    else:
        field_values.append({"field": "交付文档", "text_value": {"items": [{"text": "", "type": "text"}]}})
    
    ts = date_to_timestamp(task["deadline"])
    field_values.append({"field": "截止时间", "string_value": ts})
    
    records.append({"field_values": field_values})

result = tdoc_call("tencent-docs", "smartsheet.add_records", {
    "file_id": file_id,
    "sheet_id": sheet_id,
    "records": records
})
data = extract_content(result)
print(f"记录添加结果: {json.dumps(data, ensure_ascii=False, indent=2) if data else '失败'}")

# ===== Step 5: 添加看板视图 =====
print("\n" + "=" * 60)
print("Step 5: 添加看板视图...")
result = tdoc_call("tencent-docs", "smartsheet.add_view", {
    "file_id": file_id,
    "sheet_id": sheet_id,
    "view_title": "项目看板",
    "view_type": "kanban"
})
data = extract_content(result)
print(f"看板视图添加结果: {json.dumps(data, ensure_ascii=False, indent=2) if data else '失败'}")

# ===== 输出最终信息 =====
print("\n" + "=" * 60)
print("完成！")
print(f"file_id: {file_id}")
print(f"sheet_id: {sheet_id}")
