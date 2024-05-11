import streamlit as st
from openai import OpenAI
import os
from PIL import Image
import json

api_key = os.getenv("CYBERSECURITY_OPENAI_API_KEY")  # Used in production
client = OpenAI(api_key=api_key)

def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content.strip()

def generate_image(text, size=None):
    if not api_key:
        st.error("OpenAI API key is not set. Please set it in your environment variables.")
        return

    if size is None:
        text_length = len(text)
        if text_length <= 50:
            size = "256x256"
        elif text_length <= 100:
            size = "512x512"
        else:
            size = "1024x1024"

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=text,
            size=size,
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        st.error(f"Error generating image: {e}")
        return None

def generate_question(prompt, language):
    print("Prompt:", prompt)  # Debugging print
    imageIds = []

    if language == "English":
        if "plain text" in prompt.lower() and "image" in prompt.lower():
            question = get_completion(prompt)
            answer_options = get_completion(f"Generate four answer options for the following question:\n{question}\n")
            answer_options = answer_options.split("\n")

            output = f"Question:\n{question}\n\n"

            for option in answer_options:
                image_prompt = f"Generate an image illustrating the answer option: {option.strip()}"
                with st.spinner('Generating Image...'):
                    image_url = generate_image(image_prompt)
                output += f"{option.strip()}\n"  # Removed numbering
                output += f"![AI GENERATED IMAGE]({image_url})\n\n"

        elif "scenario image" in prompt.lower():
            question = get_completion(prompt)
            answer_options = get_completion(f"Generate four answer options for the following question:\n{question}\n")
            answer_options = answer_options.split("\n")

            output = f"Question:\n{question}\n\n"

            for option in answer_options:
                image_prompt = f"Generate an image illustrating the answer option: {option.strip()}"
                with st.spinner('Generating Image...'):
                    image_url = generate_image(image_prompt)
                output += f"{option.strip()}\n"  # Removed numbering
                output += f"![AI GENERATED IMAGE]({image_url})\n\n"

        else:
            scenario = get_completion(prompt)
            question_prompt = "Generate a relevant question based on the following scenario:\n" + scenario
            if "wrong" in prompt.lower():
                question_prompt += "\nThe question should ask what action the user should NOT take."
            else:
                question_prompt += "\nThe question should ask what action the user should take."
            question = get_completion(question_prompt)
            answer_options = get_completion(f"Generate four answer options for the following question:\n{question}\n")
            answer_options = answer_options.split("\n")

            output = f"Scenario:\n{scenario}\n\nWhat action should you take?\n\nAnswers:\n"

            for option in answer_options:
                image_prompt = f"Generate an image illustrating the answer option: {option.strip()}"
                with st.spinner('Generating Image...'):
                    image_url = generate_image(image_prompt)
                output += f"{option.strip()}\n"  # Removed numbering
                output += f"![AI GENERATED IMAGE]({image_url})\n\n"

    elif language == "Français":
        if "texte brut" in prompt.lower() and "image" in prompt.lower():
            question = get_completion(f"Traduire en français: {prompt}")
            answer_options = get_completion(f"Générer quatre options de réponse pour la question suivante:\n{question}\n")
            answer_options = answer_options.split("\n")

            output = f"Question:\n{question}\n\n"

            for option in answer_options:
                image_prompt = f"Générer une image illustrant l'option de réponse: {option.strip()}"
                with st.spinner('Génération de l\'image...'):
                    image_url = generate_image(image_prompt)
                output += f"{option.strip()}\n"  # Removed numbering
                output += f"![IMAGE GÉNÉRÉE PAR L'IA]({image_url})\n\n"

        elif "image de scénario" in prompt.lower():
            question = get_completion(f"Traduire en français: {prompt}")
            answer_options = get_completion(f"Générer quatre options de réponse pour la question suivante:\n{question}\n")
            answer_options = answer_options.split("\n")

            output = f"Question:\n{question}\n\n"

            for option in answer_options:
                image_prompt = f"Générer une image illustrant l'option de réponse: {option.strip()}"
                with st.spinner('Génération de l\'image...'):
                    image_url = generate_image(image_prompt)
                output += f"{option.strip()}\n"  # Removed numbering
                output += f"![IMAGE GÉNÉRÉE PAR L'IA]({image_url})\n\n"

        else:
            scenario = get_completion(f"Traduire en français: {prompt}")
            question_prompt = "Générer une question pertinente basée sur le scénario suivant:\n" + scenario
            if "mauvaise" in prompt.lower():
                question_prompt += "\nLa question devrait demander quelle action l'utilisateur ne devrait PAS prendre."
            else:
                question_prompt += "\nLa question devrait demander quelle action l'utilisateur devrait prendre."
            question = get_completion(question_prompt)
            answer_options = get_completion(f"Générer quatre options de réponse pour la question suivante:\n{question}\n")
            answer_options = answer_options.split("\n")

            output = f"Scénario:\n{scenario}\n\nQuelle action devriez-vous prendre?\n\nRéponses:\n"

            for option in answer_options:
                image_prompt = f"Générer une image illustrant l'option de réponse: {option.strip()}"
                with st.spinner('Génération de l\'image...'):
                    image_url = generate_image(image_prompt)
                output += f"{option.strip()}\n"  # Removed numbering
                output += f"![IMAGE GÉNÉRÉE PAR L'IA]({image_url})\n\n"

    print("Answer Options:", answer_options)  # Debugging print
    return output


def check_answer(question, answer_options, selected_answer, language):
    correct_answer = get_completion(f"Which of the following is the correct answer to the question:\n{question}\n{answer_options}")
    if selected_answer.strip() == correct_answer.strip():
        if language == "English":
            explanation = get_completion(json.dumps(f'Provide a brief explanation of why "{selected_answer}" is the correct answer to the question:\n{question}'))
            return f"Correct!\n\n{explanation}"
        else:
            explanation = get_completion(json.dumps(f'Fournissez une brève explication de pourquoi "{selected_answer}" est la bonne réponse à la question :\n{question}'))
            return f"Correct!\n\n{explanation}"
    else:
        if language == "English":
            explanation = get_completion(json.dumps(f'Provide a brief explanation of why "{selected_answer}" is not the correct answer to the question:\n{question}\n\nThe correct answer is: {correct_answer}'))
            return f"Incorrect!\n\n{explanation}"
        else:
            explanation = get_completion(json.dumps(f'Fournissez une brève explication de pourquoi "{selected_answer}" n\'est pas la bonne réponse à la question :\n{question}\n\nLa bonne réponse est : {correct_answer}'))
            return f"Incorrect!\n\n{explanation}"

import streamlit as st

def main():
    language_labels = {
        "English": {
            "title": "Cybersecurity Question Generator",
            "prompt": "Enter a prompt to generate the desired output:"
        },
        "Français": {
            "title": "Générateur de Questions de Cybersécurité",
            "prompt": "Entrez une instruction pour générer la sortie désirée:"
        }
    }

    scenarioOptionsList = {
        'English': {'Scenarios': ["English 1", "English 2"], 'Tones': ["Casual", "Professional"]},
        'Français': {'Scenarios': ["French 1", "French 2"], 'Tones': ["FCasual", "FProfessional"]}
    }

    if st.sidebar.radio("Language", ["English", "Français"]) == "English":
        desired_language = "English"
        desired_scenario = st.sidebar.selectbox("Scenario to Generate",
                                                options=scenarioOptionsList[desired_language]['Scenarios'])
        desired_tone = st.sidebar.selectbox("Desired Tone",
                                            options=scenarioOptionsList[desired_language]['Tones'])
    else if st.sidebar.radio("Langue", ["English", "Français"]) == "Français":
        desired_language = "Français"
        desired_scenario = st.sidebar.selectbox("Scénario informatique à générer",
                                                options=scenarioOptionsList[desired_language]['Scenarios'])
        desired_tone = st.sidebar.selectbox("Ton de script souhaité",
                                            options=scenarioOptionsList[desired_language]['Tones'])

    st.title(language_labels[desired_language]["title"])
    prompt = st.text_input(language_labels[desired_language]["prompt"])

    if st.button("Générer la sortie" if desired_language == "Français" else "Generate Output"):
        output = generate_question(prompt, desired_language)
        st.subheader("Sortie Générée:" if desired_language == "Français" else "Generated Output:")
        st.markdown(output, unsafe_allow_html=True)  # Allow markdown with HTML
        
if __name__ == "__main__":
    main()
