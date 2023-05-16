import io
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
from PIL import Image
from random import choice

class RandomColorFunc(object):
    def __init__(self, color_list):
        self.color_list = color_list

    def __call__(self, word, **kwargs):
        return choice(self.color_list)

class WordCloudGenerator:
    def __init__(self):
        nltk.download('punkt')
        nltk.download('stopwords')
        self.stop_words = stopwords.words('english') + stopwords.words('portuguese')
        self.pallette = ['#509B9E', '#38B6FF', '#48B091', '#01003B', '#04346D', '#2F6D51', '#44A2CB']
        self.width = 800
        self.height = 800
        self.background_color = 'white'
        self.seed = 42

    def generate_wordcloud(self, text):
        wordcloud = WordCloud(width=self.width,
                              height=self.height,
                              background_color=self.background_color,
                              stopwords=self.stop_words,
                              min_font_size=10,
                              random_state=self.seed,
                              prefer_horizontal=1).generate(text)

        color_func = RandomColorFunc(self.pallette)
        wordcloud.recolor(color_func=color_func)

        return wordcloud

    def plt_to_image(self):
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image = Image.open(buf)
        return image

    def get_wordcloud_image(self, wordcloud: WordCloud):
        plt.figure(figsize=(8, 8), facecolor=None)
        plt.imshow(wordcloud)
        plt.axis("off")
        plt.tight_layout(pad=0)
        wordcloud.to_file('wc.png')

        plt_image = self.plt_to_image()
        byte_arr = io.BytesIO()
        plt_image.save(byte_arr, format='PNG')
        byte_arr = byte_arr.getvalue()
        return byte_arr