from transformers import BertPreTrainedModel, AutoConfig, BertModel, AutoTokenizer
from app.Utils.RedisConnection import redisConnection
from bson.json_util import dumps
import torch

redis = redisConnection()

class MultilabelBERT(BertPreTrainedModel):
    def __init__(self, config):
        config = AutoConfig.from_pretrained('bert-base-multilingual-cased')
        super(MultilabelBERT, self).__init__(config)

        self.bert = BertModel(config)
        self.classifier_sentiment = torch.nn.Linear(config.hidden_size, 3)
        self.classifier_impact_intensity = torch.nn.Linear(config.hidden_size, 3)
        self.classifier_impact_term = torch.nn.Linear(config.hidden_size, 3)

        self.init_weights()

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(
            input_ids=input_ids, 
            attention_mask=attention_mask,
            output_attentions=True
        )

        pooled_output = outputs[1]
        logits_sentiment = self.classifier_sentiment(pooled_output)
        logits_impact_intensity = self.classifier_impact_intensity(pooled_output)
        logits_impact_term = self.classifier_impact_term(pooled_output)

        attentions = outputs[2]
        return logits_sentiment, logits_impact_intensity, logits_impact_term, attentions

class feedClassifier:
    def __init__(self):
        self.model = MultilabelBERT.from_pretrained(r"Tuiaia/multitask-bert-base-multilingual-cased")
        self.tokenizer = AutoTokenizer.from_pretrained(r"Tuiaia/multitask-bert-base-multilingual-cased")

    def classify_text(self, input_text):
        request_id, input_text = redis.separate_id_text(input_text['data'])
        encoded_input = self.tokenizer(input_text, truncation=True, max_length=100, return_tensors="pt")
        encoded_input.pop("token_type_ids")

        with torch.no_grad():
            logits_sentiment, logits_impact_intensity, logits_impact_term, _ = self.model(**encoded_input)
        classify = dict()
        probs_sentiment = torch.nn.functional.softmax(logits_sentiment, dim=-1)
        probs_impact_intensity = torch.nn.functional.softmax(logits_impact_intensity, dim=-1)
        probs_impact_term = torch.nn.functional.softmax(logits_impact_term, dim=-1)

        predicted_class_sentiment = torch.argmax(probs_sentiment)
        predicted_class_impact_intensity = torch.argmax(probs_impact_intensity)
        predicted_class_impact_term = torch.argmax(probs_impact_term)
        classify['sentiment'] = predicted_class_sentiment.item()
        classify['intensity'] = predicted_class_impact_intensity.item()
        classify['term'] = predicted_class_impact_term.item()
        redis.r.publish(request_id, dumps(classify))
