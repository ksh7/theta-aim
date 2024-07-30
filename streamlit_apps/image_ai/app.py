import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

genai.configure(api_key=st.secrets["api_key"])
st.set_page_config(page_title="Image GPT", page_icon=":sparkles:", layout="wide")
ai_model = genai.GenerativeModel(st.secrets["model_name"])

def main():
    st.markdown(
        """
        <h2 style='text-align: center;'>Image AI: Powered by Theta CloudGPT AI</h2>
        """,
        unsafe_allow_html=True
    )

    # Create two columns
    left_column, right_column = st.columns(2)

    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    with left_column:
        # Image upload section
        uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

        if uploaded_file is not None:
            # Open the uploaded image
            img = PIL.Image.open(uploaded_file)
            
            # Display the image
            st.image(img, caption="Uploaded Image", use_column_width=True)

    if uploaded_file is not None:
        with right_column:
            # Question and response section
            question = st.text_input("Ask a question about the image")

            if st.button("Ask"):
                if question:
                    # Generate the response
                    response = ai_model.generate_content([question, img])
                    
                    # Update chat history
                    st.session_state.chat_history.insert(0, {"question": question, "answer": response.text})
                else:
                    st.write("Please ask your query")

            # Display chat history
            for chat in st.session_state.chat_history:
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <div style="flex: 1;">
                            <span style="font-size: 24px;">🧑 <strong>You:</strong></span> {chat['question']}
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 20px;">
                        <div style="flex: 1;">
                            <span style="font-size: 24px;">🤖 <strong>AI:</strong></span> {chat['answer']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True
                )
    else:
        with right_column:
            st.markdown(
                """
                <h4 style='text-align: center; margin-top: 20px;'>Upload an image to start asking questions</h4>
                """,
                unsafe_allow_html=True
            )

if __name__ == "__main__":
    main()
