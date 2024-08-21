import json
from modules.preprocess_and_search import preprocess_question, search_json
from modules.utils import rank_results, construct_answer, find_similar_concepts

# Load the JSON file
with open('knowledge_base/museum_data.json', 'r') as f:
    museum_data = json.load(f)


def answer_question(question, conversation_history):
    keywords, entities = preprocess_question(question, conversation_history)
    results = list(search_json(museum_data, keywords))

    is_in_context = True
    if not results:
        is_in_context = False
        similar_concepts = find_similar_concepts(keywords)
        results = list(search_json(museum_data, similar_concepts))

    if not results:
        return "I'm sorry, I couldn't find information related to your question.", is_in_context

    sorted_results = rank_results(results, keywords, entities)
    best_match = sorted_results[0]
    path, value = best_match

    return construct_answer(question, path, value), is_in_context