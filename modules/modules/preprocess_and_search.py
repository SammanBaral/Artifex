import spacy
from spacy.matcher import Matcher

nlp = spacy.load("en_core_web_sm")
# matcher = Matcher(nlp.vocab)


def preprocess_question(question, conversation_history):
    resolved_question = resolve_coreferences(question, conversation_history)
    doc = nlp(resolved_question)
    important_words = [token.lemma_ for token in doc if token.pos_ in ('NOUN', 'VERB', 'ADJ', 'PROPN')]
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return important_words, entities

def resolve_coreferences(text, conversation_history):
    doc = nlp(" ".join(conversation_history + [text]))
    resolved_text = []
    for token in doc:
        if token.pos_ == "PRON":
            # Find the most recent noun phrase before this pronoun
            for previous_token in reversed(resolved_text):
                if previous_token.pos_ in ["NOUN", "PROPN"]:
                    resolved_text.append(previous_token)
                    break
            else:
                resolved_text.append(token)
        else:
            resolved_text.append(token)
    
    final_resolved_text = " ".join([token.text for token in resolved_text[-len(text.split()):]])
    return final_resolved_text

def search_json(data, keywords, current_path=[]):
    if isinstance(data, dict):
        for key, value in data.items():
            new_path = current_path + [key]
            if any(keyword.lower() in key.lower() for keyword in keywords):
                yield new_path, value
            if isinstance(value, (dict, list)):
                yield from search_json(value, keywords, new_path)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_path = current_path + [str(i)]
            if isinstance(item, (dict, list)):
                yield from search_json(item, keywords, new_path)