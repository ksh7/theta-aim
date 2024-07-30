import os
import google.generativeai as genai
import streamlit as st
from streamlit_chat import message
from pypdf import PdfReader

# Setting page title and header
st.set_page_config(page_title="Finance GPT", page_icon=":heavy_dollar_sign:")
st.markdown("<h3 style='text-align: center;'>Finance GPT - Powered by Theta EdgeCloud AI</h3>", unsafe_allow_html=True)

# Set org ID and API key
genai.configure(api_key=st.secrets["api_key"])
ai_model = genai.GenerativeModel(st.secrets["model_name"]) # this is sample model, to be replaced by Theta EdgeCloud based inferences

# Initialise session state variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {"role": "system", "content": "You are a helpful financial assistant, who have good knowledge of business, finance, stock market, etc."}
    ]
if 'model_name' not in st.session_state:
    st.session_state['model_name'] = []
if 'cost' not in st.session_state:
    st.session_state['cost'] = []
if 'total_tokens' not in st.session_state:
    st.session_state['total_tokens'] = []
if 'total_cost' not in st.session_state:
    st.session_state['total_cost'] = 0.0
if 'pdf_text' not in st.session_state:
    st.session_state['pdf_text'] = ""

# Sidebar - let user choose model, show total cost of current conversation, and let user clear the current conversation
st.sidebar.title("Available AI Models")
model_name = st.sidebar.radio("Choose a model:", ("Theta FinTech - Stock Market 2.0", "Theta FinTech - Market Trends 1.0"))
counter_placeholder = st.sidebar.empty()
counter_placeholder.write(f"Total cost of this conversation: ${st.session_state['total_cost']:.5f}")
clear_button = st.sidebar.button("Clear Conversation", key="clear")

# Map model names to OpenAI model IDs
if model_name == "Theta FinTech - Stock Market 2.0":
    model = "Theta FinTech - Stock Market 2.0"
else:
    model = "Theta FinTech - Market Trends 1.0"

# Reset everything
if clear_button:
    st.session_state['generated'] = []
    st.session_state['past'] = []
    st.session_state['messages'] = [
        {"role": "system", "content": "You are a helpful financial assistant, who have good knowledge of business, finance, stock market, etc."}
    ]
    st.session_state['number_tokens'] = []
    st.session_state['model_name'] = []
    st.session_state['cost'] = []
    st.session_state['total_cost'] = 0.0
    st.session_state['total_tokens'] = []
    st.session_state['pdf_text'] = ""
    counter_placeholder.write(f"Total cost of this conversation: ${st.session_state['total_cost']:.5f}")

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# File upload
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

if uploaded_file is not None:
    # Extract and store PDF content
    pdf_text = extract_text_from_pdf(uploaded_file)
    st.session_state["pdf_text"] = pdf_text
    st.write("PDF content has been successfully extracted and stored.")
    st.success("You can now start asking questions based on the PDF content.")
else:
    st.write("Please upload a PDF file to get started with your finance queries.")

# Generate a response
def generate_response(prompt, context=None):
    st.session_state['messages'].append({"role": "user", "content": prompt})
    if context:
        prompt = f"{context}\n\n based on above content answer following question \n\n {prompt}"
    response = ai_model.generate_content(prompt)
    st.session_state['messages'].append({"role": "assistant", "content": response})

    total_tokens = len(prompt.split())
    prompt_tokens = len(prompt.split())
    completion_tokens = len(prompt.split())
    return response, total_tokens, prompt_tokens, completion_tokens

# Container for chat history
response_container = st.container()
# Container for text box
container = st.container()

if st.session_state["pdf_text"]:
    with container:
        with st.form(key='my_form', clear_on_submit=True):
            user_input = st.text_area("Ask your finance query:", key='input', height=100)
            submit_button = st.form_submit_button(label='Send')

        if submit_button and user_input:
            context = st.session_state["pdf_text"] if st.session_state["pdf_text"] else None
            output, total_tokens, prompt_tokens, completion_tokens = generate_response(user_input, context)
            st.session_state['past'].append(user_input)
            st.session_state['generated'].append(output)
            st.session_state['model_name'].append(model_name)
            st.session_state['total_tokens'].append(total_tokens)

            if model_name == "Theta MediTech - Cancer 1.0":
                cost = total_tokens * 0.002 / 1000
            else:
                cost = (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000

            st.session_state['cost'].append(cost)
            st.session_state['total_cost'] += cost

if st.session_state['generated']:
    with response_container:
        for i in range(len(list(reversed(st.session_state['generated'])))):
            message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')
            message(st.session_state['generated'][i]._result.candidates[0].content.parts[0].text, key=str(i))
