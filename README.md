# vatsim-emergency-bot
Send alert to Telegram if aircraft reported emergency on the vatsim network (squawk 7600, 7700)

## Usage
Firstly you should install dependencies with:

```shell
poetry install
```

Then you should set environment variables TELEGRAM_TOKEN and TELEGRAM_CHAT_ID

---
If you still don't have `poetry`, you can easily install it via `pipx`

```shell
pip install pipx
pipx install poetry
```

And finally you can start bot with 

```shell
python3 main.py
```