import sys
import asyncio

# 如果是在 Windows 平台上运行，则设置事件循环策略为 SelectorEventLoopPolicy
# 这是为了避免在 Windows 上运行 asyncio 时可能出现的问题
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import collections  # 用于词频统计
import json  # 用于处理 JSON 数据
import aiohttp  # 用于异步 HTTP 请求
import asyncio  # 用于异步操作
import re  # 正则表达式模块，用于解析弹幕
import openpyxl  # 用于处理 Excel 文件
import pandas as pd  # 用于数据处理
import cProfile  # 用于性能分析

# 创建性能分析器实例，并开始性能分析
profile = cProfile.Profile()
profile.enable()

# 定义开始和结束日期，用于生成日期范围（虽然在代码中未使用此变量）
startdate = '2024-07-10'
enddate = '2024-09-10'
# 生成日期列表，格式为 'YYYY-MM-DD'
date = [x for x in pd.date_range(startdate, enddate).strftime('%Y-%m-%d')]

# 定义 Excel 文件名，用于保存弹幕数据
file_xlsx = '我的全部弹幕.xlsx'

# 创建一个新的 Excel 工作簿和工作表，并添加标题行 '弹幕'
total_workbook = openpyxl.Workbook()
total_sheet = total_workbook.active
total_sheet.append(['弹幕'])

# 定义 B 站弹幕 API 的基础 URL，其中 {number} 是占位符，用于填充视频的 cid 号
tempApi = 'https://api.bilibili.com/x/v1/dm/list.so?oid={number}'

# 定义请求头，包含 cookie 和 user-agent，用于伪装请求
headers = {
    'cookie': "您的 B 站 Cookie 值",
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."
}

# 全局缓存，用于存储 bvid 和 cid，避免重复请求
bvid_cache = {}
cid_cache = {}

# 异步函数：获取 bvid，带缓存功能
async def get_bvid(session, page, index):
    # 如果已经在缓存中，则直接返回缓存的 bvid
    if (page, index) in bvid_cache:
        return bvid_cache[(page, index)]
    
    # 构造 API 请求的 URL，查询指定页码和关键字的视频
    url = f'https://api.bilibili.com/x/web-interface/search/type?page={page}&page_size=50&keyword=2024%E5%B7%B4%E9%BB%8E%E5%A5%A5%E8%BF%90%E4%BC%9A&search_type=video'
    
    # 发送异步 GET 请求
    async with session.get(url) as response:
        try:
            # 尝试将响应内容解析为 JSON 格式
            json_data = await response.json()
            # 提取第 index 个视频的 bvid
            bvid = json_data['data']['result'][index]['bvid']
            # 将 bvid 存入缓存
            bvid_cache[(page, index)] = bvid
            return bvid
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            # 如果出现异常，打印错误信息和响应内容，返回 None
            print(f"获取 bvid 时出错: {e}")
            print(f"响应状态码: {response.status}")
            text = await response.text()
            print(f"响应内容: {text}")
            return None

# 异步函数：获取 cid，带缓存功能
async def get_cid(session, bvid):
    # 如果 bvid 已经在缓存中，则直接返回缓存的 cid
    if bvid in cid_cache:
        return cid_cache[bvid]
    
    # 构造 API 请求的 URL，查询指定 bvid 的视频信息
    url = f'https://api.bilibili.com/x/player/pagelist?bvid={bvid}&jsonp=jsonp'
    
    # 发送异步 GET 请求
    async with session.get(url) as response:
        try:
            # 尝试将响应内容解析为 JSON 格式
            json_dict = await response.json()
            # 提取第一个视频的 cid
            cid = json_dict['data'][0]['cid']
            # 将 cid 存入缓存
            cid_cache[bvid] = cid
            return cid
        except (KeyError, IndexError, json.JSONDecodeError):
            # 如果出现异常，返回 None
            return None

# 异步函数：获取并保存某个视频的弹幕
async def fetch_and_save_bulletchat(session, cid):
    # 使用 cid 构造弹幕 API 的 URL
    url = tempApi.replace("{number}", str(cid))
    try:
        # 发送异步 GET 请求
        async with session.get(url) as response:
            # 获取响应的文本内容（XML 格式）
            response_text = await response.text()
            # 使用正则表达式提取所有弹幕内容
            data = re.findall('<d p=".*?">(.*?)</d>', response_text)
            # 如果有弹幕数据，返回列表，否则返回空列表
            return data if data else []
    except:
        # 如果出现异常，返回空列表
        return []

# 异步函数：处理并发任务，收集所有弹幕数据
async def fetch_all_bulletchats(session):
    all_bulletchats = []  # 用于存储所有的弹幕数据
    tasks = []  # 用于存储所有的异步任务

    total_requests = 6 * 50  # 总共请求 6 页，每页 50 个视频，共 300 个视频
    for i in range(total_requests):
        page_number = i // 50 + 1  # 计算当前请求的页码
        index = i % 50  # 计算当前页内的索引
        # 创建异步任务，获取每个视频的弹幕数据
        tasks.append(asyncio.ensure_future(fetch_bulletchat_data(session, page_number, index)))
    
    # 使用 asyncio.as_completed 来迭代已完成的任务
    for task in asyncio.as_completed(tasks):
        bulletchat_data = await task
        if bulletchat_data:
            # 将获取的弹幕数据添加到总列表中
            all_bulletchats.extend(bulletchat_data)

    return all_bulletchats  # 返回所有的弹幕数据

# 异步函数：获取单个视频的弹幕数据
async def fetch_bulletchat_data(session, page_number, index):
    # 获取视频的 bvid
    bvid = await get_bvid(session, page_number, index)
    if bvid:
        # 获取视频的 cid
        cid = await get_cid(session, bvid)
        if cid:
            # 获取并返回视频的弹幕数据
            return await fetch_and_save_bulletchat(session, cid)
    return []  # 如果获取失败，返回空列表

# 函数：保存弹幕数据到文本文件和 Excel 文件
def save_to_file(bulletchats):
    # 以追加模式打开文本文件，编码为 utf-8
    with open('我的全部弹幕.txt', 'a', encoding='utf-8') as file_txt:
        for index in bulletchats:
            # 将每条弹幕写入文本文件，并换行
            file_txt.write(index + '\n')
            # 将弹幕写入 Excel 表格
            total_sheet.append([index])
    # 保存 Excel 文件
    total_workbook.save(file_xlsx)

# 函数：计算弹幕频次，并保存到 Excel 文件
def calculate_frequency():
    try:
        # 读取 Excel 文件中的弹幕数据
        fd = pd.read_excel(file_xlsx)
        lines = fd['弹幕']
        # 将所有弹幕拼接成一个字符串
        text = ' '.join(lines.astype(str))
        # 将字符串按照空格分割为单词列表
        words = text.split()
        # 使用 collections.Counter 统计词频
        word_counts = collections.Counter(words)
        # 将词频按照出现次数从高到低排序
        sorted_word_counts = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        # 创建一个新的 Excel 工作簿和工作表，并添加标题行
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.append(['弹幕', '频次'])
        
        # 将排序后的词频数据写入 Excel 表格
        for word, count in sorted_word_counts:
            sheet.append([word, count])
        
        # 保存统计结果到新的 Excel 文件
        workbook.save('我的统计弹幕出现次数.xlsx')
    except Exception as e:
        # 如果出现异常，打印错误信息
        print(f"计算频次时出错: {e}")

# 异步主函数，负责执行整个流程
async def main():
    # 创建一个异步的 HTTP 会话，使用指定的请求头
    async with aiohttp.ClientSession(headers=headers) as session:
        # 异步获取所有弹幕数据
        bulletchats = await fetch_all_bulletchats(session)
        # 保存弹幕数据到文件
        save_to_file(bulletchats)
        # 计算弹幕频次并保存结果
        calculate_frequency()
        # 输出流程结束信息
        print("Finished")

# 启动异步任务
if __name__ == '__main__':
    asyncio.run(main())

# 停止性能分析
profile.disable()
# 将性能分析数据保存到文件中
profile.dump_stats('./youhua.prof')
