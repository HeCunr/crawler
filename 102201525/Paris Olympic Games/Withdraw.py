import re

# 读取txt文件
with open('我的全部弹幕.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

# 使用正则表达式提取包含“ai”或“AI”的弹幕，去掉单词边界限制
ai_danmu = [line.strip() for line in lines if re.search(r'[Aa][Ii]', line)]

# 保存结果到新文件
with open('提取.txt', 'w', encoding='utf-8') as output_file:
    for danmu in ai_danmu:
        output_file.write(danmu + '\n')

# 输出提取的弹幕
print(f"提取了 {len(ai_danmu)} 条弹幕，其中包含 'ai' 或 'AI' 关键字。")
