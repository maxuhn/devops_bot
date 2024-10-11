import logging
import paramiko
import os
import re
import psycopg2

from dotenv import load_dotenv
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, ContextTypes
from psycopg2 import Error

load_dotenv()

# Подключаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

host = os.getenv('HOST')
TOKEN = os.getenv('TOKEN')
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
db_version = os.getenv('POSTGRES_VERSION')

def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def helpCommand(update: Update, context):
    update.message.reply_text('Help!')


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'find_phone_number'

def findEmailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска электронных почт: ')

    return 'find_email'

def verifyPasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки на сложность: ')

    return 'verify_password'

def getAptListCommand(update: Update, context):
    update.message.reply_text('Введите номер команды, которую хотите вызвать:\n 1. Вывод всех пакетов\n 2. Поиск информации о пакете')

    return 'get_apt_list'

def findEmail (update: Update, context):
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

def saveEmail(update: Update, context):
    user_input = update.message.text
    user_data = context.user_data.get("1")
    if user_input == "да" or user_input == "Да" or user_input == "+":
        for i in range(len(user_data)):
            response = getTableData("INSERT INTO emails (email) VALUES ('" + f'{user_data[i]}' "');")
            if response:
                update.message.reply_text(f'Почта {user_data[i]} сохранена успешно')
    return ConversationHandler.END

def findPhoneNumbers (update: Update, context):
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
            response = getTableData("INSERT INTO phones (phone) VALUES ('" + f'{user_data[i]}' "');")
            if response:
                update.message.reply_text(f'Телефон {user_data[i]} сохранен успешно')
    return ConversationHandler.END

def verifyPassword(update: Update, context):
    user_input = update.message.text

    passwordRegex = re.compile(r'((?=.*[0-9])(?=.*[!@#$%^&*])(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z!@#$%^&*]{8,})')

    passwordComplexity = passwordRegex.match(user_input)

    if passwordComplexity:
        update.message.reply_text('Пароль сложный')
    else:
        update.message.reply_text('Пароль простой')
    return ConversationHandler.END

def getAptList(update: Update, context):
    user_input = update.message.text

    if user_input == "1":
        data = getConnectionCommand('dpkg-query -l | head -n 20')
        update.message.reply_text(data)
        return ConversationHandler.END

    elif user_input == "2":
        update.message.reply_text("Введите название пакета")
        return 'get_apt_list_package'

    else:
        update.message.reply_text("Неверная команда")
        return ConversationHandler.END

def getAptListPackage(update: Update, context):
    user_input = update.message.text
    try:
        data = getConnectionCommand("dpkg -L " + user_input + " | head -n 20")
        update.message.reply_text(data)
    except:
        update.message.reply_text("Неверное название пакета")
    return ConversationHandler.END

def echo(update: Update, context):
    update.message.reply_text(update.message.text)

def getConnectionCommand(command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=user_password)
    stdin, stdout, stderr = client.exec_command(command)
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data.decode('utf-8')).replace('\\n', '\n').replace('\\t', '\t')[:-1]
    return data

def getRelease(update: Update, context):
    data = getConnectionCommand('cat /etc/os-release')
    update.message.reply_text(data)

def getUname(update: Update, context):
    data = getConnectionCommand('hostnamectl')
    update.message.reply_text(data)

def getUptime(update: Update, context):
    data = getConnectionCommand('uptime')
    update.message.reply_text(data)

def getDf(update: Update, context):
    data = getConnectionCommand('df')
    update.message.reply_text(data)

def getFree(update: Update, context):
    data = getConnectionCommand('free')
    update.message.reply_text(data)

def getMpstat(update: Update, context):
    data = getConnectionCommand('mpstat')
    update.message.reply_text(data)

def getW(update: Update, context):
    data = getConnectionCommand('w')
    update.message.reply_text(data)

def getAuths(update: Update, context):
    data = getConnectionCommand('last')
    data = data.split("\n")
    formedData = []

    for i in range(10):
        formedData.append(data[i])

    update.message.reply_text("\n".join(formedData))

def getCritical(update: Update, context):
    data = getConnectionCommand('journalctl -r -p crit -n 5 | head -n 5')
    update.message.reply_text(data)

def getPs(update: Update, context):
    data = getConnectionCommand('ps | head -n 20')
    update.message.reply_text(data)

def getSs(update: Update, context):
    data = getConnectionCommand('ss | head -n 20')
    update.message.reply_text(data)

def getServices(update: Update, context):
    data = getConnectionCommand('systemctl | head -n 20')
    update.message.reply_text(data)

def getReplLogs(update: Update, context):
    data = getConnectionCommand(f'cat /var/log/postgresql/postgresql-{db_version}-main.log | tail -n 20')
    update.message.reply_text(data[-4000:])

def getTableData(sql = "SELECT * FROM emails"):
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

def getEmails(update: Update, context):
    result = getTableData("SELECT * FROM emails")
    update.message.reply_text(result)

def getPhones(update: Update, context):
    result = getTableData("SELECT * FROM phones")
    update.message.reply_text(result)

def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    convHandlerGetAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', getAptListCommand)],
        states={
            'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, getAptList)],
            'get_apt_list_package': [MessageHandler(Filters.text & ~Filters.command, getAptListPackage)],
        },
        fallbacks=[]
    )

    convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailCommand)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, findEmail)],
            'save_email': [MessageHandler(Filters.text & ~Filters.command, saveEmail)],
        },
        fallbacks=[]
    )

    # Обработчик диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'save_phone': [MessageHandler(Filters.text & ~Filters.command, savePhone)],
        },
        fallbacks=[]
    )

    convHandlerCheckPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)],
        },
        fallbacks=[]
    )
    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(CommandHandler("get_release", getRelease))
    dp.add_handler(CommandHandler("get_uname", getUname))
    dp.add_handler(CommandHandler("get_uptime", getUptime))
    dp.add_handler(CommandHandler("get_df", getDf))
    dp.add_handler(CommandHandler("get_free", getFree))
    dp.add_handler(CommandHandler("get_mpstat", getMpstat))
    dp.add_handler(CommandHandler("get_w", getW))
    dp.add_handler(CommandHandler("get_auths", getAuths))
    dp.add_handler(CommandHandler("get_critical", getCritical))
    dp.add_handler(CommandHandler("get_ps", getPs))
    dp.add_handler(CommandHandler("get_ss", getSs))
    dp.add_handler(CommandHandler("get_services", getServices))
    dp.add_handler(CommandHandler("get_repl_logs", getReplLogs))
    dp.add_handler(CommandHandler("get_emails", getEmails))
    dp.add_handler(CommandHandler("get_phone_numbers", getPhones))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerCheckPassword)
    dp.add_handler(convHandlerGetAptList)

    # Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
