from telegram_bot import Telegram_Bot, command, inline, inline_callback, chosen_inline, checked
import datetime, json

token = ''  # Bot API token here

bot = Telegram_Bot(token)
send = bot.sender

class Reminder:
    datetime_format = "%d %B %Y, %H:%M"
    def __init__(self, text, time_string, chat_id, sender):
        self.text = text
        self.sender = sender
        self.chat_id = chat_id

        self.time = datetime.datetime.strptime(time_string, self.datetime_format)
    def date_string(self):
        return self.time.strftime(self.datetime_format)
    def to_json(self):
        return json.dumps({self.date_string(): [self.text, self.chat_id, self.sender]})
    def is_passed(self):
        # True if current time is greater than time for the Reminder's time
        return datetime.datetime.now() > self.time

class TodayReminder(Reminder):
    time_format = '%H:%M'
    def __init__(self, text, time_string, chat_id, sender):
        now = datetime.datetime.now()
        self.text = text
        self.sender = sender
        self.chat_id = chat_id

        self.time = datetime.datetime.strptime(time_string, self.time_format)
        self.time = datetime.datetime(year=now.year, month=now.month, day=now.day, hour=self.time.hour, minute=self.time.minute)

class JSONReminder(Reminder):
    def from_json(self, json_string):
        json_dict = json.loads(json_string)
        data_key = list(json_dict.keys())[0]
        time_string = data_key

        self.text = json_dict[data_key][0]
        self.chat_id = json_dict[data_key][1]
        self.sender = json_dict[data_key][2]
        self.time = datetime.datetime.strptime(time_string, self.datetime_format)

    def __init__(self, json_string):
        self.from_json(json_string)

reminders = []
try:
    with open('reminders.json') as f:
        reminders_unparsed = json.load(f)
        for reminder_primitive in reminders_unparsed:
            reminders.append(JSONReminder(reminder_primitive))
except FileNotFoundError:
    pass

@command.define('/addreminder')
def add_reminder(message):
    if message.argument_count == 1:
        reply = 'Usage: /addreminder tea 10 November 2016, 18:00 or /addreminder tea 18:00'
    else:
        text = message.get_arguments()[1]
        time_string = ' '.join(message.get_arguments()[2:])

        try:
            reminder = TodayReminder(text, time_string, message.chat_id, message.sender['username'])
            reminders.append(reminder)
            reply = 'Reminder successfully added.'
        except ValueError:
            try:
                reminder = Reminder(text, time_string, message.chat_id, message.sender['username'])
                reminders.append(reminder)
                reply = 'Reminder successfully added.'
            except ValueError:
                reply = 'Usage: /addreminder tea 10 November 2016, 18:00 or /addreminder tea 18:00'
    send.markdown_reply(message.chat_id, reply, message.message_id)

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

if __name__ == '__main__':
    bot.run()
