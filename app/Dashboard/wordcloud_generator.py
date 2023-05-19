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
        # Download necessary NLTK resources
        nltk.download('punkt')
        nltk.download('stopwords')

        # Define stop words in English and Portuguese
        self.stop_words = stopwords.words('english') + stopwords.words('portuguese')

        # Define additional unusable words
        unusable_words = ["U", "R", "diz", "say", "says", "new", "veja", "milhões", "preço", "preços"]

        # Extend stop words with additional unusable words
        self.stop_words.extend(unusable_words)

        # Define color palette for wordcloud
        self.palette = ['#509B9E', '#38B6FF', '#48B091', '#01003B', '#04346D', '#2F6D51', '#44A2CB']

        # Define wordcloud dimensions
        self.width = 800
        self.height = 800

        # Define background color of wordcloud
        self.background_color = 'white'

        # Define random seed for wordcloud generation
        self.seed = 42

    def generate_wordcloud(self, text):
        # Generate wordcloud
        wordcloud = WordCloud(
            width=self.width,
            height=self.height,
            background_color=self.background_color,
            stopwords=self.stop_words,
            min_font_size=10,
            random_state=self.seed,
            prefer_horizontal=1
        ).generate(text)

        # Define custom color function for wordcloud
        color_func = RandomColorFunc(self.palette)
        wordcloud.recolor(color_func=color_func)

        return wordcloud

    def plt_to_image(self):
        # Convert matplotlib plot to image
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image = Image.open(buf)
        return image

    def get_wordcloud_image(self, wordcloud):
        # Generate and retrieve wordcloud image as bytes
        plt.figure(figsize=(8, 8), facecolor=None)
        plt.imshow(wordcloud)
        plt.axis("off")
        plt.tight_layout(pad=0)

        plt_image = self.plt_to_image()
        byte_arr = io.BytesIO()
        plt_image.save(byte_arr, format='PNG')
        byte_arr = byte_arr.getvalue()
        return byte_arr
    
    def get_bar_graph(self, text):
        # Generate bar graph of word frequencies
        text = WordCloud(stopwords=self.stop_words).process_text(text)
        text = dict(sorted(text.items(), key=lambda x: x[1], reverse=True))

        plt.figure(figsize=(8, 8), facecolor=None)
        plt.bar(list(text.keys())[:5], list(text.values())[:5], color='tab:blue')
        plt.show(block=True)
        plt.tight_layout(pad=0)

        plt_image = self.plt_to_image()
        image_bytes = io.BytesIO()
        plt_image.save(image_bytes, format='PNG')

        return image_bytes.getvalue()
