# Import required libraries
import os
import json
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackContext, ApplicationBuilder
from asyncio import Queue
import google.generativeai as genai
import re
import textwrap
import pandas as pd
from newspaper import Article
from datetime import datetime
from threading import Thread
from http.server import SimpleHTTPRequestHandler, HTTPServer
import asyncio

# Gemini API settings, you will need to get this from https://ai.google.dev or from Google Cloud
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]  # Stored in environment variables for security

# Your bot token, you will need to generate this from your telegram
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_KIDS_TUTOR_BOT_TOKEN"] # Stored in environment variables for security

# Configure the API key
genai.configure(api_key=GEMINI_API_KEY)

# Create the model
# See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
generation_config = {
  "temperature": 1, # Is used to control the randomness of the output. Lower values make the model more deterministic.
  "top_p": 0.95, # Is used to control the diversity of the output. Lower values make the model more deterministic.
  "top_k": 64, # Is used to control the diversity of the output. Lower values make the model more deterministic.
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain", # The response format of the model (text/plain or application/json)  
}

# Safety settings for the model to prevent generation of harmful content
# See https://ai.google.dev/api/python/google/generativeai/types/HarmBlockThreshold
safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
  },
]

# Create the model instance with the specified settings
model = genai.GenerativeModel(
  model_name="gemini-1.5-pro",
  safety_settings=safety_settings,
  generation_config=generation_config,
  system_instruction=f'''
                Instruction:
                - You are a kids tutor chatbot named "David" and you help your students with their homework or question.
                - If the name is not in the history, ask for the name and remember it.
                - The chatbot should be able to answer questions on various subjects such as math, science, history, etc.
                - The chatbot should provide accurate and relevant information to the students.
                - The chatbot should not entertain questions that are inappropriate or harmful for a child that is less than 10 years old.
                - The chatbot should not give the answer directly but provide an explanation or guidance to help the student understand the concept.
                - Use '•' if you need to list the options in the response.
                - Don't use *.
                ''',
)

# Function to save chat history to a file
def save_chat_history(user, history):
    try:
        filename = f'chat_history_{user.id}_{user.first_name}.json'
        with open(filename, 'w') as file:
            json.dump(history, file)
    except Exception as e:
        print(f'''Error saving chat history: {e}''')

# Function to load chat history from a file
def load_chat_history(user):
    try:
        filename = f'chat_history_{user.id}_{user.first_name}.json'
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                history = json.load(file)
            return history
        else:
            return []
    except Exception as e:
        print(f'''Error loading chat history: {e}''')
        return []  
    
# Function to archive chat history with timestamp
def archive_chat_history(user):
    try:
        filename = f'chat_history_{user.id}_{user.first_name}.json'
        if os.path.exists(filename):
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            new_filename = f'chat_history_{user.id}_{user.first_name}_{timestamp}.json'
            os.rename(filename, new_filename)
            print(f'Chat history archived to {new_filename}')
        else:
            print(f'No chat history found for user {user.first_name}')
    except Exception as e:
        print(f'Error archiving chat history: {e}')

# Function to query Gemini API for chat response
def query_gemini_api(text, user):
    response = None
    try:
        chat_history = load_chat_history(user)

        # Add user message to chat history
        chat_history.append({'role': 'user', 'parts': text})

        # Create chat session with history
        chat_session = model.start_chat(
            history=chat_history
        )

        prompt = textwrap.dedent(text)
        response = chat_session.send_message(prompt)

        # Handle the blocked prompt case specifically
        # See https://ai.google.dev/api/python/google/generativeai/types/BlockedReason
        if response.prompt_feedback.block_reason == 2:
            return "Content was blocked, but the reason is uncategorized."
        
        # Check if there are any candidates in the response
        if response.text is not None:
            response_data = response.text
        else:
            return "No response received from the Gemini API."
        
        # Add AI response to chat history
        chat_history.append({'role': 'model', 'parts': response_data})

        # Save updated chat history to file
        save_chat_history(user, chat_history)
              
        return response_data
    except Exception as e:
        print(f'''Error: {e}\nResponse: {response}''')
        return f'''Error: {e}\nResponse: {response}'''
    
def replace_asterisks(text):
    # This regex will replace single asterisks not part of a pair of double asterisks
    text = re.sub(r'(?<!\*)\*(?!\*)(.*?)', r'• \1', text)    
    text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)    # Bold
    return text

# Escape special characters for Markdown
def escape_markdown(text):
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    text = replace_asterisks(text)
    text = re.sub(f'([{escape_chars}])', r'\\\1', text)
    text = re.sub(r"<a.*?href=['\"](.*?)['\"].*?>(.*?)</a>", r"\2 (\1)", text)
    return text
    
# Create an update queue
update_queue = Queue()

async def start(update: Update, _: CallbackContext) -> None:
    # When the user sends a /start command, the history is deleted and the bot asks for the user's name
    user = update.message.from_user

     # Call the archive chat history function
    archive_chat_history(user)

    await update.message.reply_text('''Hi I'm David, I will be your tutor? What is your name? ''')

async def echo(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    user = update.message.from_user
    
    try:

        if (text == ""):
             prediction = "I do not understand that. Can you ask your question again?"

        # Query the Gemini API for chat response
        prediction = query_gemini_api(text, user)

        # Retry if the resource has been exhausted
        if '429 Resource has been exhausted' in prediction:
            print(f'Resource has been exhausted. Retrying in 1 minute')
            prediction = f'I am not able to provide an answer now. Please try again later.'

    except Exception:
        prediction = f'I do not understand that. Can you ask your question again?'

    try:
        await update.message.reply_text(f"{replace_asterisks(prediction)}", parse_mode='Markdown') 
    except Exception:
        escaped_prediction = escape_markdown(prediction)
        print(f'Escaped Prediction: {escaped_prediction}')
        await update.message.reply_text(f"{escaped_prediction}", parse_mode='Markdown')

def run_http_server():
    server = HTTPServer(('0.0.0.0', int(os.environ.get('PORT', 8080))), SimpleHTTPRequestHandler)
    server.serve_forever()

def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    application.run_polling()

if __name__ == '__main__':
    # Start HTTP server in a separate thread
    http_server_thread = Thread(target=run_http_server)
    http_server_thread.start()

    # Run Telegram bot in the main thread
    main()
