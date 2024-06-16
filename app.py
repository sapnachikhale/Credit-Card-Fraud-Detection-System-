import streamlit as st
import pandas as pd
import joblib
import json

# Function to load the trained model
def load_model(model_path):
    try:
        return joblib.load(model_path)
    except FileNotFoundError:
        st.error("Model file not found. Please ensure 'fraud_detection_model.pkl' is in the correct location.")
        return None

# Function to perform feature extraction
def extract_features(data):
    # Convert categorical variables into numerical representations using one-hot encoding
    data = pd.get_dummies(data, columns=['merchant', 'category', 'gender', 'job'])
    # Assuming 'dob' and 'trans_num' columns are not needed for training, remove them
    data = data.drop(columns=['dob', 'trans_num'])
    return data

# Function to get prediction for user input
def predict_fraud(model, input_data):
    prediction = model.predict(input_data)
    return "Not fraud" if prediction[0] == 0 else "Fraud"

# Function to authenticate user
def authenticate_user(email, password, user_data):
    if email in user_data:
        if user_data[email]['password'] == password:
            return True
    return False

# Function to register new user
def register_user(email, password, user_data):
    if email not in user_data:
        user_data[email] = {'password': password}
        with open('user_data.json', 'w') as f:
            json.dump(user_data, f)
        return True
    return False

# Function to load user data from JSON file
def load_user_data():
    try:
        with open('user_data.json', 'r') as f:
            user_data = json.load(f)
    except FileNotFoundError:
        user_data = {}
    return user_data

# Function to store prediction history with only relevant details
def store_history(email, cc_num, gender, trans_num, prediction):
    history = load_history()
    if email not in history:
        history[email] = []
    history[email].append({'cc_num': cc_num, 'gender': gender, 'trans_num': trans_num, 'prediction': prediction})
    with open('history.json', 'w') as f:
        json.dump(history, f)

# Function to load history data from JSON file
def load_history():
    try:
        with open('history.json', 'r') as f:
            history = json.load(f)
    except FileNotFoundError:
        history = {}
    return history

# Load the trained model
model_path = "fraud_detection_model.pkl"
model = load_model(model_path)

# Check if model is loaded
if model:
    # Get feature names from the model
    feature_names = model.feature_names_in_

    # Load user data
    user_data = load_user_data()

    # Title of the web app
    st.title("Fraud Detection Web App")

    # Page state
    page = st.sidebar.radio("Navigation", ["Login", "Register"])

    if page == "Login":
        st.subheader("Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if authenticate_user(email, password, user_data):
                st.success("Logged in successfully!")
                st.session_state.email = email
                st.session_state.logged_in = True
            else:
                st.error("Invalid email or password. Please try again.")

    elif page == "Register":
        st.subheader("Register")
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.button("Register"):
            if new_password == confirm_password:
                if register_user(new_email, new_password, user_data):
                    st.success("Registration successful! Please login.")
                else:
                    st.error("Email already registered. Please use a different email.")
            else:
                st.error("Passwords do not match. Please try again.")

    # Input fields for prediction (only shown if logged in)
    if st.session_state.get('logged_in'):
        st.subheader("Enter Transaction Details")
        cc_num = st.text_input("Credit Card Number")
        merchant = st.text_input("Merchant")
        category = st.text_input("Category")
        gender = st.selectbox("Gender", options=["M", "F"])
        zip_code = st.text_input("Zip Code")
        lat = st.text_input("Latitude")
        long = st.text_input("Longitude")
        city_pop = st.text_input("City Population")
        job = st.text_input("Job")
        dob = st.text_input("Date of Birth (YYYY-MM-DD)")
        trans_num = st.text_input("Transaction Number")

        # Create a DataFrame with the input data
        input_data = pd.DataFrame({
            'cc_num': [cc_num],
            'merchant': [merchant],
            'category': [category],
            'gender': [gender],
            'zip': [zip_code],
            'lat': [lat],
            'long': [long],
            'city_pop': [city_pop],
            'job': [job],
            'dob': [dob],
            'trans_num': [trans_num]
        })

        # Extract features and ensure column order
        input_data = extract_features(input_data)

        # Ensure input data columns match model's feature names and order
        for feature in feature_names:
            if feature not in input_data.columns:
                input_data[feature] = 0

        input_data = input_data[feature_names]

        # Make prediction
        if st.button("Predict"):
            output = predict_fraud(model, input_data)
            st.write(f"Prediction: {output}")

            # Store prediction history
            if st.session_state.get('logged_in'):
                store_history(st.session_state.email, cc_num, gender, trans_num, output)

    # Page to display history
    if st.sidebar.checkbox("History") and st.session_state.get('logged_in'):
        st.title("Prediction History")
        email = st.session_state.email
        history = load_history()
        if email in history:
            for idx, entry in enumerate(history[email]):
                st.subheader(f"Entry {idx+1}")
                st.write("Card Number:", entry['cc_num'])
                st.write("Gender:", entry['gender'])
                st.write("Transaction Number:", entry['trans_num'])
                st.write("Prediction:", entry['prediction'])
        else:
            st.write("No history found for this email.")
