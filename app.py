import streamlit as st
from openai import OpenAI
import os

api_key = os.getenv("CYBERSECURITY_OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Function to get completion with adjusted temperature
def get_completion(prompt, model="gpt-3.5-turbo", temperature=0):
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content

# Function to generate the image
def generate_image(text, size="256x256"):
    if not api_key:
        st.error("OpenAI API key is not set. Please set it in your environment variables.")
        return

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

# Function to generate question and corresponding images
def generate_question(prompt):
    print("Prompt:", prompt)  # Debugging print

    if "plain text" in prompt.lower() and "image" in prompt.lower():
        question = get_completion(prompt)
        answer_options = get_completion(f"Generate four answer options for the following question:\n{question}\n", temperature=0)
        answer_options = answer_options.split("\n")

        output = f"Question:\n{question}\n\n"

        for option in answer_options:
            image_prompt = f"Generate an image illustrating the answer option: {option.strip()}"
            with st.spinner('Generating Image...'):
                image_url = generate_image(image_prompt, size="256x256")
            output += f"{option.strip()}\n"
            output += f"![AI GENERATED IMAGE]({image_url})\n\n"

    elif "scenario image" in prompt.lower():
        question = get_completion(prompt)
        answer_options = get_completion(f"Generate four answer options for the following question:\n{question}\n", temperature=0)
        answer_options = answer_options.split("\n")

        output = f"Question:\n{question}\n\n"

        for option in answer_options:
            image_prompt = f"Generate an image illustrating the answer option: {option.strip()}"
            with st.spinner('Generating Image...'):
                image_url = generate_image(image_prompt, size="256x256")
            outpu
