

import os
from os import path
from wordcloud import WordCloud
import jieba
from imageio.v3 import imread

def Bulletchat_Wordcloud():
    try:
        #获取当前文件路径
        d = path.dirname(__file__) if "__file__" in locals() else os.getcwd()
        text = open(path.join(d,r'2028.txt'), 'rb').read()
        # 设置模板图
        img_mask = imread(r'm1.png')
        # 对弹幕进行精确模式分词
        text_list = jieba.lcut(text,cut_all=False)
        text_str = ' '.join(text_list)
        # print(text_str)
        # 设置中文字体
        font_path = r'C:\Users\15653\msyh.ttc'
        # 停止词设置
        stopwords = set('')
        stopwords.update(['的','和','又','了','都','是','什么','所以','这','呢','吧','吗','个','呀','嘛','哈'])
        wc = WordCloud(
            font_path=font_path,
            #max_words=500,  # 最多词个数
            #min_font_size=15,
            #max_font_size=100,
            mask=img_mask,
            background_color='white',
            stopwords=stopwords,
            colormap='copper'
        )
        wc.generate(text_str)
        wc.to_file(r'outm1.png')
    except Exception as e:
        print(f"词云图生成异常: {e}")

if __name__ == '__main__':
    Bulletchat_Wordcloud()