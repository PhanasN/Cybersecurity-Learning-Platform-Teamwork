import streamlit as st
from openai import OpenAI
import os
import requests
from PIL import Image

api_key = os.getenv("CYBERSECURITY_OPENAI_API_KEY")  # Used in production
client = OpenAI(api_key=api_key)

def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content.strip()

def generate_image(text):
    if not api_key:
        st.error("La clé API OpenAI n'est pas définie. Veuillez la définir dans vos variables d'environnement.")
        return

    try:
        with st.spinner('Génération de l\'image...'):
            response = client.images.generate(
                model="dall-e-3",
                prompt=text,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            return response.data[0].url
    except Exception as e:
        st.error(f"Erreur lors de la génération de l'image : {e}")
        return None

def generate_question(prompt):
    imageIds = []

    if "plain text" in prompt.lower() and "image" in prompt.lower():
        question = get_completion(prompt)
        answer_options = get_completion(f"Générer quatre options de réponse pour la question suivante :\n{question}\n")
        answer_options = answer_options.split("\n")

        output = f"Question :\n{question}\n\n"

        for option in answer_options:
            image_prompt = f"Générer une image illustrant l'option de réponse : {option.strip()}"
            image_url = generate_image(image_prompt)
            output += f"{option.strip()}\n"  # Removed numbering
            output += f"![IMAGE GÉNÉRÉE PAR IA]({image_url})\n\n"

    elif "scenario image" in prompt.lower():
        question = get_completion(prompt)
        answer_options = get_completion(f"Générer quatre options de réponse pour la question suivante :\n{question}\n")
        answer_options = answer_options.split("\n")

        output = f"Question :\n{question}\n\n"

        for option in answer_options:
            image_prompt = f"Générer une image illustrant l'option de réponse : {option.strip()}"
            image_url = generate_image(image_prompt)
            output += f"{option.strip()}\n"  # Removed numbering
            output += f"![IMAGE GÉNÉRÉE PAR IA]({image_url})\n\n"

    else:
        scenario = get_completion(prompt)
        question_prompt = "Générer une question pertinente basée sur le scénario suivant :\n" + scenario
        if "wrong" in prompt.lower():
            question_prompt += "\nLa question doit demander quelle action l'utilisateur ne devrait PAS prendre."
        else:
            question_prompt += "\nLa question doit demander quelle action l'utilisateur devrait prendre."
        question = get_completion(question_prompt)
        answer_options = get_completion(f"Générer quatre options de réponse pour la question suivante :\n{question}\n")
        answer_options = answer_options.split("\n")

        output = f"Scénario :\n{scenario}\n\nQuelle action devriez-vous prendre ?\n\nRéponses :\n"

