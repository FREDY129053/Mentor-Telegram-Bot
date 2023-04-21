import asyncio
import logging
import mysql
import datetime
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
admin_tg = 1202748393

# flags
is_process_mentoring = False
is_process_meeting = False
last_id_mentor = 0
last_id_meeting = 0


# команда "/start"
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    telegram_id = message.from_id
    telegram_username = message.from_user.username

    cursor.execute(f"SELECT EXISTS(SELECT * FROM telegram_info WHERE telegram_id = '{telegram_id}' OR telegram_name = '{telegram_username}')")

    if cursor.fetchone()[0] == "0":
        cursor.execute(f"INSERT INTO telegram_info(telegram_id, telegram_name) VALUES('{telegram_id}', '{telegram_username}')")
        db.commit()

    await message.answer(f"Привет!\nИспользуй: /profile для проверки 👤")


# команда просмотра профиля
@dp.message_handler(commands=['profile'])
async def start(message: types.Message):
    username = message.from_user.username

    if message.chat.id == admin_tg:
        await message.answer(f"Ваш 👤:\n\n"
                             f"🏆Вы наш админ! Поздравляю🏆")
    else:
        cursor.execute(f"SELECT * FROM mentors WHERE mentor_telegram='@{username}'")
        for db in cursor.fetchall():
            (num, meeting, telegram, surname, name, price, exp, saves, sphere, about) = db
            if saves is None:
                saves = 0
            await message.answer(f"Ваш 👤:\n\n"
                                 f"• Фамилимя: {surname}\n• Имя: {name}\n• Telegram: {telegram}\n"
                                 f"• Стоимость встречи: {price}₽\n• Опыт работы: {exp} года(лет)\n"
                                 f"• Ваша сфера: {sphere}\n• Вы помогли {saves} людям")


# команда "О себе"
@dp.message_handler(commands=['about'])
async def start(message: types.Message):
    username = message.from_user.username

    cursor.execute(f"SELECT * FROM mentors WHERE mentor_telegram='@{username}'")
    for db in cursor.fetchall():
        (num, meeting, telegram, surname, name, price, exp, saves, sphere, about) = db
        await message.answer(f"Информация в карточке:\n\n"
                             f"• О Вас: {about}\n")


# отправка заявки на менторство
async def checking_applicatoins_for_mentoring():
    global is_process_mentoring
    global last_id_mentor

    while True:
        cursor.execute("SELECT * FROM applications_for_mentoring WHERE moderation=2")
        requests = cursor.fetchall()
        db.commit()
        if not is_process_mentoring:
            if len(requests) == 0:
                await asyncio.sleep(1)
                continue
            request = requests[0]
            last_id_mentor = request[0]

            message = f"""Новая заявка на менторство\n\n• Фамилия: {request[1]}\n• Имя: {request[2]}\n•Телеграмм: {request[3]}\n• Почта: {request[4]}\n• Цена: {request[5]}\n• Опыт работы: {request[6]}\n• Сферы: {request[7]}\n• О себе: {request[8]}\n"""
            inline_keyboard = InlineKeyboardMarkup(row_width=2)
            accept = InlineKeyboardButton(text="✅ Accept", callback_data="accept")
            decline = InlineKeyboardButton(text="⛔ Deny", callback_data="deny")
            inline_keyboard.add(accept, decline)

            await bot.send_message(chat_id=admin_tg, text=message, reply_markup=inline_keyboard)

            is_process_mentoring = True

        await asyncio.sleep(1)


# заявка на менторство принята
@dp.callback_query_handler(text="accept")
async def accept_the_mentor(callback: types.CallbackQuery):
    global is_process_mentoring
    global last_id_mentor

    await callback.answer("Заявка принята!")

    cursor.execute(f"SELECT telegram FROM applications_for_mentoring WHERE id = {last_id_mentor}")
    mentor_telegram_name = cursor.fetchone()[0][1:]
    cursor.execute(f"SELECT telegram_id FROM telegram_info WHERE telegram_name = '{mentor_telegram_name}'")
    mentor_telegram_id = int(cursor.fetchone()[0])


    # замена значения у отправленного сообщения
    cursor.execute(f"UPDATE applications_for_mentoring SET moderation = 1 WHERE moderation = 2 AND id = {last_id_mentor}")
    db.commit()

    # выбор текущей заявки и занесение ее в таблицу менторов
    cursor.execute(f"SELECT * FROM applications_for_mentoring WHERE id = {last_id_mentor}")

    accepted_request = cursor.fetchall()
    cursor.execute(f"INSERT INTO mentors(mentor_telegram, mentor_surname, mentor_name, price, experience, sphere, about) VALUES('{accepted_request[0][3]}', '{accepted_request[0][1]}', '{accepted_request[0][2]}', '{accepted_request[0][4]}', {accepted_request[0][5]}, '{accepted_request[0][6]}', '{accepted_request[0][7]}')")
    db.commit()

    cursor.execute(f"DELETE FROM applications_for_mentoring WHERE moderation = 1 AND id = {last_id_mentor}")
    db.commit()

    await bot.send_message(chat_id=mentor_telegram_id, text="Заявка принята модерацией.\nВы в нашей системе.\n ⭐Желаем много встреч и клиентов!⭐\n\tP.S. С уважением модерация👩🏻‍💻")

    is_process_mentoring = False


# заявка на менторство отвергнута
@dp.callback_query_handler(text="deny")
async def deny_the_mentor(callback: types.CallbackQuery):
    global is_process_mentoring
    global last_id_mentor

    await callback.answer("Заявка отвергнута!")

    cursor.execute(f"SELECT telegram FROM applications_for_mentoring WHERE id = {last_id_mentor}")
    mentor_telegram_name = cursor.fetchone()[0][1:]
    cursor.execute(f"SELECT telegram_id FROM telegram_info WHERE telegram_name = '{mentor_telegram_name}'")
    mentor_telegram_id = int(cursor.fetchone()[0])


    cursor.execute(f"UPDATE applications_for_mentoring SET moderation = 0 WHERE id = {last_id_mentor} AND moderation = 2")
    db.commit()

    cursor.execute(f"DELETE FROM applications_for_mentoring WHERE moderation = 0 AND id = {last_id_mentor}")
    db.commit()

    await bot.send_message(chat_id=mentor_telegram_id, text="Заявка отвергнута модерацией.\n 🍀Удачи в следующий раз!🍀")

    is_process_mentoring = False


# заявки на встречу
async def checking_applicatoins_for_meeting():
    global is_process_meeting
    global last_id_meeting

    while True:
        cursor.execute("SELECT * FROM applications_for_meeting WHERE confirmation=2")
        requests = cursor.fetchall()
        db.commit()

        if not is_process_meeting:
            if len(requests) == 0:
                await asyncio.sleep(1)
                continue

            request = requests[0]
            last_id_meeting = request[6]
            new_format = "%d-%m-%Y"
            date = request[4].strftime(new_format).replace("-", ".")

            message = f"""Новая заявка на встречу\n\n• Фамилия клиента: {request[0]}\n• Имя клиента: {request[1]}\n• Телеграмм клиента: {request[3]}\n• Дата встречи: {date}"""
            inline_keyboard = InlineKeyboardMarkup(row_width=2)
            accept = InlineKeyboardButton(text="✅ Agree", callback_data="agree")
            decline = InlineKeyboardButton(text="⛔ Refuse", callback_data="refuse")
            inline_keyboard.add(accept, decline)

            cursor.execute(f"SELECT mentor_telegram FROM applications_for_meeting WHERE id = {last_id_meeting}")
            mentor_telegram_name = cursor.fetchone()[0][1:]
            cursor.execute(f"SELECT telegram_id FROM telegram_info WHERE telegram_name = '{mentor_telegram_name}'")
            mentor_telegram_id = int(cursor.fetchone()[0])

            await bot.send_message(chat_id=mentor_telegram_id, text=message, reply_markup=inline_keyboard)

            is_process_meeting = True

        await asyncio.sleep(1)


# заявка на менторство принята
@dp.callback_query_handler(text="agree")
async def agree_for_meeting(callback: types.CallbackQuery):
    global is_process_meeting
    global last_id_meeting

    await callback.answer("Вы согласились на встречу!")

    # выбор id телеграмма ментора
    cursor.execute(f"SELECT mentor_telegram FROM applications_for_meeting WHERE id = {last_id_meeting}")
    mentor_telegram_name = cursor.fetchone()[0][1:]
    cursor.execute(f"SELECT telegram_id FROM telegram_info WHERE telegram_name = '{mentor_telegram_name}'")
    mentor_telegram_id = int(cursor.fetchone()[0])

    # выбор id телеграмма пользователя
    cursor.execute(f"SELECT user_telegram FROM applications_for_meeting WHERE id = {last_id_meeting}")
    user_telegram_name = cursor.fetchone()[0][1:]
    cursor.execute(f"SELECT telegram_id FROM telegram_info WHERE telegram_name = '{user_telegram_name}'")
    user_telegram_id = int(cursor.fetchone()[0])

    # замена значения у отправленного сообщения
    cursor.execute(f"UPDATE applications_for_meeting SET confirmation = 1 WHERE confirmation = 2 AND id = {last_id_meeting}")
    db.commit()

    # выбор текущей заявки и занесение ее в таблицу менторов
    cursor.execute(f"SELECT * FROM applications_for_meeting WHERE id = {last_id_meeting}")

    accepted_request = cursor.fetchall()
    cursor.execute(f"INSERT INTO meeting(confirm_date, mentors_telegram, user_telegram) VALUES('{accepted_request[0][4]}', '{accepted_request[0][2]}', '{accepted_request[0][3]}')")
    db.commit()

    cursor.execute(f"DELETE FROM applications_for_meeting WHERE confirmation = 1 AND id = {last_id_meeting}")
    db.commit()

    await bot.send_message(chat_id=mentor_telegram_id, text="<ТЕКСТ ДЛЯ МЕНТОРА ПРИ ПРИНЯТИИ ЗАЯВКИ>")
    await bot.send_message(chat_id=user_telegram_id, text=f"Ваша заявка принята!\nTelegram ментора: @{mentor_telegram_name}\nУдачной встречи!")

    is_process_meeting = False


# заявка на менторство отвергнута
@dp.callback_query_handler(text="refuse")
async def refuse_for_meeting(callback: types.CallbackQuery):
    global is_process_meeting
    global last_id_meeting

    await callback.answer("Вы отказались от встречи!")

    # выбор id телеграмма ментора
    cursor.execute(f"SELECT mentor_telegram FROM applications_for_meeting WHERE id = {last_id_meeting}")
    mentor_telegram_name = cursor.fetchone()[0][1:]
    cursor.execute(f"SELECT telegram_id FROM telegram_info WHERE telegram_name = '{mentor_telegram_name}'")
    mentor_telegram_id = int(cursor.fetchone()[0])

    # выбор id телеграмма пользователя
    cursor.execute(f"SELECT user_telegram FROM applications_for_meeting WHERE id = {last_id_meeting}")
    user_telegram_name = cursor.fetchone()[0][1:]
    cursor.execute(f"SELECT telegram_id FROM telegram_info WHERE telegram_name = '{user_telegram_name}'")
    user_telegram_id = int(cursor.fetchone()[0])

    # замена значения у отправленного сообщения
    cursor.execute(f"UPDATE applications_for_meeting SET confirmation = 0 WHERE confirmation = 2 AND id = {last_id_meeting}")
    db.commit()

    # выбор текущей заявки и занесение ее в таблицу менторов
    cursor.execute(f"SELECT * FROM applications_for_meeting WHERE id = {last_id_meeting}")

    accepted_request = cursor.fetchall()
    cursor.execute(
        f"INSERT INTO meeting(confirm_date, mentors_telegram, user_telegram) VALUES('{accepted_request[0][4]}', '{accepted_request[0][2]}', '{accepted_request[0][3]}')")
    db.commit()

    cursor.execute(f"DELETE FROM applications_for_meeting WHERE confirmation = 0 AND id = {last_id_meeting}")
    db.commit()

    await bot.send_message(chat_id=mentor_telegram_id, text="<ТЕКСТ ДЛЯ МЕНТОРА ПРИ ОТКАЗЕ ОТ ЗАЯВКИ>")
    await bot.send_message(chat_id=user_telegram_id, text=f"Ваша заявка отклонена!\nВаше стремление радует, не останавливайтесь!\n")

    is_process_meeting = False


# функция напоминания
async def reminder():
    pass


# функция для удаления лишних людей из таблицы Username - ID
async def delete_extra():
    pass


async def main():
    loop = asyncio.get_event_loop()
    loop.create_task(checking_applicatoins_for_mentoring())
    loop.create_task(checking_applicatoins_for_meeting())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
