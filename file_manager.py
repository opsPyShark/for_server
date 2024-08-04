import os

class FileManager:
    def __init__(self, bot, chat_id):
        self.bot = bot
        self.chat_id = chat_id
        self.files = [
            "exclude-hosts-custom.txt",
            "exclude-hosts-dist.txt",
            "exclude-ips-custom.txt",
            "include-hosts-custom.txt",
            "include-ips-custom.txt"
        ]

    def edit_file(self, message):
        try:
            # Получение имени файла из сообщения
            filename = message.text.split(maxsplit=1)[1]

            # Проверка, что файл в списке разрешенных
            if filename not in self.files:
                self.bot.send_message(self.chat_id, f"File {filename} is not allowed or doesn't exist.")
                return

            # Попросить пользователя отправить текст для добавления или удаления
            self.bot.send_message(self.chat_id, f"Send the text to add or remove from {filename}.")
            self.bot.register_next_step_handler(message, self.modify_file, filename)

        except IndexError:
            self.bot.send_message(self.chat_id, "Please specify a file name.")

    def modify_file(self, message, filename):
        text = message.text

        try:
            # Путь к файлу
            filepath = os.path.join(os.getcwd(), filename)

            # Проверка существования файла
            if not os.path.isfile(filepath):
                self.bot.send_message(self.chat_id, f"File {filename} not found.")
                return

            with open(filepath, 'r+') as file:
                lines = file.readlines()
                if text.startswith("-"):
                    # Удалить строку из файла
                    lines = [line for line in lines if line.strip() != text[1:].strip()]
                else:
                    # Добавить строку в файл
                    if text.strip() + '\n' not in lines:
                        lines.append(text.strip() + '\n')

                # Запись обратно в файл
                file.seek(0)
                file.truncate()
                file.writelines(lines)

            self.bot.send_message(self.chat_id, f"File {filename} has been modified.")
        except Exception as e:
            self.bot.send_message(self.chat_id, f"Failed to modify file: {e}")
