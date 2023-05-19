from transformers import BertPreTrainedModel, AutoConfig, BertModel, AutoTokenizer
from app.Utils.RedisConnection import redisConnection
from bson.json_util import dumps
import torch

# Create a Redis connection
redis = redisConnection()

# Define a custom BERT model for multilabel classification
class MultilabelBERT(BertPreTrainedModel):
    def __init__(self, config):
        # Load the configuration of the pre-trained BERT model
        config = AutoConfig.from_pretrained('bert-base-multilingual-cased')
        super(MultilabelBERT, self).__init__(config)

        # Initialize the BERT model
        self.bert = BertModel(config)

        # Define linear classifiers for each label
        self.classifier_sentiment = torch.nn.Linear(config.hidden_size, 3)
        self.classifier_impact_intensity = torch.nn.Linear(config.hidden_size, 3)
        self.classifier_impact_term = torch.nn.Linear(config.hidden_size, 3)

        # Initialize the model's weights
        self.init_weights()

    def forward(self, input_ids, attention_mask):
        # Pass the input through the BERT model and retrieve the outputs
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_attentions=True
        )

        # Extract the pooled output (representation of the entire input sequence)
        pooled_output = outputs[1]

        # Pass the pooled output through each linear classifier
        logits_sentiment = self.classifier_sentiment(pooled_output)
        logits_impact_intensity = self.classifier_impact_intensity(pooled_output)
        logits_impact_term = self.classifier_impact_term(pooled_output)

        # Retrieve the attention weights from the BERT model
        attentions = outputs[2]

        # Return the logits and attention weights
        return logits_sentiment, logits_impact_intensity, logits_impact_term, attentions

# Define a feed classifier class
class feedClassifier:
    def __init__(self):
        # Load the pre-trained multitask BERT model and tokenizer
        self.model = MultilabelBERT.from_pretrained(r"Tuiaia/multitask-bert-base-multilingual-cased")
        self.tokenizer = AutoTokenizer.from_pretrained(r"Tuiaia/multitask-bert-base-multilingual-cased")

    def classify_text(self, input_text):
        # Separate the request ID and input text from the input data
        request_id, input_text = redis.separate_id_text(input_text['data'])

        # Tokenize the input text and encode it as input for the model
        encoded_input = self.tokenizer(input_text, truncation=True, max_length=100, return_tensors="pt")
        encoded_input.pop("token_type_ids")

        with torch.no_grad():
            # Perform forward pass through the model to get the logits and attentions
            logits_sentiment, logits_impact_intensity, logits_impact_term, _ = self.model(**encoded_input)

        # Create a dictionary to store the classification results
        classify = dict()

        # Apply softmax to get probabilities and find the predicted classes
        probs_sentiment = torch.nn.functional.softmax(logits_sentiment, dim=-1)
        probs_impact_intensity = torch.nn.functional.softmax(logits_impact_intensity, dim=-1)
        probs_impact_term = torch.nn.functional.softmax(logits_impact_term, dim=-1)

        predicted_class_sentiment = torch.argmax(probs_sentiment)
        predicted_class_impact_intensity = torch.argmax(probs_impact_intensity)
        predicted_class_impact_term = torch.argmax(probs_impact_term)

        # Store the predicted classes in the classification dictionary
        classify['sentiment'] = predicted_class_sentiment.item()
        classify['intensity'] = predicted_class_impact_intensity.item()
        classify['term'] = predicted_class_impact_term.item()

        # Publish the classification results to Redis channel using the request ID as the channel name
        redis.r.publish(request_id, dumps(classify))