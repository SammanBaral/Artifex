from flask import Flask, request, jsonify, render_template
from modules.NLP.create_JSON import create_museum_json
from modules.NLP.retrieval_model import answer_question
# from modules.NLP.TSS import speak
from modules.NLP.NLG import generate_ai_response
from modules.NLP.utils import classify_intent, resolve_coreferences, extract_entities
from modules.NLP.grammar import grammar_corrector
from modules.NLP.STT import record_and_transcribe

app = Flask(__name__)
conversation_history = []
app.status="idle"
app.handled=False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start', methods=['GET'])
def start_conversation():
    create_museum_json() 
    initial_message = "Hello, how may I help you?"
    app.status="speaking"
    # speak(initial_message)
    app.status="idle"
    return jsonify({"message": initial_message})

@app.route('/transcribe', methods=['POST'])
def transcribe():
    app.status="transcribing"
    text = record_and_transcribe()
    app.status="processing"
    return jsonify({"transcription": text})

@app.route('/ask', methods=['POST'])
def ask():
    entities=[]
    data = request.json
    user_question = data['question']

    while True:
        if not app.handled:
            corrected_question = grammar_corrector.correct(user_question)
            resolved_question = resolve_coreferences(corrected_question, entities)
            entities.append(resolved_question)

        retrieved_answer, is_in_context = answer_question(resolved_question, entities)

        if not is_in_context and not app.handled:
            # speak("This question seems unrelated to the current context. Was this question intentional?")
            clarification_response = record_and_transcribe()
            
            while clarification_response is None:
                # speak("I didn't quite get that. Was this question intentional?")
                clarification_response = record_and_transcribe()
                if clarification_response:
                    break
                else:
                    continue

            clarification_intent = classify_intent(clarification_response)
            if clarification_intent == "affirmative":
                prompt = f"Question: {resolved_question}, Answer the question briefly"
                ai_response = generate_ai_response(prompt)
                # speak(ai_response)
                # Mark that the out-of-context question has been handled
                app.handled = True
                break
            elif clarification_intent == "negative":
                # speak("Let's continue with questions related to the museum.")
                app.handled = False
                break  # Continue as normal

        if app.handled or is_in_context:
            if not app.handled:
                prompt = f"Question: {resolved_question}, context: {retrieved_answer}, based on context answer the question asked in a human-like response"
                ai_response = generate_ai_response(prompt)
                app.status="speaking"
                # speak(ai_response)
                app.status="idle"
                entities.append(ai_response)
                return jsonify({"answer": ai_response})

@app.route('/continue', methods=['POST'])
def continue_conversation():
    message = "Do you have any more questions?"
    app.status="speaking"
    # speak(message)
    app.status="transcribing"
    return jsonify({"message": message})

@app.route('/classify_intent', methods=['POST'])
def classify_intent_route():
    data = request.json
    text = data['text']
    app.status="processing"
    intent = classify_intent(text)
    return jsonify({"intent": intent})

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({"status": app.status,"handled":app.handled})

# if __name__ == '__main__':
#     app.run(debug=True)
