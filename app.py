import streamlit as st
from openai import OpenAI
import os

api_key = os.getenv("CYBERSECURITY_OPENAI_API_KEY")  # Used in production
client = OpenAI(api_key=api_key)

def get_completion(prompt, model="gpt-3.5-turbo", max_tokens=200):
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()

def generate_image(prompt: str):
    # Placeholder function for generating image URLs
    # Replace this with your actual implementation
    return "https://example.com/image.png"

def generate_question(prompt):
    print("Prompt:", prompt)  # Debugging print

    if "plain text" in prompt.lower() and "image" in prompt.lower():
        question = get_completion(prompt)
        answer_options = get_completion(f"Generate four answer options for the following question:\n{question}\n")
        answer_options = answer_options.split("\n")

        output = f"Question:\n{question}\n\n"

        image_prompt = f"Generate an image illustrating the following question:\n{question}"
        image_url = generate_image(image_prompt)
        output += f"Image: {image_url}\n\nAnswers:\n"

        for i, option in enumerate(answer_options):
            output += f"{chr(65+i)}. {option.strip()}\n"
            image_prompt = f"Generate an image illustrating the answer option: {option.strip()}"
            image_url = generate_image(image_prompt)
            output += f"Image: {image_url}\n\n"

    elif "scenario image" in prompt.lower():
        question = get_completion(prompt)
        answer_options = get_completion(f"Generate four answer options for the following question:\n{question}\n")
        answer_options = answer_options.split("\n")

        output = f"Question:\n{question}\n\n"

        image_prompt = f"Generate an image illustrating the scenario described in the following question:\n{question}"
        image_url = generate_image(image_prompt)
        output += f"Image: {image_url}\n\nAnswers:\n"

        for i, option in enumerate(answer_options):
            output += f"{chr(65+i)}. {option.strip()}\n"
            image_prompt = f"Generate an image illustrating the answer option: {option.strip()}"
            image_url = generate_image(image_prompt)
            output += f"Image: {image_url}\n\n"

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

        for i, option in enumerate(answer_options):
            image_prompt = f"Generate an image illustrating the answer option: {option.strip()}"
            image_url = generate_image(image_prompt)
            output += f"{chr(65+i)}. {option.strip()}\n"
            output += f"Image: {image_url}\n\n"

    print("Answer Options:", answer_options)  # Debugging print
    return output

def main():
    st.title("Cybersecurity Question Generator")
    prompt = st.text_input("Enter a prompt to generate the desired output:")

    if st.button("Generate Output"):
        output = generate_question(prompt)
        st.subheader("Generated Output:")
        st.text(output)

if __name__ == "__main__":
    main()
