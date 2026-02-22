import json
import pickle
import random
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# 1. Load Data
# We load the intents from the JSON file
# 1. Load Data
# We load the intents from the JSON file
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'intents.json')
    with open(file_path, 'r') as file:
        data = json.load(file)
    print("Data loaded successfully.")
except FileNotFoundError:
    print(f"Error: intents.json not found at {file_path}. Please ensure the file exists in the directory.")
    exit()

# 2. Preprocess Data
# Extract patterns (X) and tags (y)
patterns = []
tags = []

for intent in data['intents']:
    for pattern in intent['patterns']:
        patterns.append(pattern)
        tags.append(intent['tag'])

print(f"Total patterns: {len(patterns)}")
print(f"Total tags: {len(tags)}")

# 3. Vectorization
# Using TF-IDF (Term Frequency-Inverse Document Frequency) to convert text to numbers
# It automatically handles tokenization and stop words if configured, but default is usually fine for this scale
vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1) # Enhanced vectorizer settings
X = vectorizer.fit_transform(patterns)

# 4. Train-Test Split (80-20)
# Stratified split to ensure all classes are represented in train/test if possible
try:
    X_train, X_test, y_train, y_test = train_test_split(X, tags, test_size=0.2, random_state=42, stratify=tags)
except ValueError:
    # Fallback if some classes have too few samples
    X_train, X_test, y_train, y_test = train_test_split(X, tags, test_size=0.2, random_state=42)
    
print("Data split into training and testing sets.")

# 5. Model Training
# LinearSVC is a fast and effective Support Vector Machine for text classification
model = LinearSVC()
model.fit(X_train, y_train)
print("Model training complete.")

# 6. Evaluation
# Predict on the test set
y_pred = model.predict(X_test)

# Calculate accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy * 100:.2f}%")

# Detailed classification report
print("\nClassification Report:\n")
# Handle division by zero warning in report if needed
print(classification_report(y_test, y_pred, zero_division=0))

# 7. Save Model and Vectorizer
# We need both to make predictions later (vectorizer transforms input, model predicts)
with open(os.path.join(script_dir, 'chatbot_model.pkl'), 'wb') as model_file:
    pickle.dump(model, model_file)

with open(os.path.join(script_dir, 'vectorizer.pkl'), 'wb') as vec_file:
    pickle.dump(vectorizer, vec_file)

print(f"Model saved to {os.path.join(script_dir, 'chatbot_model.pkl')}")
print(f"Vectorizer saved to {os.path.join(script_dir, 'vectorizer.pkl')}")
print("Training script execution finished.")
