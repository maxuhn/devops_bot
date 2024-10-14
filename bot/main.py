import logging
import paramiko
import os
import re
import psycopg2

from dotenv import load_dotenv
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, ContextTypes
from psycopg2 import Error

# === Конфигурация и Загрузка переменных окружения ===
load_dotenv()

# === Логирование ===
logging.basicConfig(
    filename='logfile.txt',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


TOKEN = os.getenv('TOKEN')

host = os.getenv('HOST')
username = os.getenv('USER')
user_password = os.getenv('PASSWORD')
postgres_port = os.getenv('POSTGRES_PORT')
postgres_host = os.getenv('POSTGRES_HOST')
postgres_username = os.getenv('POSTGRES_USER')
postgres_password = os.getenv('POSTGRES_PASSWORD')
repl_host = os.getenv('REPL_HOST')
repl_password = os.getenv('REPL_PASSWORD')
port = os.getenv('PORT')
postgres_db = os.getenv('POSTGRES_DB')


def start(update: Update, context):
    user = update.effective_user
    logger.info(f'Пользователь {user.full_name} начал сессию.')
    update.message.reply_text(f'Привет {user.full_name}!')

def help_command(update: Update, context):
    logger.info('Вызвана команда /help.')
    update.message.reply_text('Помощь!')


def ssh_execute(command):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, username=username, password=user_password)
        stdin, stdout, stderr = client.exec_command(command)
        data = stdout.read() + stderr.read()
        client.close()
        data = str(data.decode('utf-8')).replace('\\n', '\n').replace('\\t', '\t')[:-1]
        return data
    except paramiko.SSHException as e:
        logger.error(f"Ошибка SSH: {e}")
        return "Ошибка подключения к SSH: " + str(e)
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        return "Произошла ошибка: " + str(e)

def get_system_info_command(update: Update, context):
    logger.info('Вызвана команда /get_system_info.')
    update.message.reply_text("Выберите информацию о системе:\n"
                              "/get_release - Информация о релизе\n"
                              "/get_uname - Информация о системе\n"
                              "/get_uptime - Время работы\n"
                              "/get_df - Состояние файловой системы\n"
                              "/get_free - Состояние оперативной памяти\n"
                              "/get_mpstat - Производительность системы\n"
                              "/get_w - Работающие пользователи\n"
                              "/get_auths - Последние 10 входов\n"
                              "/get_critical - Последние 5 критических событий\n"
                              "/get_ps - Запущенные процессы\n"
                              "/get_ss - Используемые порты\n"
                              "/get_apt_list - Установленные пакеты\n"
                              "/get_services - Запущенные сервисы\n")


def get_release(update: Update, context):
    logger.info('Вызвана команда /get_release.')
    data = ssh_execute('cat /etc/os-release')
    update.message.reply_text(data)
    
def get_table_data(sql = "SELECT * FROM emails"):
    result = ""
    try:
        connection = psycopg2.connect(user=postgres_username,
                                      password=postgres_password,
                                      host=postgres_host,
                                      port=postgres_port,
                                      database=postgres_db)

        cursor = connection.cursor()
        cursor.execute(sql)
        connection.commit()
        logging.info("Команда успешно выполнена")
        data = cursor.fetchall()
        data = [str(element) for element in data]
        for row in data:
            result += row + "\n"
        logging.info("Команда успешно выполнена")

    except (Exception, Error) as error:
        return ("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()

    return result    
    
def get_emails(update: Update, context):
    result = get_table_data("SELECT * FROM emails")
    update.message.reply_text(result)

def get_phones(update: Update, context):
    result = get_table_data("SELECT * FROM phones")
    update.message.reply_text(result)

def get_repl_logs(update: Update, context):
    data = ssh_execute('docker logs db | grep replication')
    update.message.reply_text(data[-4000:])



def get_uname(update: Update, context):
    logger.info('Вызвана команда /get_uname.')
    data = ssh_execute('hostnamectl')
    update.message.reply_text(data)

def get_uptime(update: Update, context):
    logger.info('Вызвана команда /get_uptime.')
    data = ssh_execute('uptime')
    update.message.reply_text(data)

def get_df(update: Update, context):
    logger.info('Вызвана команда /get_df.')
    data = ssh_execute('df')
    update.message.reply_text(data)

def get_free(update: Update, context):
    logger.info('Вызвана команда /get_free.')
    data = ssh_execute('free')
    update.message.reply_text(data)

def get_mpstat(update: Update, context):
    logger.info('Вызвана команда /get_mpstat.')
    data = ssh_execute('mpstat')
    update.message.reply_text(data)

def get_w(update: Update, context):
    logger.info('Вызвана команда /get_w.')
    data = ssh_execute('w')
    update.message.reply_text(data)

def get_auths(update: Update, context):
    logger.info('Вызвана команда /get_auths.')
    data = ssh_execute('last')
    data = data.split("\n")
    formedData = []

    for i in range(10):
        formedData.append(data[i])

    update.message.reply_text("\n".join(formedData))

def get_critical(update: Update, context):
    logger.info('Вызвана команда /get_critical.')
    data = ssh_execute('journalctl -r -p crit -n 5 | head -n 5')
    update.message.reply_text(data)

def get_ps(update: Update, context):
    logger.info('Вызвана команда /get_ps.')
    data = ssh_execute('ps | head -n 20')
    update.message.reply_text(data)

def get_ss(update: Update, context):
    logger.info('Вызвана команда /get_ss.')
    data = ssh_execute('ss | head -n 20')
    update.message.reply_text(data)

def getServices(update: Update, context):
    data = ssh_execute('systemctl | head -n 20')
    update.message.reply_text(data)



def find_phone_numbers_command(update: Update, context):
    logger.info('Вызвана команда /find_phone_numbers.')
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')
    return 'find_phone_number'

def find_email_command(update: Update, context):
    update.message.reply_text('Введите текст для поиска электронных почт: ')

    return 'find_email'

def verify_password_command(update: Update, context):
    update.message.reply_text('Введите пароль для проверки на сложность: ')
    return 'verify_password'

def get_apt_list_command(update: Update, context):
    update.message.reply_text('Введите номер команды, которую хотите вызвать:\n 1. Вывод всех пакетов\n 2. Поиск информации о пакете')

    return 'get_apt_list'

def find_email (update: Update, context):
    user_input = update.message.text

    emailRegex = re.compile(r'([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)')

    emailList = emailRegex.findall(user_input)
    context.user_data["1"] = emailList

    if not emailList:
        update.message.reply_text('Эл. почта не найдена')
        return

    emails = ''
    for i in range(len(emailList)):
        emails += f'{i+1}. {emailList[i]}\n'

    update.message.reply_text(emails)
    update.message.reply_text("Хотите сохранить данные в базу данных?/ Введите 'Да/да'")
    return 'save_email'

def save_email(update: Update, context):
    user_input = update.message.text
    user_data = context.user_data.get("1")
    if user_input == "да" or user_input == "Да" or user_input == "+":
        for i in range(len(user_data)):
            response = get_table_data("INSERT INTO emails (email) VALUES ('" + f'{user_data[i]}' "');")
            if response:
                update.message.reply_text(f'Почта {user_data[i]} сохранена успешно')
    return ConversationHandler.END

def find_phone_numbers (update: Update, context):
    user_input = update.message.text

    phoneNumRegex = re.compile(r'(?:\+7|8)(?: \(\d{3}\) \d{3}-\d{2}-\d{2}|\d{10}|\(\d{3}\)\d{7}| \d{3} \d{3} \d{2} \d{2}| \(\d{3}\) \d{3} \d{2} \d{2}|-\d{3}-\d{3}-\d{2}-\d{2})')

    phoneNumberList = phoneNumRegex.findall(user_input)
    context.user_data["2"] = phoneNumberList

    if not phoneNumberList:
        update.message.reply_text('Телефонные номера не найдены')
        return

    phoneNumbers = ''
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n'

    update.message.reply_text(phoneNumbers)
    update.message.reply_text("Хотите сохранить данные в базу данных?/ Введите 'Да/да'")
    return 'save_phone'

def savePhone(update: Update, context):
    user_input = update.message.text
    user_data = context.user_data.get("2")
    if user_input == "да" or user_input == "Да" or user_input == "+":
        for i in range(len(user_data)):
            response = get_table_data("INSERT INTO phones (phone) VALUES ('" + f'{user_data[i]}' "');")
            if response:
                update.message.reply_text(f'Телефон {user_data[i]} сохранен успешно')
    return ConversationHandler.END

def verify_password(update: Update, context):
    user_input = update.message.text

    passwordRegex = re.compile(r'((?=.*[0-9])(?=.*[!@#$%^&*])(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z!@#$%^&*]{8,})')

    passwordComplexity = passwordRegex.match(user_input)

    if passwordComplexity:
        update.message.reply_text('Пароль сложный')
    else:
        update.message.reply_text('Пароль простой')
    return ConversationHandler.END

def get_apt_list(update: Update, context):
    user_input = update.message.text

    if user_input == "1":
        data = ssh_execute('dpkg-query -l | head -n 20')
        update.message.reply_text(data)
        return ConversationHandler.END

    elif user_input == "2":
        update.message.reply_text("Введите название пакета")
        return 'get_apt_list_package'

    else:
        update.message.reply_text("Неверная команда")
        return ConversationHandler.END

def get_apt_listPackage(update: Update, context):
    user_input = update.message.text
    try:
        data = ssh_execute("dpkg -L " + user_input + " | head -n 20")
        update.message.reply_text(data)
    except:
        update.message.reply_text("Неверное название пакета")
    return ConversationHandler.END

def echo(update: Update, context):
    update.message.reply_text(update.message.text)








def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    convHandlerget_apt_list = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', get_apt_list_command)],
        states={
            'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, get_apt_list)],
            'get_apt_list_package': [MessageHandler(Filters.text & ~Filters.command, get_apt_listPackage)],
        },
        fallbacks=[]
    )

    convHandlerfind_emails = ConversationHandler(
        entry_points=[CommandHandler('find_email', find_email_command)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, find_email)],
            'save_email': [MessageHandler(Filters.text & ~Filters.command, save_email)],
        },
        fallbacks=[]
    )

    # Обработчик диалога
    convHandlerfind_phone_numbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', find_phone_numbers_command)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, find_phone_numbers)],
            'save_phone': [MessageHandler(Filters.text & ~Filters.command, savePhone)],
        },
        fallbacks=[]
    )

    convHandlerCheckPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verify_password_command)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verify_password)],
        },
        fallbacks=[]
    )
    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_services", getServices))
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phones))
    dp.add_handler(convHandlerfind_phone_numbers)
    dp.add_handler(convHandlerfind_emails)
    dp.add_handler(convHandlerCheckPassword)
    dp.add_handler(convHandlerget_apt_list)

    # Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
