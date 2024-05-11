import streamlit as st
from openai import OpenAI
import os
from PIL import Image
import json

# General Housekeeping


api_key = "SECRET"  # Used in production
client = OpenAI(api_key=api_key)


# Defining Helper Functions

def generate_question(selected_language, selected_quiz_type, selected_category):
    promptOptionList = {
        'English': {'Plain text multiple choice': f"Create a multiple choice question about {selected_category} with four options and one correct answer. Format your output as a JSON response with the following keys: 'Question', 'A', 'B', 'C', 'D', 'Correct Answer'. For the 'Correct Answer' key, the value should be the letter corresponding to the correct option.", 
                    'Image-based': f"Generate a question about {selected_category} where the user must select the correct action or response from four images. Provide a detailed description of each image. Format your output as a JSON response with the following keys: 'Question', 'A', 'B', 'C', 'D', 'Correct Answer'. For the 'Correct Answer' key, the value should be the letter corresponding to the correct option."},
        'Français': {'Choix multiple en texte brut': f"Créez une question à choix multiple sur {selected_category} avec quatre options et une seule réponse correcte. Formatez votre sortie sous forme de réponse JSON avec les clés suivantes : « Question », « A », « B », « C », « D », « Bonne réponse ». Pour la touche 'Réponse correcte', la valeur doit être la lettre correspondant à l'option correcte.", 
                    "Basé sur l'image": f"Générez une question sur {selected_category} où l'utilisateur doit sélectionner l'action ou la réponse correcte parmi quatre images. Fournissez une description détaillée de chaque image."}
    }
    systemPromptOptionList = {
        'English': "You are an expert in IT cybersecurity and specialize in creating helpful content aimed at end users.",
        'Français': "Vous êtes un expert en cybersécurité informatique et spécialisé dans la création de contenu utile destiné aux utilisateurs finaux."
    }
    messages = [{"role": "user", "content": promptOptionList[selected_language][selected_quiz_type]},
                {"role": "system", "content": systemPromptOptionList[selected_language]}]
    
    """response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature = 0.1
    )
    return response.choices[0].message.content.strip()"""

    return '{"Question": "Panda", "A": "Are", "B": "Very", "C": "Adorable", "D": "Yeah?", "Answer": "B"}'

def generate_image(selected_quiz_type, question_info):
    pass

def check_answer(provided_answer, current_question):
    model_answer = json.loads(current_question)["Answer"]
    if json.loads(current_question)[model_answer] == provided_answer:
        st.success("Congrats, there is cake for you!")
    else:
        st.error("Failure, there is no cake for you!")

def sidebar_handler(current_option, scenarioList, current_language):
    if current_option == "Custom" or current_option == "Coutume":
        desired_scenario= st.sidebar.text_area("Enter a prompt here")
    else:
        desired_scenario = st.sidebar.selectbox("Scénario informatique à générer",
                                            options=scenarioList[current_language]['Scenarios'])
    return desired_scenario
    

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

    desired_language = st.sidebar.radio("Langue souhaitée", ["English", "Français"], index=0)

    scenarioOptionsList = {
        'English': {'Scenarios': ["phishing attacks", "spear phishing", "social engineering", "ransomware", "CEO fraud", "baiting", "Wi-Fi eavesdropping", "website spoofing", "password reuse", "insider threats", "outdated software", "convincing contractors", "helpful hackers"], 'Tones': ["Casual", "Professional"], 'Quiz Types': ["Plain text multiple choice", "Image-based", "Custom"]},
        'Français': {'Scenarios': ["attaques de phishing", "l'hameçonnage ciblé", "l'ingénierie sociale", "rançongiciels", "fraude au PDG", "l'appâtage", "l'écoute clandestine", "réutilisation de mot de passe", "imprimantes non sécurisées", "logiciels obsolètes", "entrepreneurs convaincants", "hackers utiles"], 'Tones': ["Décontracté", "Professionnel"], 'Quiz Types': ["Choix multiple en texte brut", "Basé sur l'image", "Coutume"]}
    }
    desired_quiz = st.sidebar.selectbox("Type de quiz souhaité", options = scenarioOptionsList[desired_language]['Quiz Types'])
    desired_scenario = sidebar_handler(desired_quiz, scenarioOptionsList, desired_language)

    st.title(language_labels[desired_language]["title"])
                                      
    # Initialize session state variables if they don't exist
    if "generated_output" not in st.session_state:
        st.session_state.generated_output = None
    if "feedback_displayed" not in st.session_state:
        st.session_state.feedback_displayed = False

    if st.session_state.generated_output == None:
        st.write("Select your options from the left, once complete, your custom item(s) will be generated below")
        if st.button("Générer la sortie" if desired_language == "Français" else "Generate Output"):
            output = generate_question(desired_language, desired_quiz, desired_scenario)
            st.session_state.generated_output = output
            st.session_state.feedback_displayed = False
            st.rerun()

    if st.session_state.generated_output:
        current_options = []
        st.subheader("Generated Output:")
        st.write(json.loads(st.session_state.generated_output)["Question"])
        #Add condition here for checking if image quiz or multiple choice only.
        for choice in ["A", "B", "C", "D"]:
            current_options.append(json.loads(st.session_state.generated_output)[choice])
        # Display each choice as a selectable multiple choice item
        user_choice = st.radio("Choices:", options = current_options)
        if st.button("Submit" if desired_language == "English" else "Soumettre"):
            check_answer(user_choice,st.session_state.generated_output)
            st.session_state.feedback_displayed = True
        
        if st.session_state.feedback_displayed:
            if st.button("Next" if desired_language == "English" else "Suivant"):
                st.session_state.generated_output = None
                st.session_state.feedback_displayed = False
                st.rerun()
              
if __name__ == "__main__":
    main()
