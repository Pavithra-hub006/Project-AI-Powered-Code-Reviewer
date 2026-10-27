 
#--------------------------------
# Step 1: Basic Streamlit App
#--------------------------------
 
# import streamlit as st
 
# def main():
#     st.title("My First Streamlit App")
#     st.write("Hi Students")
 
# if __name__ == "__main__":
#     main()
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
#--------------------------------
# Step 2: Adding Text Input
#--------------------------------
 
# import streamlit as st
 
# def main():
#     st.title("Streamlit – Step 2")
#     st.write("Hi Students")
 
#     name = st.text_input("Enter your name:")
 
#     st.write("You typed:", name)
 
# if __name__ == "__main__":
#     main()
 
 
 
 
 
 
 
 
 
 
#--------------------------------
# Step 3: Adding a Button
#--------------------------------
 
# import streamlit as st
 
# def main():
#     st.title("Streamlit – Step 3")
#     st.write("Hi Students")
 
#     name = st.text_input("Enter your name:")
 
#     if st.button("Greet"):
#         st.write("Hello", name)
 
# if __name__ == "__main__":
#     main()
 
 
 
 
 
 
 
 
 
 
 
#--------------------------------
# Step 4: Adding Number Inputs
#--------------------------------
 
# import streamlit as st
 
# def main():
#     st.title("Streamlit – Step 4")
#     st.write("Hi Students")
 
#     name = st.text_input("Enter your name:")
 
#     st.write("Enter two numbers to add:")
 
#     a = st.number_input("First number:", value=0)
#     b = st.number_input("Second number:", value=0)
 
#     if st.button("Calculate Sum"):
#         total = a + b
#         st.write("Hello", name)
#         st.write("Sum of the two numbers is:", total)
 
# if __name__ == "__main__":
#     main()
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
#--------------------------------
# Step 5: Adding Operation Selection
#--------------------------------
 
# import streamlit as st
 
# def main():
#     st.title("Streamlit – Step 5")
#     st.write("Hi Students")
 
#     name = st.text_input("Enter your name:")
 
#     a = st.number_input("First number:", value=0)
#     b = st.number_input("Second number:", value=0)
 
#     operation = st.selectbox(
#         "Choose operation:",
#         ["Add", "Subtract", "Multiply"]
#     )
 
#     if st.button("Calculate"):
#         if operation == "Add":
#             result = a + b
#         elif operation == "Subtract":
#             result = a - b
#         else:
#             result = a * b
 
#         st.write("Hello", name)
#         st.write("Operation:", operation)
#         st.write("Result:", result)
 
# if __name__ == "__main__":
#     main()
 
 
 
 
 
 
 
 
#--------------------------------
# Step 6: Adding Sidebar Navigation
#--------------------------------
 
# import streamlit as st
 
# st.sidebar.title("Menu")
# option = st.sidebar.selectbox("Choose:", ["Home", "Calculator", "About"])
 
# st.title("Main Page")
 
# if option == "Home":
#     st.write("Welcome to Home Page")
# elif option == "Calculator":
#     st.write("This is Calculator Page")
# else:
#     st.write("This is About Page")
 
 
 
#--------------------------------
# Step 7: Adding a Checkbox
#--------------------------------
 
# import streamlit as st
 
# st.title("Checkbox Example")
 
# show = st.checkbox("Show message")
 
# if show:
#     st.write("Hello Students!")
 
 
 
 
 
 
#--------------------------------
# Step 8: Adding a Slider
#--------------------------------
 
# import streamlit as st
 
# st.title("Slider Example")
 
# age = st.slider("Select your age:", 1, 100)
# st.write("Your age is:", age)
 
 
 
 
 
 
 
 
 
 
#--------------------------------
# Step 9: Adding File Upload
#--------------------------------
 
# import streamlit as st
 
# st.title("File Upload Example")
 
# file = st.file_uploader("Upload a text file", type=["txt"])
 
# if file is not None:
#     content = file.read().decode("utf-8")
#     st.write(content)
 
 
 
 
 
 
 
#--------------------------------
# Step 10: Using Columns for Layout
#--------------------------------
 
# import streamlit as st
 
# st.title("Column Layout")
 
# col1, col2 = st.columns(2)
 
# with col1:
#     st.write("This is left column")
 
# with col2:
#     st.write("This is right column")
 