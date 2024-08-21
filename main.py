from modules.NLP.STT import record_and_transcribe
from modules.NLP.create_JSON import create_museum_json
from modules.NLP.retrieval_model import answer_question
from modules.NLP.TSS import speak
from modules.NLP.NLG import generate_ai_response
from modules.NLP.utils import classify_intent, resolve_coreferences, extract_entities
from modules.NLP.grammar import grammar_corrector




def main():
    create_museum_json()
    speak("Hello, how may I help you?")

    entities = []
    handled_out_of_context = False  # Flag to check if out-of-context question was handled

    while True:
        if not handled_out_of_context:
            user_question = record_and_transcribe()
            if user_question is None:
                speak("I didn't quite get that. Could you please repeat your question?")
                continue

        try:
            if not handled_out_of_context:
                corrected_question = grammar_corrector.correct(user_question)
                print(f"Original question: {user_question}")
                print(f"Corrected question: {corrected_question}")

                resolved_question = resolve_coreferences(corrected_question, entities)
                entities.append(resolved_question)

                retrieved_answer, is_in_context = answer_question(resolved_question, entities)
                print(f"Context from answer_question: {retrieved_answer}")

            if not is_in_context and not handled_out_of_context:
                speak("This question seems unrelated to the current context. Was this question intentional?")
                clarification_response = record_and_transcribe()
                if clarification_response is None:
                    speak("I didn't quite get that. Was this question intentional?")
                    continue

                clarification_intent = classify_intent(clarification_response)
                if clarification_intent == "affirmative":
                    prompt = f"Question: {resolved_question}, Answer the question briefly"
                    ai_response = generate_ai_response(prompt)
                    speak(ai_response)
                    handled_out_of_context = True  # Mark that the out-of-context question has been handled
                elif clarification_intent == "negative":
                    speak("Let's continue with questions related to the museum.")
                    handled_out_of_context = False  # Continue as normal
                else:
                    speak("I'm not sure if you want to continue. Could you please say 'yes' if you want to proceed with this question, or 'no' if not?")
                    continue

            if handled_out_of_context or is_in_context:
                if not handled_out_of_context:
                    prompt = f"Question: {resolved_question}, context: {retrieved_answer}, based on context answer the question asked in a human-like response"
                    ai_response = generate_ai_response(prompt)
                    speak(ai_response)
                    entities.append(ai_response)

                # Ask if the user has more questions
                speak("Do you have any more questions?")
                while True:
                    continue_response = record_and_transcribe()
                    if continue_response is None:
                        speak("I didn't quite catch that. Do you have more questions?")
                        continue

                    continue_intent = classify_intent(continue_response)
                    if continue_intent == "negative":
                        print("Thank you for using the museum assistant. Goodbye!")
                        speak("Thank you for using the museum assistant. Goodbye!")
                        return  # End the conversation
                    elif continue_intent in ["affirmative", "question"]:
                        handled_out_of_context = False  # Reset flag for next question
                        break
                    else:
                        speak("I'm not sure if you want to continue. Could you please say 'yes' if you have more questions, or 'no' if you're done?")

        except Exception as e:
            print(f"An error occurred: {e}")
            speak("I'm sorry, I encountered an error. Could you please rephrase your question?")

    
if __name__ == "__main__":
    main()
