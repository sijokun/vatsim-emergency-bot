# vatsim-emergency-bot
Send alert to Telegram if aircraft reported emergency on the vatsim network (squawk 7600, 7700)

## Usage
Firstly you should install dependencies with:

```python3 -m pip install -r requirements.txt```

Then you should set environment variables TELEGRAM_TOKEN and TELEGRAM_CHAT_ID

And finally you can start bot with 

```python3 main.py```