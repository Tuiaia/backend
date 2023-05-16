from transformers import AutoTokenizer, AutoModelForSequenceClassification
import nltk
from nltk.corpus import stopwords
from langdetect import detect
from transformers_interpret import SequenceClassificationExplainer
from string import punctuation
from bson.json_util import dumps
from app.Utils.RedisConnection import redisConnection
redis = redisConnection()

sentiment_path = r"Tuiaia/bert-base-multilingual-cased-sentiment"
term_path = r"Tuiaia/bert-base-multilingual-cased-impact-term"
intensity_path = r"Tuiaia/bert-base-multilingual-cased-impact-intensity"
class Classifier:

    def __init__(self) -> None:
        nltk.download('stopwords')
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')
        print("Reading model")
        self.sentiment_tokenizer = AutoTokenizer.from_pretrained(sentiment_path)
        self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(sentiment_path)
        self.term_tokenizer = AutoTokenizer.from_pretrained(term_path)
        self.term_model = AutoModelForSequenceClassification.from_pretrained(term_path)
        self.intensity_tokenizer = AutoTokenizer.from_pretrained(intensity_path)
        self.intensity_model = AutoModelForSequenceClassification.from_pretrained(intensity_path)
        self.sentiment_cls_explainer = SequenceClassificationExplainer(self.sentiment_model, self.sentiment_tokenizer)
        self.term_cls_explainer = SequenceClassificationExplainer(self.term_model, self.term_tokenizer)
        self.intensity_cls_explainer = SequenceClassificationExplainer(self.intensity_model, self.intensity_tokenizer)


    # Função para remover stopwords de um texto
    def remove_stopwords(self, text: str, language: str = "auto") -> str:
        """
        Remove stopwords de um texto em português ou inglês.

        Args:
            text (str): O texto para remover as stopwords.
            language (str, optional): O idioma das stopwords. Por padrão, é utilizado "auto" para detectar o idioma automaticamente.

        Returns:
            str: O texto sem stopwords.

        Raises:
            ValueError: Se o idioma detectado automaticamente não for suportado pela aplicação.

        Exemplo de uso:
            >>> texto = "Este é um exemplo de texto em português que será processado para remoção de stopwords."
            >>> texto_sem_stopwords = remove_stopwords(texto, language="portuguese")
            >>> print(texto_sem_stopwords)
            "exemplo texto português processado remoção stopwords."
        """
        if language == 'auto':
            language = detect(text)
            if language == 'en':
                language = 'english'
            else:
                language = 'portuguese'
        words = nltk.word_tokenize(text)
        stopwords_list = set(stopwords.words(language))
        filtered_words = [word for word in words if word.lower() not in stopwords_list]
        return " ".join(filtered_words)

    def merge_subtokens(self, tokenizer, word_attributions: list[tuple]) -> list[tuple]:
        """
        Agrupa as pontuações de tokens divididos do BERT em um único token.
        
        Args:
            tokenizer: Tokenizer BERT para usar.
            word_attributions (List[tuple]): As atribuições de palavras do tokenizador.

        Returns:
            List[tuple]: Atribuições de palavras com tokens divididos mesclados.
        """
        merged_attributions = []
        merged_token = ''
        merged_value = 0.0

        for token, value in word_attributions:
            detokenized_token = tokenizer.convert_tokens_to_string([token]).strip()
            if detokenized_token:
                if detokenized_token in punctuation or detokenized_token in {'[CLS]', '[SEP]', '[UNK]'}:
                    continue
                if token.startswith('##'):
                    merged_token += token[2:]
                    merged_value += value
                else:
                    if merged_token:
                        merged_attributions.append((merged_token, merged_value))
                        merged_token = ''
                        merged_value = 0.0
                    merged_token = detokenized_token
                    merged_value = value
            else:
                merged_token += token.replace('##', '')
                merged_value += value

        if merged_token:
            merged_attributions.append((merged_token, merged_value))

        return merged_attributions

    def format_attributions(self, word_attributions: list[tuple[str, float]]) -> list[tuple[str, str]]:
        """
        Formata as atribuições de palavras para uma representação mais intuitiva.

        Args:
            word_attributions: Uma lista de tuplas contendo as atribuições de palavras. Cada tupla contém uma palavra/token
                e um valor float representando sua importância.

        Returns:
            Uma lista de tuplas contendo as palavras formatadas e suas atribuições em formato de porcentagem, ordenadas por
            importância.
        """
        # Obter o valor total das atribuições
        total = sum(abs(score) for _, score in word_attributions)

        # Formatar cada atribuição como uma tupla (token, porcentagem)
        formatted_attributions = []
        for token, score in word_attributions:
            # Calcular a porcentagem e arredondar para duas casas decimais
            percentage = round((abs(score) / total) * 100, 2)
            formatted_attributions.append((token, percentage))

        # Ordenar as atribuições por porcentagem descendente
        formatted_attributions = sorted(formatted_attributions, key=lambda x: x[1], reverse=True)

        return formatted_attributions


    def classify_text(self, input_text):
        request_id, input_text = redis.separate_id_text(input_text['data'])
        input_text = self.remove_stopwords(input_text)
        classify = list()
        classify.append(self.classify_sentiment(input_text))
        classify.append(self.classify_intensity(input_text))
        classify.append(self.classify_term(input_text))

        redis.r.publish(request_id, dumps(classify))

    def classify_sentiment(self, input_text):
        input_text = self.remove_stopwords(input_text)
        tokenized_input = self.sentiment_tokenizer(input_text, truncation=True, max_length=100, return_tensors='pt')
        truncated_input_text = self.sentiment_tokenizer.decode(tokenized_input['input_ids'][0])
        word_attributions = self.sentiment_cls_explainer(truncated_input_text)
        word_attributions = self.merge_subtokens(self.sentiment_tokenizer, word_attributions)
        word_attributions = sorted(word_attributions, key=lambda x: (-x[1], x[0]))
        word_attributions = self.format_attributions(word_attributions)
        return {
            'prediction_index': int(self.sentiment_cls_explainer.predicted_class_index),
            'prediction_probatility': f"{round(float(self.sentiment_cls_explainer.pred_probs.numpy()*100), 2)}%",
            'influential_words': [x[0] for x in word_attributions]
        }

    def classify_intensity(self, input_text):
        input_text = self.remove_stopwords(input_text)
        tokenized_input = self.intensity_tokenizer(input_text, truncation=True, max_length=100, return_tensors='pt')
        truncated_input_text = self.intensity_tokenizer.decode(tokenized_input['input_ids'][0])
        word_attributions = self.intensity_cls_explainer(truncated_input_text)
        word_attributions = self.merge_subtokens(self.intensity_tokenizer, word_attributions)
        word_attributions = sorted(word_attributions, key=lambda x: (-x[1], x[0]))
        word_attributions = self.format_attributions(word_attributions)
        return {
            'prediction_index': int(self.intensity_cls_explainer.predicted_class_index),
            'prediction_probatility': f"{round(float(self.intensity_cls_explainer.pred_probs.numpy()*100), 2)}%",
            'influential_words': [x[0] for x in word_attributions]
        }
    
    def classify_term(self, input_text):
        input_text = self.remove_stopwords(input_text)
        tokenized_input = self.term_tokenizer(input_text, truncation=True, max_length=100, return_tensors='pt')
        truncated_input_text = self.term_tokenizer.decode(tokenized_input['input_ids'][0])
        word_attributions = self.term_cls_explainer(truncated_input_text)
        word_attributions = self.merge_subtokens(self.term_tokenizer, word_attributions)
        word_attributions = sorted(word_attributions, key=lambda x: (-x[1], x[0]))
        word_attributions = self.format_attributions(word_attributions)
        return {
            'prediction_index': int(self.term_cls_explainer.predicted_class_index),
            'prediction_probatility': f"{round(float(self.term_cls_explainer.pred_probs.numpy()*100), 2)}%",
            'influential_words': [x[0] for x in word_attributions]
        }