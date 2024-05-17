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
api_key = os.getenv("CYBERSECURITY_OPENAI_API_KEY") 
client = OpenAI(api_key=api_key)


# Defining Helper Functions

def generate_question(selected_language, selected_quiz_type, selected_category, previous_response):
    promptOptionList = {
        'English': {'Plain text multiple choice': f"Create a scenario-based multiple choice question about {selected_category} with four options and one correct answer. Format your output as a JSON response with the following keys: 'Question', 'A', 'B', 'C', 'D', 'Correct Answer'. For the 'Correct Answer' key, the value should be the letter corresponding to the correct option.", 
                    'Image-based': f"Generate a scenario-based question about {selected_category} where the user must select the incorrect action or response from four images. Only one image description should correspond with an incorrect action. All other options should be an appropriate response but not provide justification as to why they are correct. Format your output as a JSON response with the following keys: 'Question', 'A', 'B', 'C', 'D', 'Incorrect Answer'. For the 'Incorrect Answer' key, the value should be the letter corresponding to the incorrect option.",
                    'Custom': f"""Given an overview of a new cybersecurity threat to end users, generate the following items: 

                    1. A small vignette that frames a way the threat may possibly appear.
                    2. A scenario-based question relating to the vignette on what action one of the characters in the vignette, representing the end user, should take.
                    3. Four possible answer choices relating to the vignette and question.

                    Output the response in a JSON format with the following keys: 'Scenario', 'Question', 'A', 'B', 'C', 'D', 'Answer', The output must only contain one correct answer.  The 'Answer' value should correspond with the key that has the description of the correct action.

                    Example threat overview: {selected_category}"""},
                    # Add Custom Image from JSON

        'Français': {'Choix multiple en texte brut': f"Créez une question à choix multiples basée sur un scénario sur {selected_category} avec quatre options et une seule réponse correcte. Formatez votre sortie sous forme de réponse JSON avec les clés suivantes : « Question », « A », « B », « C », « D », « Bonne réponse ». Pour la touche 'Réponse correcte', la valeur doit être la lettre correspondant à l'option correcte.", 
                    "Basé sur l'image": f"Générez une question basée sur un scénario sur {selected_category} dans laquelle l'utilisateur doit sélectionner l'action ou la réponse incorrecte parmi quatre images. Une seule description d’image doit correspondre à une action incorrecte. Toutes les autres options doivent constituer une réponse appropriée mais ne doivent pas justifier pourquoi elles sont correctes. Formatez votre sortie sous forme de réponse JSON avec les clés suivantes : « Question », « A », « B », « C », « D », « Réponse incorrecte ». Pour la touche « Réponse incorrecte », la valeur doit être la lettre correspondant à l'option incorrecte.",
                    'Coutume': f"""Compte tenu d’un aperçu d’une nouvelle menace de cybersécurité pour les utilisateurs finaux, générez les éléments suivants :

                    1. Une petite vignette qui décrit la façon dont la menace peut éventuellement apparaître.
                    2. Une question basée sur un scénario relative à la vignette sur l'action que devrait entreprendre l'un des personnages de la vignette, représentant l'utilisateur final.
                    3. Quatre choix de réponses possibles relatifs à la vignette et à la question.

                    Affichez la réponse au format JSON avec les clés suivantes : "Scénario", "Question", "A", "B", "C", "D", "Réponse". La sortie ne doit contenir qu'une seule réponse correcte. La valeur « Réponse » doit correspondre à la clé qui contient la description de l'action correcte.

                    Exemple de présentation des menaces : {selected_category}"""}
                    # Add Custom Image from JSON
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

def sidebar_handler(current_option, scenarioList, current_language):
    if current_option == "Custom" or current_option == "Coutume":
        desired_scenario= st.sidebar.text_area("Enter a prompt here")
    else:
        desired_scenario = st.sidebar.selectbox("Scénario informatique à générer",
                                            options=scenarioList[current_language]['Scenarios'])
    return desired_scenario

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

def create_sample_json(json_data):
    # Create a named temporary file
    with tempfile.NamedTemporaryFile(mode='w+', suffix=".json", delete=False) as temp_file:
        # Write the JSON data to the file
        json.dump(json.loads(json_data), temp_file)
        # Save the path of the temporary file
        file_path = temp_file.name

    # The file will persist after closing the block, so it can be accessed later
    return file_path
    
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

def main():
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

    desired_language = st.sidebar.radio("Langue souhaitée", ["English", "Français"], index=1)

    scenarioOptionsList = {
        'English': {'Scenarios': ["phishing attacks", "spear phishing", "social engineering", "ransomware", "CEO fraud", "baiting", "Wi-Fi eavesdropping", "website spoofing", "password reuse", "insider threats", "outdated software", "convincing contractors", "helpful hackers"], 'Tones': ["Casual", "Professional"], 'Quiz Types': ["Plain text multiple choice", "Image-based", "Custom"]},
        'Français': {'Scenarios': ["attaques de phishing", "l'hameçonnage ciblé", "l'ingénierie sociale", "rançongiciels", "fraude au PDG", "l'appâtage", "l'écoute clandestine", "réutilisation de mot de passe", "imprimantes non sécurisées", "logiciels obsolètes", "entrepreneurs convaincants", "hackers utiles"], 'Tones': ["Décontracté", "Professionnel"], 'Quiz Types': ["Choix multiple en texte brut", "Basé sur l'image", "Coutume"]}
    }
    desired_quiz = st.sidebar.selectbox("Type de quiz souhaité", options = scenarioOptionsList[desired_language]['Quiz Types'])
    desired_scenario = sidebar_handler(desired_quiz, scenarioOptionsList, desired_language)

    st.title(language_labels[desired_language]["title"])
                                      
    storage_states = ["generated_output", "output_to_modify", "current_chat_id", "generated_images", "generated_descriptions", "export_generated"]
    flag_states = ["feedback_displayed", "edits_requested", "download_complete", "regeneration_requested"]
    
    for i, item in enumerate(storage_states):
        if item not in st.session_state:
            st.session_state[item] = None

    for i, item in enumerate(flag_states):
        if item not in st.session_state:
            st.session_state[item] = False
 
    if st.session_state.generated_output == None:
        st.write(language_labels[desired_language]["initial instructions"])
       
        if st.button("Générer la sortie" if desired_language == "Français" else "Generate Output"):
            complete_response = generate_question(desired_language, desired_quiz, desired_scenario, st.session_state.generated_output)
            st.session_state.generated_output = complete_response[0]
            st.session_state.current_chat_id = complete_response[1]
            st.session_state.feedback_displayed = False
            st.rerun()

    if st.session_state.generated_output:

        # TODO Refactor into a generic function that is called based on current state, dictated by language + quiz_type. Sidepanel should disappear after first generation to avoid cross-language issues. 
        
        # Output Display(desired_quiz, desired_language)
        # st.sidebar.clear()

        if desired_quiz in ["Plain text multiple choice", "Choix multiple en texte brut", "Coutume", "Custom"]: # TODO Fix to become session state dependent - edge case around swapping choices mid-stream
            current_options = []
            st.subheader("Sortie générée:")
            st.write(json.loads(st.session_state.generated_output)["Question"])
            
            for choice in ["A", "B", "C", "D"]:
                current_options.append(json.loads(st.session_state.generated_output)[choice])
            # Display each choice as a selectable multiple choice item
            user_choice = st.radio("Les choix:", options = current_options)

            if st.button("Regenerate" if desired_language == "English" else "Régénérer"):
                complete_response = generate_question(desired_language, desired_quiz, desired_scenario, st.session_state.generated_output)
                st.session_state.generated_output = complete_response[0]
                st.rerun()
            
            if st.button("Edit" if desired_language == "English" else "Modifier"):
                st.session_state.output_to_modify = st.session_state.generated_output
                st.text_input(st.session_state.output_to_modify)
                st.session_state.edits_requested = True
                st.session_state.generated_output = False
                st.rerun()

            if st.button("Export" if desired_language == "English" else "Exporter"):
                # TODO Add state management here for the generated output so the file is only created once. 
                
                sample_file_path = create_sample_json(st.session_state.generated_output)
                with open(sample_file_path, "w+b") as file:
                    file_contents = file.read()
                if st.download_button(label="Download", data=file_contents, file_name="sample_file.json", mime="application/json"):
                    st.session_state.download_complete = True
                if st.session_state.download_complete == True:
                    # Clean up: Delete the temporary directory and its contents
                    os.remove(sample_file_path)
                    os.rmdir(os.path.dirname(sample_file_path))
                    st.session_state.download_complete = False

            if st.button("Reset" if desired_language == "English" else "Réinitialiser"):
                session_state_keys = st.session_state.keys()
                for key in session_state_keys:
                    del st.session_state[key]
                st.rerun()
        else:
            # Handle Image Generation and Associated Functions
            # Reminder st.session_state.generated_output is assigned to the output at this juncture. 
            st.subheader("Sortie générée:")
            st.write(json.loads(st.session_state.generated_output)["Question"])
            
            if st.session_state.generated_images == None:
                current_options = {}
                # Gen Descriptions
                for choice in ["A", "B", "C", "D"]:
                    current_options[choice] = json.loads(st.session_state.generated_output)[choice]
                st.session_state.generated_descriptions = current_options
                
                # Image Gen Here
                with st.spinner("Génération d'images, merci pour votre patience!"):
                    st.session_state.generated_images = generate_image(st.session_state.generated_output, desired_language)
                st.rerun()

            st.image(st.session_state.generated_images[0], caption=f'A. {st.session_state.generated_descriptions["A"]}')
            st.image(st.session_state.generated_images[1], caption=f'B. {st.session_state.generated_descriptions["B"]}')
            st.image(st.session_state.generated_images[2], caption=f'C. {st.session_state.generated_descriptions["C"]}')
            st.image(st.session_state.generated_images[3], caption=f'D. {st.session_state.generated_descriptions["D"]}')

            if st.button("Regenerate Images" if desired_language == "English" else "Régénérer les images"):
                st.session_state.output_to_modify = st.session_state.generated_output
                st.text_input(st.session_state.output_to_modify)
                st.session_state.regeneration_requested = True
                st.session_state.generated_output = False
                st.rerun()

            # Intention here is to target captions/descriptions only
            
            if st.button("Edit Captions" if desired_language == "English" else "Modifier les légendes"):
                st.session_state.output_to_modify = st.session_state.generated_output
                st.text_input(st.session_state.output_to_modify)
                st.session_state.edits_requested = True
                st.session_state.generated_output = False
                st.rerun()

            # Goal here is to generate a zip file that contains the json and image files (as png)

            if st.button("Export" if desired_language == "English" else "Exporter"):
                # TODO Add Better State Management Here to avoid continuous calls. 
                
                image_paths = download_and_store_images(st.session_state.generated_images)
                sample_zip = create_sample_zip(image_paths, st.session_state.generated_output)
                
                # Create the sample ZIP file
                with open(sample_zip, "r+b") as file:
                    file_contents = file.read()
                    # TODO: With better state management, Add a function to iterate through each file and remove the tempfile part of the name. 
                if st.download_button(label="Download", data=file_contents, file_name="sample_files.zip", mime="application/zip"):
                    st.session_state.download_complete = True
                if st.session_state.download_complete == True:
                    # Image Cleanup
                    for image_path in image_paths:
                        os.remove(image_path)

                    #Zip Cleanup
                    os.remove(sample_zip)
                    os.rmdir(os.path.dirname(sample_zip))

            if st.button("Reset" if desired_language == "English" else "Réinitialiser"):
                session_state_keys = st.session_state.keys()
                for key in session_state_keys:
                    del st.session_state[key]
                st.rerun()

    if st.session_state.edits_requested:
            st.session_state.output_to_modify = st.text_area("The current quiz objects." if desired_language == "English" else "Les objets du quiz en cours.", st.session_state.output_to_modify)
            if st.button("Submit Change Request" if desired_language == "English" else "soumettre une demande de modification"):
                st.session_state.generated_output = st.session_state.output_to_modify
                if st.session_state.generated_images != None:
                    current_options = {}
                    for choice in ["A", "B", "C", "D"]:
                        current_options[choice] = json.loads(st.session_state.output_to_modify)[choice]
                st.session_state.generated_descriptions = current_options   
                st.session_state.edits_requested = False
                st.rerun()
    
    if st.session_state.regeneration_requested:
        st.image(st.session_state.generated_images[0], caption=f'A. {st.session_state.generated_descriptions["A"]}')
        st.image(st.session_state.generated_images[1], caption=f'B. {st.session_state.generated_descriptions["B"]}')
        st.image(st.session_state.generated_images[2], caption=f'C. {st.session_state.generated_descriptions["C"]}')
        st.image(st.session_state.generated_images[3], caption=f'D. {st.session_state.generated_descriptions["D"]}')
        selected_options = st.multiselect("Select options:", list(st.session_state.generated_descriptions))
        if st.button("Select Images to Regenerate" if desired_language == "English" else "Demander de nouvelles image(s)"):
            st.session_state.generated_images = regenerate_image(st.session_state.generated_images, st.session_state.generated_descriptions, selected_options, desired_language)
            st.session_state.regeneration_requested = False
            st.session_state.generated_output = st.session_state.output_to_modify
            st.rerun()
        
if __name__ == "__main__":
    main()
