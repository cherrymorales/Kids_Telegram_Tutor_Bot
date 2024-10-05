# Kid's Telegram Tutor Bot

Kid's Telegram Tutor Bot is a Telegram-based educational bot designed to help children with learning tasks. The bot uses Google's Gemini API for generating intelligent responses, providing tutoring services in an interactive and safe manner. This bot aims to provide an engaging learning environment for kids while ensuring security and user privacy.

## Prerequisites
To run the bot, you'll need:
- **Python 3.8+**
- A **Telegram bot token** from BotFather
- A **Google Gemini API key**

## Setup Instructions

### 1. Clone the Repository
Start by cloning the repository to your local machine:
```bash
git clone https://github.com/your-username/kids-telegram-tutor-bot.git
cd kids-telegram-tutor-bot
```
### 2. Install Required Libraries
Install all necessary libraries using the provided `requirements.txt` file:
```bash
pip install -r requirements.txt
```
The key libraries required for this project are:
- `python-telegram-bot`
- `google.generativeai`
- `newspaper3k`
- `pandas`

### 3. Set Environment Variables
Set up your environment variables to store sensitive information securely.

- **GEMINI_API_KEY**: Your API key for the Google Gemini AI
- **TELEGRAM_KIDS_TUTOR_BOT_TOKEN**: Your bot token from Telegram

On **Linux/Mac**:
```bash
export GEMINI_API_KEY="your-google-gemini-api-key"
export TELEGRAM_KIDS_TUTOR_BOT_TOKEN="your-telegram-bot-token"
```

On **Windows**:
```bash
set GEMINI_API_KEY="your-google-gemini-api-key"
set TELEGRAM_KIDS_TUTOR_BOT_TOKEN="your-telegram-bot-token"
```

### 4. Run the Bot
With everything set up, you can now run the bot with the following command:
```bash
python app.py
```
The bot will now be running and ready to interact with users on Telegram.

## Usage

1. **Start the Bot**: Open Telegram, search for your bot's username, and start a chat.
2. **Command Interaction**: Use the `/start` command to initialize the bot and begin interaction.
3. **Educational Responses**: The bot will respond to messages and tutoring requests using AI-generated content via the Google Gemini API.

## Example Bot Code

Here is a simple portion of the bot's code that generates a response using Google Gemini AI:

```python
import generativeai as genai

# Set your API key
API_KEY = os.environ["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# Configure the generation model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

# Safety settings to block harmful content
safety_settings = [
  {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
  {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# Sample function to generate text
def generate_response(prompt):
    response = genai.generate(prompt=prompt, **generation_config)
    return response['text']
```

## Security Considerations
- **Environment Variables**: API keys are stored in environment variables for security.
- **Safety Settings**: The bot uses Google's safety settings to block harmful content, ensuring that the generated text is safe for children.

## Future Enhancements
- Adding more subject areas for tutoring.
- Introducing image and video-based learning materials.
- Enhancing the user interface with multimedia support.

## Contribution
We welcome contributions! Please fork the repository and submit a pull request with your enhancements or suggestions.
