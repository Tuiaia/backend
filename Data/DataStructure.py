import pandas as pd

class ConjuntoDados:
    def __init__(self):
        self.df = pd.DataFrame({'data': [], 'titulo': [], 'urls' : [], 'subtitle': []})

    def load_data(self):
        self.df = pd.read_csv(r"C:\Users\User\Desktop\Pantanal.dev\backend\Data\newsletter.csv")

    def transform_json(self):
        data_json = dict()
        for i in range(len(self.df['data'])):
            data_json[i] = {'data' : self.df['data'], 'titulo': self.df['titulo'],
                         'url' : self.df['urls'], 'texto' : self.df['text']}
        return data_json