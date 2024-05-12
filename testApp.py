import streamlit as st
from openai import OpenAI
import os
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


api_key = "SECRET"  # Used in production
client = OpenAI(api_key=api_key)


# Defining Helper Functions

def generate_question(selected_language, selected_quiz_type, selected_category, previous_response):
    promptOptionList = {
        'English': {'Plain text multiple choice': f"Create a scenario-based multiple choice question about {selected_category} with four options and one correct answer. Format your output as a JSON response with the following keys: 'Question', 'A', 'B', 'C', 'D', 'Correct Answer'. For the 'Correct Answer' key, the value should be the letter corresponding to the correct option.", 
                    'Image-based': f"Generate a scenario-based question about {selected_category} where the user must select the incorrect action or response from four images. Only one image description should correspond with an incorrect action. All other options should be an appropriate response but not provide justification as to why they are correct. Format your output as a JSON response with the following keys: 'Question', 'A', 'B', 'C', 'D', 'Incorrect Answer'. For the 'Incorrect Answer' key, the value should be the letter corresponding to the incorrect option."},
        'Français': {'Choix multiple en texte brut': f"Créez une question à choix multiples basée sur un scénario sur {selected_category} avec quatre options et une seule réponse correcte. Formatez votre sortie sous forme de réponse JSON avec les clés suivantes : « Question », « A », « B », « C », « D », « Bonne réponse ». Pour la touche 'Réponse correcte', la valeur doit être la lettre correspondant à l'option correcte.", 
                    "Basé sur l'image": f"Générez une question basée sur un scénario sur {selected_category} dans laquelle l'utilisateur doit sélectionner l'action ou la réponse incorrecte parmi quatre images. Une seule description d’image doit correspondre à une action incorrecte. Toutes les autres options doivent constituer une réponse appropriée mais ne doivent pas justifier pourquoi elles sont correctes. Formatez votre sortie sous forme de réponse JSON avec les clés suivantes : « Question », « A », « B », « C », « D », « Réponse incorrecte ». Pour la touche « Réponse incorrecte », la valeur doit être la lettre correspondant à l'option incorrecte."}
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
    keyOptions = {"English":{"Plain text multiple choice":["Question", "A", "B", "C", "D", "Correct Answer"], "Image-based":["Question", "A", "B", "C", "D", "Incorrect Answer"]},
                  "Français": {"Choix multiple en texte brut":["Question", "A", "B", "C", "D", "Bonne réponse"], "Basé sur l'image":["Question", "A", "B", "C", "D", "Réponse incorrecte"]}}
    with st.spinner("Checking output..."):
        validation_failure = False
        keys = keyOptions[selected_language][selected_quiz_type]
        while not validated_output:
            test_dict = json.loads(response.choices[0].message.content.strip())
            for key in keys:
                if key not in test_dict:
                    st.error("Invalid Format Detected, regenerating.")
                    validation_failure = True
                    print(json.loads(response.choices[0].message.content.strip())) # TODO Remove, Testing only
                    sleep(5) # TODO Remove, Testing only
                    break 
            if not validation_failure:
                st.success("Format validated!")
                sleep(2)
                validated_output = True

    print("Done!") # TODO Remove, Testing only
    return [response.choices[0].message.content.strip(), response.id]

def generate_image(question_options, selected_language):
    image_links = []
    image_user_prompts = {"English":"Design a cartoon illustration in a pop art style featuring robots collaborating in a corporate office environment and utilizing technology like phones and computers. While avoiding text-based representations, the image should correspond to the following IT-related action:",
                          "Français":"Concevez une illustration de dessin animé représentant des robots experts en technologie collaborant dans un environnement de bureau d'entreprise animé, inspirée de l'action liée à l'informatique:"}
    image_system_prompts = {"English":"Let's create a vibrant and lively scene with our color choices! Think of bold and dynamic hues that evoke energy and excitement. Remember, we're avoiding text to focus solely on colorful visuals.",
                             "Français":"Créons une scène vibrante et vivante avec nos choix de couleurs! Pensez à des teintes audacieuses et dynamiques qui évoquent l’énergie et l’excitation. N'oubliez pas que nous évitons le texte pour nous concentrer uniquement sur des visuels colorés."}
    base_user_prompt = image_user_prompts[selected_language]
    system_prompt = image_system_prompts[selected_language]
    for choice in ["A", "B"]: # TODO ADD C and D - A and B only for testing
        question_option = json.loads(question_options)[choice]
        combo_user_prompt = f"{base_user_prompt} {question_option}"
        print(combo_user_prompt) # TODO Remove, Testing Only
        response = client.images.generate(
            model="dall-e-2",
            prompt=combo_user_prompt,
            quality="standard",
            n=1,
        )
        image_links.append(response.data[0].url)
    return image_links

def regenerate_image(current_images, images_to_regen):
    pass

def sidebar_handler(current_option, scenarioList, current_language):
    if current_option == "Custom" or current_option == "Coutume":
        desired_scenario= st.sidebar.text_area("Enter a prompt here")
    else:
        desired_scenario = st.sidebar.selectbox("Scénario informatique à générer",
                                            options=scenarioList[current_language]['Scenarios'])
    return desired_scenario

def create_sample_json(json_data):
    # Create a temporary file
    with tempfile.TemporaryFile(mode='w+', suffix= ".json", delete=False) as temp_file:
        # Write the JSON data to the file
        json.dump(json_data, temp_file)
    
    # Get the path of the temporary file
    file_path = temp_file.name
    
    return file_path

# TODO Make this the primary function so that the one above is gone.
    
def create_sample_zip(images, json_data):

    # Create a json temporary file
    with tempfile.TemporaryFile(mode='w+', suffix= "_question_answers.json", delete=False) as temp_file:
        # Write the JSON data to the file
        json.dump(json_data, temp_file)
    
    # Get the path of the temporary file
    file_path = temp_file.name
    
    # Create a temporary directory
    temp_dir_2 = tempfile.TemporaryDirectory()

    # Example image and text files
    image_paths = images

    # Save images and text files into the temporary directory
    for image_path in image_paths:
        shutil.copy(image_path, temp_dir_2.name)
    shutil.copy(file_path, temp_dir_2.name)

    # Zip the directory
    zip_file_path = "sample_files.zip"
    with ZipFile(zip_file_path, "w") as zipf:
        for root, _, files in os.walk(temp_dir_2.name):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), temp_dir_2.name))

    # Delete the temporary directory
    shutil.rmtree(temp_dir_2.name)

    os.remove(file_path)

    return zip_file_path

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
    if "edits_requested" not in st.session_state:
        st.session_state.edits_requested = False
    if "output_to_modify" not in st.session_state:
        st.session_state.output_to_modify = None
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    if "generated_images" not in st.session_state:
        st.session_state.generated_images = None
    if "generated_descriptions" not in st.session_state:
        st.session_state.generated_descriptions = None
 
    if st.session_state.generated_output == None:
        st.write("Select your options from the left, once complete, your custom item(s) will be generated below")
       
        if st.button("Générer la sortie" if desired_language == "Français" else "Generate Output"):
            complete_response = generate_question(desired_language, desired_quiz, desired_scenario, st.session_state.generated_output)
            st.session_state.generated_output = complete_response[0]
            st.session_state.current_chat_id = complete_response[1]
            st.session_state.feedback_displayed = False
            st.rerun()

    if st.session_state.generated_output:

        # TODO Refactor into a generic function that is called based on current state, dictated by language + quiz_type

        if desired_quiz in ["Plain text multiple choice", "Choix multiple en texte brut"]: # TODO Fix to become session state dependent - edge case around swapping choices mid-stream
            current_options = []
            st.subheader("Generated Output:")
            st.write(json.loads(st.session_state.generated_output)["Question"])
            #Add condition here for checking if image quiz or multiple choice only.
            for choice in ["A", "B", "C", "D"]:
                current_options.append(json.loads(st.session_state.generated_output)[choice])
            # Display each choice as a selectable multiple choice item
            user_choice = st.radio("Choices/Les choix:", options = current_options)

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
                sample_file_path = create_sample_json(st.session_state.generated_output)
                with open(sample_file_path, "rb") as file:
                    file_contents = file.read()
                st.download_button(label="Download", data=file_contents, file_name="sample_file.json", mime="application/json")
                # Clean up: Delete the temporary directory and its contents
                os.remove(sample_file_path)
                os.rmdir(os.path.dirname(sample_file_path))
            else:
                pass

            if st.button("Reset" if desired_language == "English" else "Réinitialiser"):
                session_state_keys = st.session_state.keys()
                for key in session_state_keys:
                    del st.session_state[key]
                st.rerun()
        else:
            # Handle Image Generation and Associated Functions
            # Reminder st.session_state.generated_output is assigned to the output at this juncture. 
            st.subheader("Generated Output:")
            st.write(json.loads(st.session_state.generated_output)["Question"])
            
            if st.session_state.generated_images == None:
                current_options = []
                # Gen Descriptions
                for choice in ["A", "B"]: # TODO ADD C and D - A and B only for testing
                    current_options.append(json.loads(st.session_state.generated_output)[choice])
                st.session_state.generated_descriptions = current_options
                
                # Image Gen Here
                with st.spinner("Generating images, thank you for your patience!"):
                    st.session_state.generated_images = generate_image(st.session_state.generated_output, desired_language)
                st.rerun()

            # 2-Image Test
            st.image(st.session_state.generated_images[0], caption=st.session_state.generated_descriptions[0])
            st.image(st.session_state.generated_images[1], caption=st.session_state.generated_descriptions[1])

            if st.button("Regenerate Images" if desired_language == "English" else "Régénérer les images"):
                pass

            # Intention here is to target captions/descriptions only
            
            if st.button("Edit Captions" if desired_language == "English" else "Modifier les légendes"):
                st.session_state.output_to_modify = st.session_state.generated_output
                st.text_input(st.session_state.output_to_modify)
                st.session_state.edits_requested = True
                st.session_state.generated_output = False
                st.rerun()

            # Goal here is to generate a zip file that contains the json and image files (as png)

            if st.button("Export" if desired_language == "English" else "Exporter"):
                image_paths = []
                file_downloaded = False
                for index, imageLink in enumerate(st.session_state.generated_images):
                    # Download the image from the URL
                    response = requests.get(imageLink)
                    if response.status_code != 200:
                        raise Exception("Failed to download the image")
                    
                    # Create a temporary file to save the image
                    temp_file = tempfile.TemporaryFile(suffix=f"_choice_{index+1}.png", delete=False)

                    # Write the image content to the temporary file
                    with open(temp_file.name, "wb") as file:
                        file.write(response.content)
                    
                    # Adding to List
                    image_paths.append(temp_file.name)
                sample_zip = create_sample_zip(image_paths, st.session_state.generated_output)

                # Create the sample ZIP file
                with open(sample_zip, "r+b") as file:
                    file_contents = file.read()
                if st.download_button(label="Download", data=file_contents, file_name="sample_files.zip", mime="application/zip"):
                    file_downloaded = True
                if file_downloaded:
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

              
    if st.session_state.feedback_displayed:
        if st.button("Next" if desired_language == "English" else "Suivant"):
            st.session_state.generated_output = None
            st.session_state.feedback_displayed = False
            st.rerun()

    if st.session_state.edits_requested:
            st.session_state.output_to_modify = st.text_area("The current quiz objects." if desired_language == "English" else "Les objets du quiz en cours.", st.session_state.output_to_modify)
            if st.button("Submit Change Request" if desired_language == "English" else "soumettre une demande de modification"):
                st.session_state.generated_output = st.session_state.output_to_modify
                if st.session_state.generated_images != None:
                    current_options = []
                    for choice in ["A", "B", "C", "D"]:
                        current_options.append(json.loads(st.session_state.generated_output)[choice])
                        st.session_state.generated_descriptions = current_options    
                st.session_state.edits_requested = False
                st.rerun()
        
if __name__ == "__main__":
    main()
