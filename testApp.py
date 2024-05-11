import streamlit as st
from openai import OpenAI
import os
from PIL import Image
import json
import os
import shutil
from zipfile import ZipFile
import tempfile

# General Housekeeping


api_key = "SECRET"  # Used in production
client = OpenAI(api_key=api_key)


# Defining Helper Functions

def generate_question(selected_language, selected_quiz_type, selected_category, previous_response):
    promptOptionList = {
        'English': {'Plain text multiple choice': f"Create a scenario-based multiple choice question about {selected_category} with four options and one correct answer. Format your output as a JSON response with the following keys: 'Question', 'A', 'B', 'C', 'D', 'Correct Answer'. For the 'Correct Answer' key, the value should be the letter corresponding to the correct option.", 
                    'Image-based': f"Generate a scenario-based question about {selected_category} where the user must select the incorrect action or response from four images. Only one image description should correspond with an incorrect action. All other options should be an appropriate response but not provide justification as to why they are correct. Provide a detailed description of each image. Format your output as a JSON response with the following keys: 'Question', 'A', 'B', 'C', 'D', 'Incorrect Answer'. For the 'Incorrect Answer' key, the value should be the letter corresponding to the incorrect option. Each letter should have only two associated keys - 'Description' and 'Gen AI Description'. The 'Description' should clearly explain the possible action without leading the reader. The 'Gen AI Description' should be a prompt for a generative AI image generator that relates to the 'Description'."},
        'Français': {'Choix multiple en texte brut': f"Créez une question à choix multiples basée sur un scénario sur {selected_category} avec quatre options et une seule réponse correcte. Formatez votre sortie sous forme de réponse JSON avec les clés suivantes : « Question », « A », « B », « C », « D », « Bonne réponse ». Pour la touche 'Réponse correcte', la valeur doit être la lettre correspondant à l'option correcte.", 
                    "Basé sur l'image": f"Générez une question basée sur un scénario sur {selected_category} dans laquelle l'utilisateur doit sélectionner l'action ou la réponse incorrecte parmi quatre images. Une seule description d’image doit correspondre à une action incorrecte. Toutes les autres options doivent constituer une réponse appropriée mais ne doivent pas justifier pourquoi elles sont correctes. Fournissez une description détaillée de chaque image. Formatez votre sortie sous forme de réponse JSON avec les clés suivantes : « Question », « A », « B », « C », « D », « Réponse incorrecte ». Pour la touche « Réponse incorrecte », la valeur doit être la lettre correspondant à l'option incorrecte. Chaque lettre doit avoir deux clés associées : « Description » et « Description Gen AI ». La description doit expliquer clairement l'action possible sans induire le lecteur. La « Description de l'IA de génération » doit être une invite pour un générateur d'images d'IA générative lié à la « Description »"}
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
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature = 0.1,
        response_format={"type": "json_object"},
    )

    """
    # Check for proper context
    if selected_quiz_type in ["Image-based", "Basé sur l'image"]:
        validated_output = False
        while not validated_output:
            if selected_quiz_type in ["Image-based", "Basé sur l'image"]:
                test_dict = json.loads(response.choices[0].message.content.strip())
                with st.spinner("Checking output..."):
                    if "Description" not in test_dict:
                        print("Validation failed!, regenerating!")
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=messages,
                            temperature = 0.1,
                            response_format={"type": "json_object"},
                        )
                    else:
                        validated_output = True
                        print(response.choices[0].message.content.strip())
    """
    print("Done!")
    return [response.choices[0].message.content.strip(), response.id]

def generate_image(desc_list):
    image_links = []
    for index, item in enumerate(desc_list):
        response = client.images.generate(
            model="dall-e-2",
            prompt=desc_list[index],
            size="256x256",
            quality="standard",
            n=1,
        )
        image_links.append(response.data[0].url)
    return image_links

def regenerate_image(current_images, images_to_regen):
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

def create_sample_json(json_data):
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Create a sample JSON data
    json_data = json_data
    file_path = os.path.join(temp_dir, "sample_file.json")

    # Write the JSON data to the file
    with open(file_path, "w") as file:
        json.dump(json_data, file)
    
    return file_path
    
def create_sample_zip(images, jsons):
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Example image and text files
    image_paths = images
    text_paths = jsons

    # Save images and text files into the temporary directory
    for image_path in image_paths:
        shutil.copy(image_path, temp_dir)
    for text_path in text_paths:
        shutil.copy(text_path, temp_dir)

    # Zip the directory
    zip_file_path = "sample_files.zip"
    with ZipFile(zip_file_path, "w") as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), temp_dir))

    # Delete the temporary directory
    shutil.rmtree(temp_dir)

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
        if desired_quiz in ["Plain text multiple choice", "Choix multiple en texte brut"]: # Fix to become session state dependent - edge case around swapping choices mid-stream
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
                if desired_quiz in ["Plain text multiple choice", "Choix multiple en texte brut"]:
                    sample_file_path = create_sample_json(st.session_state.generated_output)
                    with open(sample_file_path, "rb") as file:
                        file_contents = file.read()
                    st.download_button(label="Download", data=file_contents, file_name="sample_file.json", mime="application/json")
                    # Clean up: Delete the temporary directory and its contents
                    os.remove(sample_file_path)
                    os.rmdir(os.path.dirname(sample_file_path))
                else:
                    pass

            if st.button("Reset" if desired_language == "English" else "réinitialiser"):
                session_state_keys = st.session_state.keys()
                for key in session_state_keys:
                    del st.session_state[key]
                st.rerun()
        else:
            st.subheader("Generated Output:")
            current_options = []
            image_desc = []
            st.write(json.loads(st.session_state.generated_output)["Question"])
            if st.session_state.generated_images == None:
                for choice in ["A", "B", "C", "D"]:
                    temp_load = json.loads(st.session_state.generated_output)
                    current_options.append(temp_load[choice]["Description"][choice])
                    image_desc.append(temp_load[choice]["Description"][choice])
                st.session_state.generated_images = generate_image(image_desc)
                st.session_state.generated_descriptions = current_options
                st.rerun()

            # 2 x 2 Grid    
            col1, col2 = st.columns(2)
            with col1:
                st.image(st.session_state.generated_images[0], caption=st.session_state.generated_descriptions[0])
                st.image(st.session_state.generated_images[2], caption=st.session_state.generated_descriptions[2])
            with col2:
                st.image(st.session_state.generated_images[1], caption=st.session_state.generated_descriptions[1])
                st.image(st.session_state.generated_images[3], caption=st.session_state.generated_descriptions[3])

            # Display each choice as a selectable multiple choice item
            selected_option = st.selectbox("Select an option:", st.session_state.generated_descriptions)

            if st.button("Regenerate Images" if desired_language == "English" else "Régénérer les images"):
                pass
            
            if st.button("Edit Text" if desired_language == "English" else "Éditer le texte"):
                st.session_state.output_to_modify = st.session_state.generated_output
                st.text_input(st.session_state.output_to_modify)
                st.session_state.edits_requested = True
                st.session_state.generated_output = False
                st.rerun()

            if st.button("Export" if desired_language == "English" else "Exporter"):
                pass 

            if st.button("Reset" if desired_language == "English" else "réinitialiser"):
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
                    image_desc = []
                    for choice in ["A", "B", "C", "D"]:
                        current_options.append(json.loads(json.loads(st.session_state.generated_output)[choice])["Description"][choice])
                        image_desc.append(json.loads(st.session_state.generated_output)[choice]["Gen AI Description"][choice])
                        st.session_state.generated_descriptions = current_options    
                st.session_state.edits_requested = False
                st.rerun()
        
if __name__ == "__main__":
    main()
