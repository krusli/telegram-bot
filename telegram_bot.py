import json, requests
from collections import defaultdict

bot_data_filename = 'bot_data.json'

def download_to_tempfile(url, filename='tempfile.jpg'):
    r = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)

class Send:
    def __init__(self, token):
        self.url = 'https://api.telegram.org/bot%s/' % token
    def message(self, chat_id, message_text, reply_markup=None):
        if reply_markup:
            requests.get(self.url+'sendMessage', params=dict(chat_id=chat_id, text=message_text, reply_markup=reply_markup))
        else:
            requests.get(self.url+'sendMessage', params=dict(chat_id=chat_id, text=message_text))
    def message_reply(self, chat_id, message_text, message_id, reply_markup=None):
        if reply_markup:
            requests.get(self.url+'sendMessage', params=dict(chat_id=chat_id, text=message_text, reply_to_message_id=message_id, reply_markup=reply_markup))
        else:
            requests.get(self.url+'sendMessage', params=dict(chat_id=chat_id, text=message_text, reply_to_message_id=message_id))
    def markdown(self, chat_id, message_text, reply_markup=None):
        if reply_markup:
            requests.get(self.url+'sendMessage', params=dict(chat_id=chat_id, text=message_text, parse_mode='Markdown', \
                reply_markup=reply_markup))
        else:
            requests.get(self.url+'sendMessage', params=dict(chat_id=chat_id, text=message_text, parse_mode='Markdown'))
    def markdown_reply(self, chat_id, message_text, message_id):
        requests.get(self.url+'sendMessage', params=dict(chat_id=chat_id, text=message_text, reply_to_message_id=message_id, \
            parse_mode='Markdown'))
    def action(self, chat_id, bot_action):
        requests.get(self.url+'sendChatAction', params=dict(chat_id=chat_id, action=bot_action))
    def send_photo(self, chat_id, filename, disable_notification=False):
        self.action(chat_id, 'upload_photo')
        requests.post(self.url+'sendPhoto', data=dict(chat_id=chat_id, disable_notification=disable_notification), files=dict(photo=open(filename, 'rb')))
    def send_document(self, chat_id, filename):
        self.action(chat_id, 'upload_document')
        requests.post(self.url+'sendDocument', data=dict(chat_id=chat_id), files=dict(document=open(filename, 'rb')))
    def inline_response(self, query_id, answer):
        requests.get(self.url+'answerInlineQuery', params=dict(inline_query_id=query_id, results=answer))
    def answer_callback_query(self, callback_query_id, message_text=None, show_alert=False):
        params = dict(callback_query_id=callback_query_id)
        if message_text:
            params['message_text'] = message_text
        if show_alert:
            params['show_alert'] = True
        requests.get(self.url+'answerCallbackQuery', params=params)
    def edit_message(self, text, chat_id=None, message_id=None, inline_message_id=None, parse_mode=None, reply_markup=None):
        # print(text, chat_id, message_id, inline_message_id, parse_mode, reply_markup)
        if chat_id or message_id or inline_message_id:
            if chat_id and message_id:
                params = dict(chat_id=chat_id, message_id=message_id, inline_message_id=inline_message_id, \
                    text=text)
            else:
                params = dict(inline_message_id=inline_message_id, text=text)
            if parse_mode: params['parse_mode'] = parse_mode
            if reply_markup: params['reply_markup'] = reply_markup
            # print(params)
            requests.get(self.url+'editMessageText', params=params)
    def edit_message_markup(self, chat_id=None, message_id=None, inline_message_id=None, reply_markup=None):
        if chat_id or message_id or inline_message_id:
            if chat_id and message_id:
                params = dict(chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)
            else:
                params = dict(inline_message_id=inline_message_id, reply_markup=reply_markup)
            requests.get(self.url+'editMessageReplyMarkup', params=params)


class Processable:
    def get_arguments(self):
        return self.text.split()
    def get_argument_count(self):
        return len(self.text.split())

class Message(Processable):
    # takes an update from Telegram Bot API
    def __init__(self, update):
        self.message_id = update['message']['message_id']
        self.chat_id = update['message']['chat']['id']
        self.sender = update['message']['from']
        try:
            self.text = update['message']['text']
        except KeyError:
            self.text = ""
        self.argument_count = self.get_argument_count()
        self.parameters = self.get_parameters()
    def get_command(self):
        try:
            return self.get_arguments()[0]
        except IndexError:
            return None
    def get_parameters(self):
        try:
            return ' '.join(self.get_arguments()[1:])
        except IndexError:
            return None

class InlineQuery(Processable):
    def __init__(self, update):
        self.query_id = update['inline_query']['id']
        self.text = update['inline_query']['query']
        self.sender = update['inline_query']['from']
        self.argument_count = self.get_argument_count()

    def get_command(self):
        try:
            return self.text.split()[0]
        except IndexError:
            return ''

class InlineResponse:
    def __init__(self):
        self.item_count = 0
        self.article_list = []
        self.photo_list = []
    def add_article(self, title, description, message_text, parse_mode=None, reply_markup=None, id=None):
        entry = dict(type='article', id=str(self.item_count+1), title=title, description=description, \
            input_message_content={'message_text': message_text})
        if parse_mode:
            entry['input_message_content']['parse_mode'] = parse_mode
        if reply_markup:
            entry['reply_markup'] = reply_markup
        if id:
            entry['id'] = id
        self.item_count += 1
        self.article_list.append(entry)
    def add_photo(self, link, width, height):
        entry = dict(type='photo', id=str(self.item_count+1), photo_url=link, photo_width=width, \
            photo_height=height, thumb_url=link)
        self.item_count += 1
        self.photo_list.append(entry)
    def get_json_response(self):
        if self.photo_list:
            return json.dumps(self.photo_list)
        return json.dumps(self.article_list)

class Checked:
    def __init__(self):
        self.functions = []
    def define(self):
        def wrapper(func):
            self.functions.append(func)
            return func
        return wrapper
    def call_functions(self):
        for function in self.functions:
            function()
checked = Checked()

class Command:
    def __init__(self):
        self.commands = {}
    def define(self, command_str):
        def wrapper(func):
            self.commands[command_str] = func
            return func
        return wrapper
    def get(self, command):
        func = None
        if command:     # if command is not None
            for func_name in self.commands.keys():
                if command.startswith(func_name):
                    func = self.commands[func_name]
        if func:
            return func
        else:
            raise ValueError('Command "{}" has not been defined'.format(command))

command = Command()

class InlineCommand:
    def __init__(self):
        self.commands = defaultdict(list)
    def define(self, command_str):
        def wrapper(func):
            self.commands[command_str].append(func)
            return func
        return wrapper
    def get_functions(self, command):
        funcs = []
        if command:
            for func in self.commands.keys():
                if command.startswith(func):
                   funcs.extend(self.commands[func])
        return funcs

inline = InlineCommand()

class InlineCallback(Command):
    def __init__(self):
        super().__init__()
inline_callback = InlineCallback()

class ChosenInline(Command):
    def __init__(self):
        self.functions = []
    def register(self):
        def wrapper(func):
            self.functions.append(func)
            return func
        return wrapper
chosen_inline = ChosenInline()

class CallbackQuery:
    def __init__(self, update):
        # print(update)
        self.id = update['callback_query']['id']
        self.sender = update['callback_query']['from']
        self.data = update['callback_query']['data']
        self.inline_message_id = update.get('callback_query').get('inline_message_id')
        try:
            self.message = Message(update['callback_query'])
        except KeyError:
            self.message = None

class InlineKeyboard:
    def __init__(self):
        self.keyboard_button_list = [[]]
    def add_keyboard_button(self, text, callback_data=None, next_row=False, switch_inline_query=None):
        if next_row:
            keyboard_button_list.append([])     # insert new row

        keyboard_button = {}
        keyboard_button['text'] = text
        if callback_data:
            keyboard_button['callback_data'] = callback_data
        if switch_inline_query:
            keyboard_button['switch_inline_query'] = switch_inline_query

        # append to last row
        self.keyboard_button_list[len(self.keyboard_button_list)-1].append(keyboard_button)
    def get_json_response(self):
        response = dict(inline_keyboard = self.keyboard_button_list)
        return json.dumps(response)
    def get_response(self):
        return dict(inline_keyboard = self.keyboard_button_list)
    def is_empty(self):
        if self.keyboard_button_list == [[]]:
            return True
        return False

class ChosenInlineResult:
    def __init__(self, update):
        self.result_id = update['chosen_inline_result']['result_id']
        self.sender = update['chosen_inline_result']['from']
        self.location = update['chosen_inline_result'].get(location)
        self.inline_message_id = update['chosen_inline_result'].get(inline_message_id)
        self.query = update['chosen_inline_result']['query']

class Telegram_Bot:
    def __init__(self, token):
        self.url = 'https://api.telegram.org/bot%s/' % token
        self.sender = Send(token)
        self.InlineKeyboard = InlineKeyboard   # class

    def run(self):
        try:
            with open(bot_data_filename) as bot_data_file:
                self.bot_data = json.load(bot_data_file)
        except FileNotFoundError:
            self.bot_data = {}

        try:
            last_update = self.bot_data['last_update']
        except KeyError:
            last_update = 0

        while True:
            checked.call_functions()
            try:
                updates = json.loads(requests.get(self.url + 'getUpdates', dict(offset=last_update)).text)['result']
            except Exception as e:
                print(e)

            for update in updates:
                if last_update < update['update_id']:
                    last_update = update['update_id']
                    self.bot_data['last_update'] = last_update

                    if 'message' in update.keys():
                        message = Message(update)
                        # print(message.text)
                        try:
                            function = command.get(message.get_command())
                            function(message)   # Message object for processing
                        except ValueError:   # no command in message
                            pass

                    if 'inline_query' in update.keys():
                        inline_query = InlineQuery(update)
                        # print(inline_query.text)
                        inline_response = InlineResponse()  # prepare a new inline response
                        functions = inline.get_functions(inline_query.get_command())
                        if functions:   # if len(functions) > 0
                            for function in functions:
                                # InlineResponse object for function to add response
                                function(inline_query, inline_response)
                        self.sender.inline_response(inline_query.query_id, inline_response.get_json_response())

                    if 'callback_query' in update.keys():
                        callback_query = CallbackQuery(update)
                        try:
                            function = inline_callback.get(callback_query.data)
                            function(callback_query)
                        except ValueError:  # undefined command
                            pass

                    """
                    if 'chosen_inline_result' in update.keys():
                        chosen_inline_result = ChosenInlineResult(update)
                        try:
                            for function in chosen_inline.functions:
                                function(chosen_inline_result)
                        except ValueError:  # undefined command
                            pass
                    """


            with open(bot_data_filename, 'w') as bot_data_file:
                json.dump(self.bot_data, bot_data_file)
