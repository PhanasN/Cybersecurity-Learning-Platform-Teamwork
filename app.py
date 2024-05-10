import streamlit as st
from openai import OpenAI
import os

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
        output = "Le type de prompt n'est pas pris en charge."

    return output

# New functions to handle additional image regenerations based on the previously generated images

def save_image_from_url(image_url):
    # Send a GET request to the image URL
    response = requests.get(image_url)
    response.raise_for_status()  # Check if the request was successful

    # Open the image from the bytes of the response content
    with Image.open(io.BytesIO(response.content)) as image:
        # Use tempfile to create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            image.save(tmp_file, 'PNG')
            print(f"Image saved temporarily at {tmp_file.name}")
            return tmp_file.name

def regenerate_image(image):
    response = client.images.create_variation(
    image=open(image, "rb"),
    n=1,
    size="1024x1024"
    )
    return response['data'][0]['url']

def main():
    st.title("Cybersecurity Question Generator")
    prompt = st.text_input("Enter a prompt to generate the desired output:")

    # Filer for localization and menu options
    scenarioOptionsList = {
        'English':{'Scenarios':["English 1", "English 2"], 'Tones': ["Casual", "Professional"]},
        'Français': {'Scenarios':["French 1", "French 2"], 'Tones': ["FCasual", "FProfessional"]}
                 }

    # Side panel options
    desired_language = st.sidebar.radio("Desired language/Langue souhaitée", ["English", "Français"], index = 0)
    desired_scenario = st.sidebar.selectbox("IT scenario to generate/Scénario informatique à générer", options = scenarioOptionsList[desired_language]['Scenarios'])
    desired_tone = st.sidebar.selectbox("Desired script tone/Ton de script souhaité", options = scenarioOptionsList[desired_language]['Tones'])

    if st.button("Generate Output"):
        output = generate_question(prompt)
        st.subheader("Generated Output:")
        st.markdown(output, unsafe_allow_html=True)  # Allow markdown with HTML

    # Need state management to allow for smooth regeneration and for things to not disappear the second a menu option is changed, forcing refresh

if __name__ == "__main__":
    main()
