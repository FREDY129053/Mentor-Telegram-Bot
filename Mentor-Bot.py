import asyncio
import logging
import mysql
import aiogram.types

from aiogram import Bot, Dispatcher, types
from aiogram import Bot, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from mysql.connector import connect, Error

logging.basicConfig(level=logging.INFO)

# mysql vars
db_config = {
    "user": "me",
    "password": "password",
    "host": "193.124.118.138",
    "database": "project",
}
db = mysql.connector.connect(**db_config)
cursor = db.cursor()

# aiogram vars
bot = Bot(token="5703403331:AAFFuggpCLrtk5qeOpwRjW-Xfeub_0Ic1gA")
dp = Dispatcher(bot)
admin_tg = "1202748393"

# flags
is_process = False
last_id = 0


# команда "/start"
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Привет!\nИспользуй: /profile для проверки 👤")


# команда просмотра профиля
@dp.message_handler(commands=['profile'])
async def start(message: types.Message):
    username = message.from_user.username
    db_query = f"SELECT * FROM mentors WHERE mentor_telegram='@{username}'"
    try:
        with connect(
                host="193.124.118.138",
                user="me",
                password="password",
                database="project"
        ) as connection:

            with connection.cursor() as cursor:
                cursor.execute(db_query)
                for db in cursor.fetchall():
                    (num, meeting, telegram, surname, name, price, exp, saves, sphere, about) = db
                    if saves is None:
                        saves = 0
                    await message.answer(f"Ваш 👤:\n\n"
                                         f"• Фамилимя: {surname}\n• Имя: {name}\n• Telegram: {telegram}\n"
                                         f"• Стоимость встречи: {price}₽\n• Опыт работы: {exp} года(лет)\n"
                                         f"• Ваша сфера: {sphere}\n• О Вас: {about}\n• Вы помогли {saves} людям")
    except Error as e:
        print(e)
        await message.answer("SERVER ERROR!")


# команда "О себе"
@dp.message_handler(commands=['about'])
async def start(message: types.Message):
    username = message.from_user.username
    db_query = f"SELECT * FROM mentors WHERE mentor_telegram='@{username}'"
    try:
        with connect(
                host="193.124.118.138",
                user="me",
                password="password",
                database="project"
        ) as connection:

            with connection.cursor() as cursor:
                cursor.execute(db_query)
                for db in cursor.fetchall():
                    (num, meeting, telegram, surname, name, price, exp, saves, sphere, about) = db
                    await message.answer(f"Информация в карточке:\n\n"
                                         f"• О Вас: {about}\n")
    except Error as e:
        print(e)
        await message.answer("SERVER ERROR!")


def get_requests():
    cursor.execute("SELECT * FROM applications_for_mentoring WHERE moderation=2")

    return cursor.fetchall()


# отправка заявки на менторство
# @dp.callback_query_handler(lambda c: c.data == 'Update')
async def checking_apllicatoins_for_mentoring():
    global is_process
    global last_id

    while True:
        requests = get_requests()
        if not is_process:
            if len(requests) == 0:
                await asyncio.sleep(1)
                continue
            request = requests[0]
            last_id = request[0]
            message = f"""Новая заявка на менторство\n\n• Фамилия: {request[1]}\n• Имя: {request[2]}\n•Телеграмм: {request[3]}\n• Цена: {request[4]}\n• Опыт работы: {request[5]}\n• Сферы: {request[6]}\n• О себе: {request[7]}\n """
            inline_keyboard = InlineKeyboardMarkup(row_width=2)
            accept = InlineKeyboardButton(text="✅ Accept", callback_data="accept")
            decline = InlineKeyboardButton(text="⛔ Deny", callback_data="deny")
            inline_keyboard.add(accept, decline)

            await bot.send_message(chat_id=admin_tg, text=message, reply_markup=inline_keyboard)

            is_process = True

        await asyncio.sleep(1)


# при нажатии accept в бд идёт замена поля у человека на 1
@dp.callback_query_handler(text="accept")
async def accept_the_mentor(callback: types.CallbackQuery):
    global is_process
    global last_id

    await callback.answer("Заявка принята!")

    # замена значения у отправленного сообщения
    cursor.execute(f"UPDATE applications_for_mentoring SET moderation = 1 WHERE moderation = 2 AND id = {last_id}")
    db.commit()

    # выбор текущей заявки и занесение ее в таблицу менторов
    cursor.execute(f"SELECT * FROM applications_for_mentoring WHERE id = {last_id}")

    accepted_request = cursor.fetchall()
    about = accepted_request[0][7].replace("\n", " ")
    # print(f"VALUES = '{accepted_request[0][3]}', '{accepted_request[0][1]}', '{accepted_request[0][2]}', '{accepted_request[0][4]}', {accepted_request[0][5]}, '{accepted_request[0][6]}', '{about}'")
    cursor.execute(f"INSERT INTO mentors(mentor_telegram, mentor_surname, mentor_name, price, experience, sphere, about) VALUES('{accepted_request[0][3]}', '{accepted_request[0][1]}', '{accepted_request[0][2]}', '{accepted_request[0][4]}', {accepted_request[0][5]}, '{accepted_request[0][6]}', '{about}')")
    db.commit()

    cursor.execute(f"DELETE FROM applications_for_mentoring WHERE moderation = 1")
    db.commit()

    is_process = False


# заявка отвергнута
@dp.callback_query_handler(text="deny")
async def accept_the_mentor(callback: types.CallbackQuery):
    global is_process
    global last_id

    await callback.answer("Заявка отвергнута!")

    cursor.execute(f"UPDATE applications_for_mentoring SET moderation = 0 WHERE id = {last_id}")
    db.commit()

    cursor.execute(f"DELETE FROM applications_for_mentoring WHERE moderation = 0")
    db.commit()

    is_process = False


async def main():
    loop = asyncio.get_event_loop()
    loop.create_task(checking_apllicatoins_for_mentoring())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
