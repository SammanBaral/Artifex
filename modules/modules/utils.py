import spacy
import torch
from transformers import AutoTokenizer, AutoModel, pipeline
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from fuzzywuzzy import fuzz

nlp = spacy.load("en_core_web_sm")
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
model = AutoModel.from_pretrained("bert-base-uncased")
sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

def find_similar_concepts(keywords, top_n=5):
    keyword_embeddings = sentence_model.encode(keywords)
    
    vocabulary = list(set(word.lower() for word in nlp.vocab.strings))
    vocab_embeddings = sentence_model.encode(vocabulary)
    
    similarities = cosine_similarity(keyword_embeddings, vocab_embeddings)
    
    similar_concepts = []
    for keyword, sim_scores in zip(keywords, similarities):
        top_indices = np.argsort(sim_scores)[-top_n:]
        similar_words = [vocabulary[i] for i in top_indices if vocabulary[i] != keyword]
        similar_concepts.extend(similar_words)
    
    return list(set(similar_concepts))

def rank_results(results, keywords, entities):
    def calculate_score(result, keywords, entities):
        path, value = result
        path_str = " ".join(path).lower()
        value_str = str(value).lower()
        
        keyword_score = sum(fuzz.partial_ratio(keyword, path_str) + fuzz.partial_ratio(keyword, value_str) for keyword in keywords)
        entity_score = sum(fuzz.partial_ratio(entity[0], path_str) + fuzz.partial_ratio(entity[0], value_str) for entity in entities)
        
        return keyword_score + entity_score

    return sorted(results, key=lambda x: calculate_score(x, keywords, entities), reverse=True)

def construct_answer(question, path, value):
    template = "Based on the information about {}, the answer to your question '{}' is: {}"
    path_str = " > ".join(path)
    
    if isinstance(value, (str, int, float)):
        answer = str(value)
    elif isinstance(value, dict):
        answer = ", ".join(f"{k}: {v}" for k, v in value.items())
    elif isinstance(value, list):
        answer = ", ".join(map(str, value))
    else:
        answer = "Information not available in the expected format."

    return template.format(path_str, question, answer)

def classify_intent(response):
    affirmative_phrases = [
        'yes', 'yeah', 'yep', 'sure', 'ok', 'okay', 'alright', 'certainly', 'absolutely',
        'continue', 'go on', 'proceed', 'carry on', 'keep going', 'let\'s continue'
    ]
    negative_phrases = ['no', 'nope', 'nah', 'not', 'stop', 'end', 'finish', 'quit']
    
    doc = nlp(response.lower())
    
    # Check for exact matches first
    for token in doc:
        if token.text in affirmative_phrases:
            return "affirmative"
        if token.text in negative_phrases:
            return "negative"
    
    # Check for phrase matches
    for phrase in affirmative_phrases:
        if phrase in doc.text:
            return "affirmative"
    for phrase in negative_phrases:
        if phrase in doc.text:
            return "negative"
    
    # Check for questions
    if any(token.tag_ == "." and token.text == "?" for token in doc):
        return "question"
    
    # Use sentiment analysis for ambiguous responses
    sentiment_result = sentiment_analyzer(response)[0]
    if sentiment_result['label'] == 'POSITIVE' and sentiment_result['score'] > 0.6:
        return "affirmative"
    elif sentiment_result['label'] == 'NEGATIVE' and sentiment_result['score'] > 0.6:
        return "negative"
    
    return "unknown"


def update_knowledge_base(question, answer):
    # This is a placeholder function. In a real-world scenario, you'd implement
    # a more sophisticated method to update the knowledge base.
    print(f"Updating knowledge base with Q: {question}, A: {answer}")
    # Here you would typically update your JSON file or database
    pass

def resolve_coreferences(text, entities):
    doc = nlp(text)
    resolved_text = []
    for token in doc:
        if token.pos_ == "PRON":
            # Find the most recent matching entity
            for entity in reversed(entities):
                if entity[1] in ["PERSON", "ORG", "GPE", "PRODUCT"]:  # Add more entity types as needed
                    resolved_text.append(entity[0])
                    break
            else:
                resolved_text.append(token.text)
        else:
            resolved_text.append(token.text)
    
    return " ".join(resolved_text)

def extract_entities(text):
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return entities

