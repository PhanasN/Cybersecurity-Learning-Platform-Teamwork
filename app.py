# Importing necessary libraries
import streamlit as st
from openai import OpenAI
import os
from PIL import Image
import json
import os
import shutil
from zipfile import ZipFile
import tempfile
from time import sleep
import requests
from io import BytesIO

# General Housekeeping
api_key = os.getenv("CYBERSECURITY_OPENAI_API_KEY") # Retrieve the OpenAI API key from environment variables
client = OpenAI(api_key=api_key) # Initialize the OpenAI client


def main():
    # Language labels for English and French
    language_labels = {
        "English": {
            "title": "Cybersecurity Question Generator",
            "prompt": "Enter a prompt to generate the desired output:",
            "initial instructions": "Select your options from the left, once complete, your custom item(s) will be generated below"
        },
        "Français": {
            "title": "Générateur de Questions de Cybersécurité",
            "prompt": "Entrez une instruction pour générer la sortie désirée:",
            "initial instructions": "Sélectionnez vos options à gauche, une fois terminé, vos articles personnalisés seront générés ci-dessous"
        }
    }
    # Options for scenarios, tones, and quiz types in English and French
    scenarioOptionsList = {
        'English': {
            'Scenarios': ["phishing attacks", "spear phishing", "social engineering", "ransomware", "CEO fraud", "baiting", "Wi-Fi eavesdropping", "website spoofing", "password reuse", "insider threats", "outdated software", "convincing contractors", "helpful hackers"],
            'Tones': ["Casual", "Professional"],
            'Quiz Types': ["Plain text multiple choice", "Image-based", "Custom"]
        },
        'Français': {
            'Scenarios': ["attaques de phishing", "l'hameçonnage ciblé", "l'ingénierie sociale", "rançongiciels", "fraude au PDG", "l'appâtage", "l'écoute clandestine", "réutilisation de mot de passe", "imprimantes non sécurisées", "logiciels obsolètes", "entrepreneurs convaincants", "hackers utiles"],
            'Tones': ["Décontracté", "Professionnel"],
            'Quiz Types': ["Choix multiple en texte brut", "Basé sur l'image", "Coutume"]
        }
    }
    # Initialize session state variables
    initialize_session_state()

    if st.session_state.generated_output is None:
        st.session_state.desired_language = st.sidebar.radio("Langue souhaitée", ["English", "Français"], index=1)
        st.session_state.desired_quiz = st.sidebar.selectbox("Type de quiz souhaité", options=scenarioOptionsList[st.session_state.desired_language]['Quiz Types'])
        st.session_state.desired_scenario = sidebar_handler(st.session_state.desired_quiz, scenarioOptionsList, st.session_state.desired_language)

        st.title(language_labels[st.session_state.desired_language]["title"])
        st.write(language_labels[st.session_state.desired_language]["initial instructions"])

        if st.button("Générer la sortie" if st.session_state.desired_language == "Français" else "Generate Output"):
            generate_and_store_output(st.session_state.desired_language, st.session_state.desired_quiz, st.session_state.desired_scenario)
    else:
        st.write(st.session_state.generated_output) #Debug
        if st.session_state.edits_requested == True:
            handle_edits(st.session_state.desired_language)
        elif st.session_state.regeneration_requested == True:
            handle_regeneration(st.session_state.desired_quiz, st.session_state.desired_language)
        else:
            display_output(st.session_state.desired_quiz, st.session_state.desired_language)
        
# Function to initialize session state variables
def initialize_session_state():
    storage_states = ["generated_output", "output_to_modify", "current_chat_id", "generated_images", "generated_descriptions", "export_generated"]
    flag_states = ["feedback_displayed", "edits_requested", "download_complete", "regeneration_requested"]
    
    for item in storage_states:
        if item not in st.session_state:
            st.session_state[item] = None

    for item in flag_states:
        if item not in st.session_state:
            st.session_state[item] = False
            
# Function to generate and store the output based on user inputs
def generate_and_store_output(language, quiz, scenario):
    complete_response = generate_question(language, quiz, scenario, st.session_state.generated_output)
    st.session_state.generated_output = complete_response[0]
    st.session_state.current_chat_id = complete_response[1]
    st.session_state.feedback_displayed = False
    if st.session_state.regeneration_requested == True:
        st.session_state.regeneration_requested = False
    st.rerun()
    
# Function to display the output based on the selected quiz type
def display_output(quiz, language):
    if quiz in ["Plain text multiple choice", "Choix multiple en texte brut", "Coutume", "Custom"]:
        display_text_output(language)
    elif quiz == "Image-based" or quiz == "Basé sur l'image":
        display_image_output(language)

# Function to display text output
def display_text_output(language):
    st.subheader("Sortie générée:")
    if st.session_state.desired_quiz in ["Coutume", "Custom"]:
        if language == "English":
            st.write(json.loads(st.session_state.generated_output)["Scenario"])
        else:
            st.write(json.loads(st.session_state.generated_output)["Scénario"])
    st.write(json.loads(st.session_state.generated_output)["Question"])
    
    current_options = [json.loads(st.session_state.generated_output)[choice] for choice in ["A", "B", "C", "D"]]
    user_choice = st.radio("Les choix:", options=current_options)

    handle_common_buttons(language, is_image_output=False)

# Function to display image output
def display_image_output(language):
    st.subheader("Sortie générée:")
    st.write(json.loads(st.session_state.generated_output)["Question"])

    if st.session_state.generated_images is None:
        generate_images(language)

    for index, choice in enumerate(["A", "B", "C", "D"]):
        st.image(st.session_state.generated_images[index], caption=f'{choice}. {st.session_state.generated_descriptions[choice]}')

    handle_common_buttons(language, is_image_output=True)

# Function to generate images based on question options
def generate_images(language):
    current_options = {choice: json.loads(st.session_state.generated_output)[choice] for choice in ["A", "B", "C", "D"]}
    st.session_state.generated_descriptions = current_options
    
    with st.spinner("Génération d'images, merci pour votre patience!"):
        st.session_state.generated_images = generate_image(st.session_state.generated_output, language)
    st.rerun()

# Function to handle common buttons for various operations
def handle_common_buttons(language, is_image_output):
    if st.button("Regenerate" if language == "English" else "Régénérer"):
        st.session_state.output_to_modify = st.session_state.generated_output
        st.session_state.regeneration_requested = True
        st.rerun()
    
    if st.button("Edit" if language == "English" else "Modifier"):
        st.session_state.output_to_modify = st.session_state.generated_output
        st.text_input(st.session_state.output_to_modify)
        st.session_state.edits_requested = True
        st.session_state.generated_output = False
        st.rerun()

    if st.button("Export" if language == "English" else "Exporter"):
        export_output(is_image_output)

    if st.button("Reset" if language == "English" else "Réinitialiser"):
        reset_session_state()
        st.rerun()

# Function to export the generated output
def export_output(is_image_output):
    if is_image_output:
        image_paths = download_and_store_images(st.session_state.generated_images)
        sample_zip = create_sample_zip(image_paths, st.session_state.generated_output)
    else:
        sample_zip = create_sample_zip(None, st.session_state.generated_output)
    
    with open(sample_zip, "r+b") as file:
        file_contents = file.read()
    if st.download_button(label="Download", data=file_contents, file_name="sample_files.zip", mime="application/zip"):
        cleanup_files(sample_zip, image_paths if is_image_output else None)

# Function to clean up temporary files
def cleanup_files(sample_zip, image_paths=None):
    if image_paths:
        for image_path in image_paths:
            os.remove(image_path)
    os.remove(sample_zip)
    os.rmdir(os.path.dirname(sample_zip))

# Function to reset the session state
def reset_session_state():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

# Function to handle edits to the generated output
def handle_edits(language):
    st.session_state.output_to_modify = st.text_area("The current quiz objects." if language == "English" else "Les objets du quiz en cours.", st.session_state.output_to_modify)
    if st.button("Submit Change Request" if language == "English" else "soumettre une demande de modification"):
        st.session_state.generated_output = st.session_state.output_to_modify
        if st.session_state.generated_descriptions:
            st.session_state.generated_descriptions = {choice: json.loads(st.session_state.generated_output)[choice] for choice in ["A", "B", "C", "D"]}
        st.session_state.edits_requested = False
        st.rerun()

# Function to handle regeneration of the output
def handle_regeneration(quiz, language):
    if quiz == "Image-based" or quiz == "Basé sur l'image":
        handle_image_regeneration(language)
    else:
        handle_text_regeneration(language)

def handle_text_regeneration(language):
    st.subheader("Sortie générée:")
    st.write(json.loads(st.session_state.generated_output)["Question"])

    current_options = [json.loads(st.session_state.generated_output)[choice] for choice in ["A", "B", "C", "D"]]
    user_choice = st.radio("Les choix:", options=current_options)

    generate_and_store_output(language, st.session_state.desired_quiz, st.session_state.desired_scenario)

# Function to handle regeneration of image output
def handle_image_regeneration(language):
    if st.session_state.generated_images:
        for index, choice in enumerate(["A", "B", "C", "D"]):
            st.image(st.session_state.generated_images[index], caption=f'{choice}. {st.session_state.generated_descriptions[choice]}')
        
        selected_options = st.multiselect("Select options:", list(st.session_state.generated_descriptions.keys()))
        
        if st.button("Select Images to Regenerate" if language == "English" else "Demander de nouvelles image(s)"):
            st.session_state.generated_images = regenerate_image(st.session_state.generated_images, st.session_state.generated_descriptions, selected_options, language)
            st.session_state.regeneration_requested = False
            st.session_state.generated_output = st.session_state.output_to_modify
            st.rerun()
    else:
        st.warning("No images found to regenerate.")

# Helper functions

# Function to generate a question based on the selected options
def generate_question(selected_language, selected_quiz_type, selected_category, previous_response):
    promptOptionList = {
        'English': {'Plain text multiple choice': f"Create a scenario-based multiple choice question about {selected_category} with four options and one correct answer. Format your output as a JSON response with the following keys: 'Question', 'A', 'B', 'C', 'D', 'Correct Answer'. For the 'Correct Answer' key, the value should be the letter corresponding to the correct option.", 
                    'Image-based': f"Generate a scenario-based question about {selected_category} where the user must select the incorrect action or response from four images. Only one image description should correspond with an incorrect action. All other options should be an appropriate response but not provide justification as to why they are correct. Format your output as a JSON response with the following keys: 'Question', 'A', 'B', 'C', 'D', 'Incorrect Answer'. For the 'Incorrect Answer' key, the value should be the letter corresponding to the incorrect option.",
                    'Custom': f"""Given an overview of a new cybersecurity threat to end users, generate the following items: 

                    1. A small vignette that frames a way the threat may possibly appear.
                    2. A scenario-based question relating to the vignette on what action one of the characters in the vignette, representing the end user, should take.
                    3. Four possible answer choices relating to the vignette and question.

                    Output the response in a JSON format with the following keys: 'Scenario', 'Question', 'A', 'B', 'C', 'D', 'Answer'. The output must only contain one correct answer. The 'Answer' value should correspond with the key that has the description of the correct action.

                    Example threat overview: {selected_category}"""},
        'Français': {'Choix multiple en texte brut': f"Créez une question à choix multiples basée sur un scénario sur {selected_category} avec quatre options et une seule réponse correcte. Formatez votre sortie sous forme de réponse JSON avec les clés suivantes : « Question », « A », « B », « C », « D », « Bonne réponse ». Pour la touche 'Réponse correcte', la valeur doit être la lettre correspondant à l'option correcte.", 
                    "Basé sur l'image": f"Générez une question basée sur un scénario sur {selected_category} dans laquelle l'utilisateur doit sélectionner l'action ou la réponse incorrecte parmi quatre images. Une seule description d’image doit correspondre à une action incorrecte. Toutes les autres options doivent constituer une réponse appropriée mais ne doivent pas justifier pourquoi elles sont correctes. Formatez votre sortie sous forme de réponse JSON avec les clés suivantes : « Question », « A », « B », « C », « D », « Réponse incorrecte ». Pour la touche « Réponse incorrecte », la valeur doit être la lettre correspondant à l'option incorrecte.",
                    'Coutume': f"""Compte tenu d’un aperçu d’une nouvelle menace de cybersécurité pour les utilisateurs finaux, générez les éléments suivants :

                    1. Une petite vignette qui décrit la façon dont la menace peut éventuellement apparaître.
                    2. Une question basée sur un scénario relative à la vignette sur l'action que devrait entreprendre l'un des personnages de la vignette, représentant l'utilisateur final.
                    3. Quatre choix de réponses possibles relatifs à la vignette et à la question.

                    Affichez la réponse au format JSON avec les clés suivantes : "Scénario", "Question", "A", "B", "C", "D", "Réponse". La sortie ne doit contenir qu'une seule réponse correcte. La valeur « Réponse » doit correspondre à la clé qui contient la description de l'action correcte.

                    Exemple de présentation des menaces : {selected_category}"""}
    }
    systemPromptOptionList = {
        'English': "You are an expert in IT cybersecurity and specialize in creating helpful content aimed at end users. When creating content, do not repeat previous examples.",
        'Français': "Vous êtes un expert en cybersécurité informatique et spécialisé dans la création de contenu utile destiné aux utilisateurs finaux. Lors de la création de contenu, ne répétez pas les exemples précédents."
    }
    if previous_response == None:
        messages = [{"role": "user", "content": promptOptionList[selected_language][selected_quiz_type]},
                    {"role": "system", "content": systemPromptOptionList[selected_language]}]
    else:
        extra_context = {
            'English': f"Your previous response was {previous_response}",
            'Français': f"Votre réponse précédente était: {previous_response}"
        }
        content = promptOptionList[selected_language][selected_quiz_type] + extra_context[selected_language]
        messages = [{"role": "user", "content": promptOptionList[selected_language][selected_quiz_type]},
                    {"role": "system", "content": content}]
        
    with st.spinner("Generating content..."):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature = 0.1,
            response_format={"type": "json_object"},
        )

    # Validation of Format Check
    validated_output = False
    keyOptions = {"English":{"Plain text multiple choice":["Question", "A", "B", "C", "D", "Correct Answer"], "Image-based":["Question", "A", "B", "C", "D", "Incorrect Answer"], "Custom": ["Scenario", "Question", "A", "B", "C", "D", "Answer"]},
                  "Français": {"Choix multiple en texte brut":["Question", "A", "B", "C", "D", "Bonne réponse"], "Basé sur l'image":["Question", "A", "B", "C", "D", "Réponse incorrecte"], "Coutume": ["Scénario", "Question", "A", "B", "C", "D", "Réponse"]}}
    with st.spinner("Checking output..."):
        validation_failure = False
        keys = keyOptions[selected_language][selected_quiz_type]
        while not validated_output:
            test_dict = json.loads(response.choices[0].message.content.strip())
            for key in keys:
                if key not in test_dict:
                    st.error("Invalid Format Detected, regenerating.")
                    validation_failure = True
                    break 
            if not validation_failure:
                st.success("Format validated!")
                sleep(2)
                validated_output = True
    return [response.choices[0].message.content.strip(), response.id]

# Function to generate images based on question options
def generate_image(question_options, selected_language):
    image_links = []
  
    image_user_prompts = {"English":"Create an image in a realistic art style depicting an office professional engaged in basic cyber security tasks at their workstation in a modern office environment. The individual should be portrayed realistically, using a business-casual attire, surrounded by vibrant but realistic technology interfaces. These interfaces should appear colorful and abstract, symbolizing the digital security tools the professional is interacting with, but remain plausible without any readable text. This scene should visually capture the focus and interaction of a regular office worker navigating cybersecurity protocols. This image should visually capture the esssence of the following action: ",
                          "Français": "Créez une image dans un style artistique réaliste représentant un professionnel de bureau engagé dans des tâches de base en matière de cybersécurité sur son poste de travail dans un environnement de bureau moderne. L'individu doit être représenté de manière réaliste, en utilisant une tenue professionnelle décontractée, entouré d'interfaces technologiques dynamiques mais réalistes. Ces interfaces doivent apparaître colorées et abstraites, symbolisant les outils de sécurité numérique avec lesquels le professionnel interagit, mais rester plausibles sans aucun texte lisible. Cette scène doit capturer visuellement l'attention et l'interaction d'un employé de bureau ordinaire naviguant dans les protocoles de cybersécurité. Cette image doit capturer visuellement l’essence de l’action suivante: "}
    
    base_user_prompt = image_user_prompts[selected_language]
    for choice in ["A", "B", "C", "D"]: 
        question_option = json.loads(question_options)[choice]
        combo_user_prompt = f"{base_user_prompt} {question_option}"
        response = client.images.generate( 
            model="dall-e-3",
            prompt=combo_user_prompt,
            quality="standard",
            n=1,
        )
        image_links.append(response.data[0].url)
    return image_links

# Function to regenerate specific images
def regenerate_image(current_images, current_descriptions, images_to_regen, current_language):
    mapping = {"A": 0, "B": 1, "C": 2, "D": 3}
    image_user_prompts = {"English":"Create an image in a realistic art style depicting an office professional engaged in basic cyber security tasks at their workstation in a modern office environment. The individual should be portrayed realistically, using a business-casual attire, surrounded by vibrant but realistic technology interfaces. These interfaces should appear colorful and abstract, symbolizing the digital security tools the professional is interacting with, but remain plausible without any readable text. This scene should visually capture the focus and interaction of a regular office worker navigating cybersecurity protocols. This image should visually capture the esssence of the following action: ",
                          "Français":"Créez une image dans un style artistique réaliste représentant un professionnel de bureau engagé dans des tâches de base en matière de cybersécurité sur son poste de travail dans un environnement de bureau moderne. L'individu doit être représenté de manière réaliste, en utilisant une tenue professionnelle décontractée, entouré d'interfaces technologiques dynamiques mais réalistes. Ces interfaces doivent apparaître colorées et abstraites, symbolisant les outils de sécurité numérique avec lesquels le professionnel interagit, mais rester plausibles sans aucun texte lisible. Cette scène doit capturer visuellement l'attention et l'interaction d'un employé de bureau ordinaire naviguant dans les protocoles de cybersécurité. Cette image doit capturer visuellement l’essence de l’action suivante: "}
    base_user_prompt = image_user_prompts[current_language]
    with st.spinner("Regenerating images, thank you for your patience..."):
        for i, image in enumerate(images_to_regen):
            combo_user_prompt = f"{base_user_prompt} {current_descriptions[image]}"
            response = client.images.generate( 
                model="dall-e-3",
                prompt=combo_user_prompt,
                quality="standard",
                n=1,
            )
            current_images[mapping[image]] = response.data[0].url
    
    return current_images

# Function to handle sidebar inputs
def sidebar_handler(current_option, scenarioList, current_language):
    if current_option == "Custom" or current_option == "Coutume":
        desired_scenario= st.sidebar.text_area("Enter a prompt here")
    else:
        desired_scenario = st.sidebar.selectbox("Scénario informatique à générer",
                                            options=scenarioList[current_language]['Scenarios'])
    return desired_scenario

# Function to download and store images locally
def download_and_store_images(image_links):
    image_paths = []
    for index, image_link in enumerate(image_links):
        try:
            # Download the image from the URL
            with requests.get(image_link) as response:
                response.raise_for_status()  # Will raise an exception for 4XX/5XX status codes

                # Create a named temporary file to save the image
                with tempfile.NamedTemporaryFile(suffix=f"_choice_{index+1}.png", delete=False) as temp_file:
                    # Write the image content to the temporary file
                    temp_file.write(response.content)
                    temp_file_path = temp_file.name

                # Adding to List
                image_paths.append(temp_file_path)
                
        except requests.RequestException as e:
            print(f"Failed to download the image from {image_link}: {e}")
            continue
        except IOError as e:
            print(f"Error writing file for {image_link}: {e}")
            continue

    return image_paths

# Function to create a ZIP file containing images and JSON data
def create_sample_zip(images, json_data):
    # Create a named temporary file for JSON with automatic deletion
    with tempfile.NamedTemporaryFile(mode='w+', suffix="_question_answers.json", delete=False) as temp_json_file:
        json.dump(json.loads(json_data), temp_json_file)
        temp_json_path = temp_json_file.name

    # Create a temporary directory to hold the images and JSON file
    with tempfile.TemporaryDirectory() as temp_dir:
        if images != None:
        # Copy image files to the temporary directory
            for image_path in images:
                shutil.copy(image_path, temp_dir)
        # Copy JSON file to the temporary directory
        if temp_json_path != None:
            shutil.copy(temp_json_path, temp_dir)

        # Zip the directory
        zip_file_path = "sample_files.zip"
        with ZipFile(zip_file_path, 'w') as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arc_name)

    # Clean up the temporary JSON file explicitly
    if temp_json_path != None:
        os.remove(temp_json_path)
    if images != None:
        for image_path in images:
            os.remove(image_path)

    return zip_file_path

# Run the main function
if __name__ == "__main__":
    main()
