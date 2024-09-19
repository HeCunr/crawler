import collections  # 用于词频统计
import json  # 用于处理JSON数据
import requests  # 用于发送HTTP请求
import re  # 正则表达式模块，用于解析弹幕
import time  # 用于时间相关操作
import openpyxl  # 用于处理Excel文件
import pandas as pd  # 用于数据处理
from concurrent.futures import ThreadPoolExecutor, as_completed  # 用于并发操作
import cProfile

profile = cProfile.Profile()
profile.enable()


# 定义开始和结束日期，用于生成日期范围
startdate = '20240710'
enddate = '20240910'
date = [x for x in pd.date_range(startdate, enddate).strftime('%Y-%m-%d')]  # 生成日期列表

# 定义Excel文件名，用于保存弹幕数据
file_xlsx = '我的全部弹幕.xlsx'

# 创建Excel工作簿和工作表，并添加标题行
total_workbook = openpyxl.Workbook()
total_sheet = total_workbook.active
total_sheet.append(['弹幕'])

# 定义B站弹幕API的基础URL，{number}是占位符，用于填充视频的cid号
tempApi = 'https://api.bilibili.com/x/v1/dm/list.so?oid={number}'

# 定义请求头，包含cookie和user-agent，用于伪装请求
headers = {        
    'cookie':"buvid3=D65868DE-AFD5-34A4-1714-A1C0F783C5DC27124infoc; b_nut=1725930527; _uuid=FF569C27-D2C6-10814-36A8-48AA8141364924857infoc; CURRENT_FNVAL=4048; buvid_fp=2ba89565eab107e1e14c7982fc1ef9ea; buvid4=FAB9A58B-B8F5-8DAF-2AC4-4E874D3D1F0E28371-024091001-a%2FA7nVxQVETBwJOeuHlVsQ%3D%3D; rpdid=|(u))kkYu|lu0J'u~klmJ|lkm; SESSDATA=e8f35e7e%2C1741482645%2Cb3572%2A91CjC7hBYEVq-d38AwweerB9sclbgqT78LR6aribbsaBRVlJ0BoUjCMidR-nm82eDlo70SVlVibjl1UnQ0Y0NzSFFCb21DRGNNSXp4YnRSbFdzMXo0NjR4QkM0TlBKejUweW1TbDJkT0g3Z2Z6bTdmQVJzdmpvVHZmR1JWOEhtbnFGZmpuQUt6WXZnIIEC; bili_jct=7d37b038ea7714a0c41ec3d26603737b; DedeUserID=1917958039; DedeUserID__ckMd5=eaa26b970b7e3104; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MjYxOTIwNTMsImlhdCI6MTcyNTkzMjc5MywicGx0IjotMX0.82V6_w7kGoSvzDy9rT-9DpsL7U_BrB24GefbBM0Vvb8; bili_ticket_expires=1726191993; header_theme_version=CLOSE; enable_web_push=DISABLE; home_feed_column=5; browser_resolution=1536-730; b_lsid=953CBCA8_191E441EE95; bp_t_offset_1917958039=976131738646347776; sid=hl295qcj",
    'user-agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

# 定义函数，获取搜索结果中的bvid（视频的唯一标识符）
def get_bvid(page_number, number):
    # 构造搜索API的URL，page_number是页码，number是该页中的视频编号
    url = f'https://api.bilibili.com/x/web-interface/search/type?page={page_number}&page_size=50&keyword=2024%E5%B7%B4%E9%BB%8E%E5%A5%A5%E8%BF%90%E4%BC%9A&search_type=video'
    response = requests.get(url=url, headers=headers)  # 发送请求
    try:
        # 解析返回的JSON数据，提取视频的bvid
        json_data = json.loads(response.text)
        print(json_data)
        bvid = json_data['data']['result'][number]['bvid']
        print(f"获取到bvid: {bvid}")
        return bvid  # 返回bvid
    except (KeyError, IndexError, json.JSONDecodeError, requests.RequestException) as e:
        print(f"获取bvid时出错: {e}")
        # 捕获错误并返回None，防止程序崩溃
        return None

# 定义函数，根据bvid获取视频的cid（弹幕对应的唯一标识符）
def get_cid(bvid):
    try:
        # 通过bvid构造获取cid的API请求URL
        url = f'https://api.bilibili.com/x/player/pagelist?bvid={bvid}&jsonp=jsonp'
        response = requests.get(url, headers=headers)  # 发送请求
        if response.status_code != 200:
            # 如果请求状态码不是200，返回None
            return None
        # 解析返回的JSON数据，提取cid
        json_dict = json.loads(response.text)
        return json_dict['data'][0]['cid']  # 返回cid
    except (KeyError, IndexError, json.JSONDecodeError, requests.RequestException):
        return None  # 捕获错误并返回None

# 定义函数，获取并保存某个视频的弹幕
def fetch_and_save_bulletchat(cid):
    # 用cid替换API中的占位符
    url = tempApi.replace("{number}", str(cid))
    try:
        # 发送请求获取弹幕数据
        response = requests.get(url, headers=headers)
        response.encoding = response.apparent_encoding  # 设置编码
        # 使用正则表达式解析弹幕内容
        data = re.findall('<d p=".*?">(.*?)</d>', response.text)
        if data:
            return data  # 返回弹幕列表
    except requests.RequestException:
        return []  # 如果请求失败，返回空列表

# 定义函数，批量获取bvid和cid，并创建并发任务
def put_api():
    tasks = []
    # 使用ThreadPoolExecutor创建线程池，用于并发请求
    with ThreadPoolExecutor(max_workers=10) as executor:
        # 控制页码范围（1到5页），每页50个视频
        for i in range(1, 7):
            for j in range(50):
                bvid = get_bvid(i, j)  # 获取bvid
                if bvid:
                    cid = get_cid(bvid)  # 获取cid
                    if cid:
                        # 提交弹幕抓取任务到线程池
                        tasks.append(executor.submit(fetch_and_save_bulletchat, cid))
    return tasks  # 返回任务列表

# 定义函数，处理并发任务，收集所有弹幕数据
def get_data(tasks):
    all_bulletchats = []
    # 遍历所有完成的任务，获取结果
    for task in as_completed(tasks):
        bulletchat_data = task.result()
        if bulletchat_data:
            all_bulletchats.extend(bulletchat_data)  # 将弹幕数据加入总列表
    return all_bulletchats  # 返回所有弹幕数据

# 定义函数，将弹幕数据保存到文件和Excel中
def save_to_file(bulletchats):
    # 打开文本文件，将弹幕逐行写入
    with open('我的全部弹幕.txt', 'a', encoding='utf-8') as file_txt:
        for index in bulletchats:
            file_txt.write(index + '\n')
            total_sheet.append([index])  # 将弹幕写入Excel表格
    total_workbook.save(file_xlsx)  # 保存Excel文件

# 定义函数，计算弹幕频次，并保存到Excel
def calculate_frequency():
    try:
        # 读取弹幕Excel文件
        fd = pd.read_excel(file_xlsx)
        lines = fd['弹幕']
        # 将所有弹幕拼接成一个字符串
        text = ' '.join(lines.astype(str))
        words = text.split()  # 将弹幕分割为单词
        word_counts = collections.Counter(words)  # 统计单词频次
        sorted_word_counts = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)  # 按频次排序
        
        # 创建新的Excel工作簿用于保存频次统计结果
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.append(['弹幕', '频次'])  # 添加标题行
        
        # 将排序后的词频结果写入Excel
        for word, count in sorted_word_counts:
            sheet.append([word, count])
        
        workbook.save('我的统计弹幕出现次数.xlsx')  # 保存频次统计的Excel文件
    except Exception as e:
        print(f"计算频次时出错: {e}")

# 主函数，负责执行整个流程
def main():
    tasks = put_api()  # 获取bvid和cid并创建并发任务
    bulletchats = get_data(tasks)  # 获取所有弹幕数据
    save_to_file(bulletchats)  # 保存弹幕数据到文件和Excel
    calculate_frequency()  # 计算弹幕频次
    print("Finished")  # 输出流程结束信息
    

# 如果此脚本被直接运行，则调用main函数
if __name__ == '__main__':
    main()

profile.disable()
# Save the profiling data to a file
profile.dump_stats('./output.prof')

