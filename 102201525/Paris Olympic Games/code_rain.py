from PIL import Image, ImageDraw, ImageFont
import random
import imageio
import os
import re

# 参数设置
WIDTH = 800        # 图片宽度
HEIGHT = 600       # 图片高度
FONT_SIZE = 20     # 字体大小
COL_WIDTH = FONT_SIZE
NUM_COLS = WIDTH // COL_WIDTH
MAX_TRAIL_LENGTH = 15   # 代码雨最大长度
FRAMES_PER_SUBTITLE = 10    # 每条字幕的帧数
OUTPUT_GIF = 'code_rain.gif'  # 输出 GIF 文件名

def read_subtitles(filename):
    """读取字幕文件"""
    with open(filename, 'r', encoding='utf-8') as f:
        subtitles = f.readlines()
    subtitles = [line.strip() for line in subtitles if line.strip()]
    return subtitles

def extract_characters(subtitles):
    """从字幕中提取所有出现的字符"""
    chars_set = set()
    for line in subtitles:
        chars_set.update(line)
    return list(chars_set)

def main():
    # 读取字幕
    subtitles = read_subtitles(r'提取.txt')

    # 提取字符集
    CHARS = extract_characters(subtitles)
    # 添加额外的字符（可选）
    CHARS.extend(list('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*()+-'))

    # 加载字体（请确保字体文件存在）
    font_path = r'msyh.ttc'  # 替换为您的字体文件完整路径，确保支持中文

    # 检查字体文件是否存在
    if not os.path.exists(font_path):
        print(f"未找到字体文件 '{font_path}'。请提供正确的字体路径。")
        return

    try:
        font = ImageFont.truetype(font_path, FONT_SIZE)
    except OSError:
        print(f"无法打开字体文件 '{font_path}'。请检查文件是否损坏或权限设置。")
        return

    # 初始化列的位置
    column_positions = [random.randint(-HEIGHT, 0) for _ in range(NUM_COLS)]

    frames = []

    for subtitle in subtitles:
        for _ in range(FRAMES_PER_SUBTITLE):
            # 创建新图像
            img = Image.new('RGB', (WIDTH, HEIGHT), color='black')
            draw = ImageDraw.Draw(img)

            # 绘制代码雨
            for i in range(NUM_COLS):
                x = i * COL_WIDTH
                y = column_positions[i]

                for j in range(MAX_TRAIL_LENGTH):
                    char = random.choice(CHARS)
                    y_pos = y - j * FONT_SIZE
                    if y_pos < 0 or y_pos > HEIGHT:
                        continue
                    green_value = int(255 / MAX_TRAIL_LENGTH * (MAX_TRAIL_LENGTH - j))
                    draw.text((x, y_pos), char, font=font, fill=(0, green_value, 0))

                # 更新列的位置
                column_positions[i] = (y + FONT_SIZE) % (HEIGHT + FONT_SIZE * MAX_TRAIL_LENGTH)

            # 绘制字幕
            bbox = draw.textbbox((0, 0), subtitle, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = (WIDTH - text_width) // 2
            text_y = HEIGHT - text_height - 10  # 距离底部 10 像素
            draw.text((text_x, text_y), subtitle, font=font, fill=(255, 255, 255))

            # 添加帧
            frames.append(img)

    # 保存为 GIF
    frames[0].save(OUTPUT_GIF, save_all=True, append_images=frames[1:], optimize=False, duration=100, loop=0)
    print(f"GIF 已保存为 '{OUTPUT_GIF}'")

if __name__ == '__main__':
    main()
