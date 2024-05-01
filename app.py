import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import os

# Authentication

# Parent Helper Functions for Export:

def exportClip():
  pass

def exportQuiz():
  pass

def exportQuizandClip():
  pass

# Helper Functions for Content Generation

def scenarioScriptGeneration():
  pass

def scenarioVideoGeneration():
  pass

# Breaking apart generation and quiz creation

def scenarioGeneration():
  st.title("Scenario Generation")
  scenarioOptionsList = {
        'English':{'Scenarios':["English 1", "English 2"], 'Tones': ["Casual", "Professional"]},
        'Français': {'Scenarios':["French 1", "French 2"], 'Tones': ["FCasual", "FProfessional"]}
                 }

  components.iframe("https://invideo.io/", height=500) # Likely change to general text box for additional context with 2 buttons. 1 will be generate script, the second will be generate video

  #userInputs
  # TO DO - add dynamic language swap based on desired_language selected - change things to assume French as default
  desired_language = st.sidebar.radio("Desired Language", ["English", "Français"], index = 0)
  desired_scenario = st.sidebar.selectbox("IT Scenario to Generate", options = scenarioOptionsList[desired_language]['Scenarios'])
  desired_tone = st.sidebar.selectbox("Desired Script Tone", options = scenarioOptionsList[desired_language]['Tones'])

  # Main Area

  # Four at Bottom after scenario generation - Generate Script, Generate Video, Regenerate [If generated content], Move onto Quiz Generation

# Helper Functions for Content Generation

def quizGeneration():
  pass

def quizFormatting():
  pass

def quizGen():
  englishTest = ["Spearfishing", "CEO Impersonation"]
  frenchTest = ["French 1", "French 2"]
  st.title("Standard Quiz Generation")
  
  quizOptionsList = {
        'English':{'Scenarios':["English1", "English 2"], 'Tones': ["Casual", "Professional"]},
        'Français': {'Scenarios':["French1", "French 2"], 'Tones': ["FCasual", "FProfessional"]}
                 }
  

  #userInputs

  desired_language = st.sidebar.radio("Desired Language", ["English", "Français"], index = 0)
  desired_scenario = st.sidebar.selectbox("IT Scenario to Generate", options = quizOptionsList[desired_language]['Scenarios'])
  desired_tone = st.sidebar.selectbox("Desired Quiz Tone", options = quizOptionsList[desired_language]['Tones'])
  use_last_scenario = st.sidebar.radio("Use Last Scenario?", ["Yes", "No"])

  # Main Area
  script = st.text_area("Enter your script that the quiz should be based upon here.") # Will likely be changed to a file upload later, so invideo can be dropped, whisper processes, then standard questions are formed.
 
  # Two Button at Bottom after Quiz Generation - Regenerate Questions, Save Changes, Export,


def main():
  st.sidebar.title("Some Fancy Subtitle")
  st.sidebar.subheader("Select your generation options")

  pages = {
      "Scenario Generation": scenarioGeneration,
      "Quiz Generation": quizGen,
  }
  
  page = st.sidebar.selectbox("What would you like to generate?", list(pages.keys()))
  
  pages[page]()

# Run the app
if __name__ == "__main__":
    main()
