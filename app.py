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

# Function to generate the image
def generate_image(text):
    if not api_key:
        st.error("OpenAI API key is not set. Please set it in your environment variables.")
        return

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=text,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        st.error(f"Error generating image: {e}")
        return None

def generate_question(prompt):
    print("Prompt:", prompt)  # Debugging print

    if "plain text" in prompt.lower() and "image" in prompt.lower():
        question = get_completion(prompt)
        answer_options = get_completion(f"Generate four answer options for the following question:\n{question}\n")
        answer_options = answer_options.split("\n")

        output = f"Question:\n{question}\n\n"

        for option in enumerate(answer_options):
            image_prompt = f"Generate an image illustrating the answer option: {option.strip()}"
            with st.spinner('Generating Image...'):
                image_url = generate_image(image_prompt)
            output += f"{i+1}. {option.strip()}\n"
            output += f"![AI GENERATED IMAGE]({image_url})\n\n"

    elif "scenario image" in prompt.lower():
        question = get_completion(prompt)
        answer_options = get_completion(f"Generate four answer options for the following question:\n{question}\n")
        answer_options = answer_options.split("\n")

        output = f"Question:\n{question}\n\n"

        for option in enumerate(answer_options):
            image_prompt = f"Generate an image illustrating the answer option: {option.strip()}"
            with st.spinner('Generating Image...'):
                image_url = generate_image(image_prompt)
            output += f"{i+1}. {option.strip()}\n"
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

        for option in eunerate(answer_options):
            image_prompt = f"Generate an image illustrating the answer option: {option.strip()}"
            with st.spinner('Generating Image...'):
                image_url = generate_image(image_prompt)
            output += f"{i+1}. {option.strip()}\n"
            output += f"![AI GENERATED IMAGE]({image_url})\n\n"

    print("Answer Options:", answer_options)  # Debugging print
    return output

def main():
    st.title("Cybersecurity Question Generator")
    prompt = st.text_input("Enter a prompt to generate the desired output:")

    if st.button("Generate Output"):
        output = generate_question(prompt)
        st.subheader("Generated Output:")
        st.markdown(output, unsafe_allow_html=True)  # Allow markdown with HTML

if __name__ == "__main__":
    main()
