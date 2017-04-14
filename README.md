# A Telegram Bot Framework for Python 3

## Prerequisties
- Python 3
- requests

## How to use
Create a new Python file and add these lines:
```
from telegram_bot import Telegram_Bot, command, inline, inline_callback, chosen_inline, checked

token = ''  # Bot API token here

bot = Telegram_Bot(token)
send = bot.sender

# define functions here

if __name__ == '__main__':
    bot.run()
```

Replace your API token with the one you got from BotFather for your bot - if you don't have one - refer to [Telegram Bot documentation](https://core.telegram.org/bots) to set up your bot first.

## Usage
### `send`
Methods of the `Send` class:
```
def message(self, chat_id, message_text, reply_markup=None):
def message_reply(self, chat_id, message_text, message_id, reply_markup=None):
def markdown(self, chat_id, message_text, reply_markup=None):
def markdown_reply(self, chat_id, message_text, message_id):
def action(self, chat_id, bot_action):
def send_photo(self, chat_id, filename, disable_notification=False):
def send_document(self, chat_id, filename):
def inline_response(self, query_id, answer):
def answer_callback_query(self, callback_query_id, message_text=None, show_alert=False):
def edit_message(self, text, chat_id=None, message_id=None, inline_message_id=None, parse_mode=None, reply_markup=None):
def edit_message_markup(self, chat_id=None, message_id=None, inline_message_id=None, reply_markup=None):
```

Refer to Telegram Bot documentation](https://core.telegram.org/bots) for more information.

### `command`
Telegram bots use slash-commands (`/somecommand`). To register a function to handle an incoming message with a specific `/command`:

```
# All messages starting with '/addreminder' will be sent to this function

@command.define('/addreminder')
def add_reminder(message):
  # more code here
```

### `inline`
Similarly, we can register functions to handle inline queries.
```

@inline.define('')
def inline_markdown(inline_query, inline_response):
    inline_response.add_article('Markdownise', 'Send formatted text', inline_query.text, 'Markdown')

@inline.define('')
def inline_currency(inline_query, inline_response):
    text = inline_query.text
    if inline_query.argument_count == 1 and len(text) == 6:
        inline_response.add_article('Currency', 'Convert ' + text[:3].upper() + ' to ' + text[3:].upper(), currency.get_rate(text))
    elif inline_query.argument_count == 2 and len(inline_query.get_arguments()[1]) == 6:
        amount = inline_query.get_arguments()[0]
        quote = inline_query.get_arguments()[1]
        try:
            float(amount)
            inline_response.add_article('Currency', \
                'Convert ' + amount + ' ' + quote[:3].upper() + ' to ' + quote[3:].upper(), \
                currency.get_rate(quote, amount))
        except ValueError:
            pass

```

### `checked`
Functions registered with `checked` will be called at the end of each iteration (getting new updates from the API, processing the updates). In the `Reminder.py` example, we use this to see if the bot has any pending reminders to be sent.

```
@checked.define()
def check_reminders():
    reminders_copy = list(reminders)
    for reminder in reminders_copy: # avoid array size change during iteration -> error
        if (reminder.is_passed()):
            reminders.remove(reminder)
            send.markdown(reminder.chat_id, "Reminder for @{}:\n{}".format(reminder.sender, reminder.text))

    # save updated reminders to file
    with open('reminders.json', 'w') as f:
        x = []
        for reminder in reminders:
            x.append(reminder.to_json())
        json.dump(x, f)
```

## Sample app: reminders
A sample Telegram reminders bot is included (`Reminder.py`).
