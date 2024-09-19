import re
from collections import Counter
import pandas as pd

# 读取txt文件
with open('提取.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

# 定义AI应用的关键词
ai_categories = {
    'AI生成/合成': [r'AI生成', r'AI合成', r'AI图', r'一眼AI', r'AI'],
    'AI视频': [r'AI视频', r'AI合成的视频'],
    'AI修复': [r'AI修复', r'AI超分', r'超分辨率'],
    'AI音效/配音': [r'AI音效', r'AI配音'],
    'AI训练': [r'AI训练']
}

# 统计AI应用类别的出现次数
category_count = Counter()

# 遍历每一行弹幕，匹配AI应用的关键词
for line in lines:
    for category, keywords in ai_categories.items():
        if any(re.search(keyword, line, re.IGNORECASE) for keyword in keywords):
            category_count[category] += 1

# 将统计结果转换为pandas DataFrame
df = pd.DataFrame(list(category_count.items()), columns=['AI应用类别', '数量'])

# 按数量从大到小排序
df_sorted = df.sort_values(by='数量', ascending=False)

# 保存结果到Excel文件
df_sorted.to_excel('AI应用统计结果.xlsx', index=False)

# 输出提示
print("AI应用统计结果已保存为 'AI应用统计结果.xlsx'，数据已按数量从大到小排序。")
