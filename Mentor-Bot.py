import asyncio
import logging
import mysql
import datetime

from aiogram import Bot, types
from aiogram import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from mysql.connector import connect

logging.basicConfig(level=logging.INFO)

# mysql vars
db_config = {
    "user": "me",
    "password": "password",
    "host": "193.124.118.138",
    "database": "project",
}
db = mysql.connector.connect(**db_config)
cursor = db.cursor(buffered=True)

# aiogram vars
bot = Bot(token="5703403331:AAFFuggpCLrtk5qeOpwRjW-Xfeub_0Ic1gA")
dp = Dispatcher(bot)
admin_tg = 1202748393

# datetime
new_format = "%d-%m-%Y"

# flags
is_process_mentoring = False
is_process_meeting = False
last_id_mentor = 0
last_id_meeting = 0
in_mentors = False
in_users = False
is_answered = False
what_kind_of_answer = 4


# команда "/start"
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    telegram_id = message.from_id
    telegram_username = message.from_user.username

    cursor.execute(f"SELECT EXISTS(SELECT * FROM telegram_info WHERE telegram_id = '{telegram_id}' OR telegram_name = '{telegram_username}')")

    if cursor.fetchone()[0] == "0":
        cursor.execute(f"INSERT INTO telegram_info(telegram_id, telegram_name) VALUES('{telegram_id}', '{telegram_username}')")
        db.commit()

    await message.answer(f"Привет!\nИщите менторов на:https://www.dns-mentor.ru/\nИспользуй: /profile для проверки 👤")


# команда просмотра профиля
@dp.message_handler(commands=['profile'])
async def start(message: types.Message):
    username = message.from_user.username
    current_data = datetime.date.today()

    cursor.execute(f"SELECT telegram_name FROM telegram_info WHERE telegram_id={message.chat.id}")
    db.commit()
    tg_name = cursor.fetchone()
    tg_name = tg_name[0]

    # находим человека в менторах
    in_mentors = False
    cursor.execute(f"SELECT mentor_telegram FROM mentors WHERE mentor_telegram = '@{tg_name}'")
    db.commit()
    if len(cursor.fetchone()) == 0:
        in_mentors = False
    else:
        in_mentors = True

    # находим человека в пользователях
    in_users = False
    cursor.execute(f"SELECT user_telegram FROM users WHERE user_telegram = '@{tg_name}'")
    db.commit()
    if len(cursor.fetchone()) == 0:
        in_users = False
    else:
        in_users = True

    # if message.chat.id == admin_tg:
    #     await message.answer(f"Ваш 👤:\n\n"
    #                          f"🏆Вы наш админ! Поздравляю🏆")
    if in_mentors:
        cursor.execute(f"SELECT * FROM mentors WHERE mentor_telegram='@{tg_name}'")
        db.commit()
        for _ in cursor.fetchall():
            (num, meeting, telegram, mail, surname, name, price, exp, saves, sphere, about) = _

            cursor.execute(f"SELECT * FROM meeting WHERE mentors_telegram='@{tg_name}'")
            db.commit()
            ok = cursor.fetchall()

            if len(ok) == 0:
                await message.answer(f"Ваш 👤:\n\nВы - ментор🙋🏻\n\n"
                                     f"• Фамилия: {surname}\n• Имя: {name}\n• Telegram: {telegram}\n"
                                     f"• Стоимость встречи: {price} (₽)\n• Опыт работы: {exp} года(лет)\n"
                                     f"• Ваша сфера: {sphere}\n• О вас: /about\n• Вы помогли {saves} людям\n\n")
            else:
                i = 1
                for ok in ok:
                    date, Id, mentor_tg, user_tg, state = ok[0], ok[1], ok[2], ok[3], ok[4]
                    if i > 1:
                        await message.answer(
                            f"Предстоящие встречи:\n {i}: 📅{(date.strftime(new_format)).replace('-', '.')} - {user_tg}. Осталось: {(date - current_data).days} дней!")
                    else:
                        await message.answer(f"Ваш 👤:\n\nВы - ментор🙋🏻\n\n"
                                             f"• Фамилия: {surname}\n• Имя: {name}\n• Telegram: {telegram}\n"
                                             f"💸 Стоимость встречи: {price} (₽)\n🌟 Опыт работы: {exp} года(лет)\n"
                                             f"• Ваша сфера: {sphere}\n• О вас: /about\n🤝 Вы помогли {saves} людям\n\n"
                                             f"Предстоящие встречи:\n {i}: 📅{(date.strftime(new_format)).replace('-', '.')} - {user_tg}. Осталось: {(date - current_data).days} дней!")
                        i += 1

    if in_users:
        cursor.execute(f"SELECT * FROM users WHERE user_telegram='@{tg_name}'")
        for _ in cursor.fetchall():
            (num, meeting, surname, telegram, mail, name) = _

            cursor.execute(f"SELECT * FROM meeting WHERE mentors_telegram='@{tg_name}'")
            db.commit()
            ok = cursor.fetchall()

            if len(ok) == 0:
                await message.answer(f"Ваш 👤:\n\nВы - пользователь🙆\n\n"
                                     f"• Фамилия: {surname}\n• Имя: {name}\n• Telegram: {telegram}\n\n")
            else:
                i = 1
                for ok in ok:
                    date, Id, mentor_tg, user_tg, state = ok[0], ok[1], ok[2], ok[3], ok[4]

                    if i > 1:
                        await message.answer(
                            f"Предстоящие встречи:\n {i}: {(date.strftime(new_format)).replace('-', '.')} - {mentor_tg}. Осталось: {(date - current_data).days} дней!")
                    else:
                        await message.answer(f"Ваш 👤:\n\nВы - пользователь🙆\n\n"
                                             f"• Фамилия: {surname}\n• Имя: {name}\n• Telegram: {telegram}\n\n"
                                             f"📅Предстоящие встречи:\n {i}: {(date.strftime(new_format)).replace('-', '.')} - {mentor_tg}. Осталось: {(date - current_data).days} дней!")
                        i += 1


# команда "О себе"
@dp.message_handler(commands=['about'])
async def start(message: types.Message):
    username = message.from_user.username

    cursor.execute(f"SELECT * FROM mentors WHERE mentor_telegram='@{username}'")
    for db in cursor.fetchall():
        (num, meeting, telegram, mail, surname, name, price, exp, saves, sphere, about) = db
        about = about.replace("*", "\n")
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
        await asyncio.sleep(5)
        if not is_process_mentoring:
            if len(requests) == 0:
                await asyncio.sleep(5)
                continue
            request = requests[0]
            last_id_mentor = request[0]
            about = request[8].replace("*", "\n")

            message = f"""Новая заявка на менторство\n\n• Фамилия: {request[1]}\n• Имя: {request[2]}\n•Телеграмм: {request[3]}\n• Почта: {request[4]}\n• Цена: {request[5]}\n• Опыт работы: {request[6]}\n• Сферы: {request[7]}\n• О себе: {about}\n"""
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
    await asyncio.sleep(3)

    # замена значения у отправленного сообщения
    cursor.execute(f"UPDATE applications_for_mentoring SET moderation = 1 WHERE moderation = 2 AND id = {last_id_mentor}")
    db.commit()
    await asyncio.sleep(5)

    # выбор текущей заявки и занесение ее в таблицу менторов
    cursor.execute(f"SELECT * FROM applications_for_mentoring WHERE id = {last_id_mentor}")

    accepted_request = cursor.fetchall()
    await asyncio.sleep(2)
    cursor.execute(
        f"INSERT INTO mentors(mentor_telegram, mentor_surname, mentor_name, price, experience, sphere, about) VALUES('{accepted_request[0][3]}', '{accepted_request[0][1]}', '{accepted_request[0][2]}', '{accepted_request[0][5]}', {accepted_request[0][6]}, '{accepted_request[0][7]}', '{accepted_request[0][8]}')")
    db.commit()
    await asyncio.sleep(3)

    cursor.execute(f"DELETE FROM applications_for_mentoring WHERE moderation = 1 AND id = {last_id_mentor}")
    db.commit()
    await asyncio.sleep(2)

    await bot.send_message(chat_id=mentor_telegram_id,
                           text="Заявка принята модерацией.\nВы в нашей системе.\n ⭐Желаем много встреч и клиентов!⭐\n\tP.S. С уважением модерация👩🏻‍💻")

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
    await asyncio.sleep(2)

    cursor.execute(f"UPDATE applications_for_mentoring SET moderation = 0 WHERE id = {last_id_mentor} AND moderation = 2")
    db.commit()
    await asyncio.sleep(1)

    cursor.execute(f"DELETE FROM applications_for_mentoring WHERE moderation = 0 AND id = {last_id_mentor}")
    db.commit()
    await asyncio.sleep(3)

    await bot.send_message(chat_id=mentor_telegram_id, text="Заявка отвергнута модерацией.\n 🍀Удачи в следующий раз!🍀")

    is_process_mentoring = False


# заявки на встречу
async def checking_applicatoins_for_meeting():
    global is_process_meeting
    global last_id_meeting

    while True:
        cursor.execute("SELECT * FROM applications_for_meeting")
        requests = cursor.fetchall()
        db.commit()
        await asyncio.sleep(1)

        if not is_process_meeting:
            if len(requests) == 0:
                await asyncio.sleep(1)
                continue
            for i in range(0, len(requests)):
                request = requests[i]
                last_id_meeting = request[6]
                meeting_date = request[4].strftime(new_format).replace("-", ".")

                message = f"""Новая заявка на встречу\n\n• Фамилия клиента: {request[0]}\n• Имя клиента: {request[1]}\n• Телеграмм клиента: {request[3]}\n• Дата встречи: {meeting_date}"""
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


# заявка на встречу принята
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
    cursor.execute(
        f"INSERT INTO meeting(confirm_date, mentors_telegram, user_telegram) VALUES('{accepted_request[0][4]}', '{accepted_request[0][2]}', '{accepted_request[0][3]}')")
    db.commit()

    cursor.execute(f"DELETE FROM applications_for_meeting WHERE confirmation = 1 AND id = {last_id_meeting}")
    db.commit()

    await bot.send_message(chat_id=mentor_telegram_id, text="<ТЕКСТ ДЛЯ МЕНТОРА ПРИ ПРИНЯТИИ ЗАЯВКИ>")
    await bot.send_message(chat_id=user_telegram_id, text=f"Ваша заявка принята!\nTelegram ментора: @{mentor_telegram_name}\nУдачной встречи!")

    is_process_meeting = False


# заявка на встречу отвергнута
@dp.callback_query_handler(text="refuse")
async def refuse_for_meeting(callback: types.CallbackQuery):
    global is_process_meeting
    global last_id_meeting

    await callback.answer("Вы отказались от встречи!")

    # изменение состояние заявки
    cursor.execute(f"UPDATE applications_for_meeting SET confirmation = 0 WHERE id = {last_id_meeting}")
    db.commit()

    # получение id чата с ментором
    cursor.execute(f"SELECT mentor_telegram FROM applications_for_meeting WHERE id = {last_id_meeting} AND confirmation = 0")
    db.commit()
    mentor_username = cursor.fetchone()[0][1:]
    cursor.execute(f"SELECT telegram_id FROM telegram_info WHERE telegram_name = '{mentor_username}'")
    db.commit()
    mentor_id = int(cursor.fetchone()[0])

    # получение id чата с пользователем
    cursor.execute(f"SELECT user_telegram FROM applications_for_meeting WHERE id = {last_id_meeting} AND confirmation = 0")
    db.commit()
    user_username = cursor.fetchone()[0][1:]
    cursor.execute(f"SELECT telegram_id FROM telegram_info WHERE telegram_name = '{user_username}'")
    db.commit()
    user_id = int(cursor.fetchone()[0])

    cursor.execute(f"DELETE FROM applications_for_meeting WHERE confirmation = 0 AND id = {last_id_meeting}")
    db.commit()

    await bot.send_message(chat_id=mentor_id, text="Удачи в поисках новых клиентов💚")
    await bot.send_message(chat_id=user_id, text="Ваша заявка на встречу не подтвердилась!\nВаше стремление радует, не останавливайтесь!!!")

    is_process_meeting = False


@dp.callback_query_handler(text="+1")
async def plus_1_to_mentor(callback: types.CallbackQuery):
    global is_answered
    global what_kind_of_answer

    is_answered = True
    what_kind_of_answer = 1

    await callback.answer("Спасибо за Ваше мнение!")


@dp.callback_query_handler(text="+0.5")
async def plus_0_5_to_mentor(callback: types.CallbackQuery):
    global is_answered
    global what_kind_of_answer

    is_answered = True
    what_kind_of_answer = 2

    await callback.answer("Спасибо за Ваше мнение!")


@dp.callback_query_handler(text="+0")
async def plus_0_to_mentor(callback: types.CallbackQuery):
    global is_answered
    global what_kind_of_answer

    is_answered = True
    what_kind_of_answer = 0

    await callback.answer("Спасибо за Ваше мнение!")


# функция напоминания
async def reminder():
    global is_answered
    global what_kind_of_answer

    while True:
        current_date = datetime.datetime.now()

        # db.commit()
        cursor.execute("SELECT id FROM meeting")
        db.commit()
        id_list = cursor.fetchall()
        await asyncio.sleep(1)

        if len(id_list) == 0:
            continue
        else:
            for meeting in id_list:
                cursor.execute(f"SELECT confirm_date FROM meeting WHERE id = {meeting[0]}")
                db.commit()
                meeting_date = cursor.fetchone()[0]
                await asyncio.sleep(1)

                difference = meeting_date - current_date.date()

                cursor.execute(f"SELECT statement FROM meeting WHERE id = {meeting[0]}")
                db.commit()
                state = cursor.fetchone()[0]
                await asyncio.sleep(1)

                # напоминалка, когда до встречи менее или равно 3 дня и потом раз в 12 часов
                # if difference <= datetime.timedelta(days=3) and (state != "1") and current_date.hour % 12 == 0 and current_date.minute == 0 and current_date.second == 0:
                if difference <= datetime.timedelta(days=3) and (state != "1") and current_date.hour % (12 or 13 or 14 or 15) == 0 and current_date.minute % 15 == 0 and current_date.second == 0:
                    cursor.execute(f"SELECT mentors_telegram FROM meeting WHERE id = '{meeting[0]}'")
                    check_mentor = cursor.fetchall()[0][0][1:]
                    db.commit()
                    await asyncio.sleep(1)

                    cursor.execute(f"SELECT user_telegram FROM meeting WHERE id = '{meeting[0]}'")
                    check_user = cursor.fetchall()[0][0][1:]
                    db.commit()
                    await asyncio.sleep(1)

                    cursor.execute(f"SELECT telegram_id FROM telegram_info WHERE telegram_name = '{check_mentor}'")
                    mentor_tg = cursor.fetchone()[0]
                    db.commit()
                    await asyncio.sleep(1)

                    cursor.execute(f"SELECT telegram_id FROM telegram_info WHERE telegram_name = '{check_user}'")
                    user_tg = cursor.fetchone()[0]
                    db.commit()
                    await asyncio.sleep(1)

                    await bot.send_message(chat_id=int(mentor_tg), text="Mentor")
                    await bot.send_message(chat_id=int(user_tg), text="User")

                # смена состояния заявки, когда уже день встречи
                if current_date == meeting_date:
                    cursor.execute(f"UPDATE meeting SET statement = 1 WHERE id = {meeting[0]}")
                    db.commit()
                    await asyncio.sleep(1)

                # если текущая дата равна дата встречи + 1 день и 12 часов, то пользователю сообщение о полезности встречи
                cursor.execute(f"SELECT statement FROM meeting WHERE id = {meeting[0]}")
                db.commit()
                state = cursor.fetchone()[0]
                await asyncio.sleep(1)
                # if True:
                if current_date.date() == meeting_date + datetime.timedelta(days=1, hours=12) and state == 1 and current_date.hour % 12 == 0 and current_date.minute == 0 and current_date.second == 0:
                    cursor.execute(f"SELECT user_telegram FROM meeting WHERE id = '{meeting[0]}'")
                    check_user = cursor.fetchall()[0][0][1:]
                    db.commit()
                    await asyncio.sleep(1)

                    cursor.execute(f"SELECT telegram_id FROM telegram_info WHERE telegram_name = '{check_user}'")
                    user_tg = cursor.fetchone()[0]
                    db.commit()
                    await asyncio.sleep(1)

                    inline_keyboard = InlineKeyboardMarkup(row_width=1)
                    good = InlineKeyboardButton(text="✅ Да, выдалась полезная встреча", callback_data="+1")
                    normal = InlineKeyboardButton(text="⚠ Встреча прошла, но не прям полезная...", callback_data="+0.5")
                    bad = InlineKeyboardButton(text="⛔ Встреча ужасная, все плохо", callback_data="+0")
                    inline_keyboard.add(good, normal, bad)

                    await bot.send_message(chat_id=int(user_tg), text="Расскажите, пожалуйста, как прошла ваша встреча с ментором?)",
                                           reply_markup=inline_keyboard)

                    # await asyncio.sleep(43_200)

                # если текущая дата равна дата встречи + 2 дня и нет ответа от пользователя, то встреча удаляется и ментору + 0.5
                # если есть ответ "+", то + 1 к ментору
                # если есть ответ "-", то + 0 к ментору
                if state == 0:
                    if current_date.date() > meeting_date + datetime.timedelta(days=2) and is_answered and what_kind_of_answer == 1:
                        cursor.execute(f"SELECT mentors_telegram FROM meeting WHERE id = {meeting[0]}")
                        db.commit()
                        tg_mentor = cursor.fetchone()[0]
                        await asyncio.sleep(1)

                        cursor.execute(f"DELETE FROM meeting WHERE id = {meeting[0]}")
                        db.commit()
                        await asyncio.sleep(1)

                        cursor.execute(f"UPDATE mentors SET number_of_rescued=number_of_rescued+1 WHERE mentor_telegram = '{tg_mentor}'")
                        db.commit()
                        await asyncio.sleep(1)

                    if current_date.date() > meeting_date + datetime.timedelta(days=2) and is_answered and what_kind_of_answer == 0:
                        cursor.execute(f"SELECT mentors_telegram FROM meeting WHERE id = {meeting[0]}")
                        db.commit()
                        tg_mentor = cursor.fetchone()[0]
                        await asyncio.sleep(1)

                        cursor.execute(f"DELETE FROM meeting WHERE id = {meeting[0]}")
                        db.commit()
                        await asyncio.sleep(1)

                        cursor.execute(f"UPDATE mentors SET number_of_rescued=number_of_rescued+0 WHERE mentor_telegram = '{tg_mentor}'")
                        db.commit()
                        await asyncio.sleep(1)

                    if current_date.date() > meeting_date + datetime.timedelta(days=2) and is_answered and what_kind_of_answer == 2:
                        cursor.execute(f"SELECT mentors_telegram FROM meeting WHERE id = {meeting[0]}")
                        db.commit()
                        tg_mentor = cursor.fetchone()[0]
                        await asyncio.sleep(1)

                        cursor.execute(f"DELETE FROM meeting WHERE id = {meeting[0]}")
                        db.commit()
                        await asyncio.sleep(1)

                        cursor.execute(f"UPDATE mentors SET number_of_rescued=number_of_rescued+0.5 WHERE mentor_telegram = '{tg_mentor}'")
                        db.commit()
                        await asyncio.sleep(1)

                    if current_date.date() > meeting_date + datetime.timedelta(days=3) and (not is_answered):
                        cursor.execute(f"SELECT mentors_telegram FROM meeting WHERE id = {meeting[0]}")
                        db.commit()
                        tg_mentor = cursor.fetchone()[0]
                        await asyncio.sleep(1)

                        cursor.execute(f"DELETE FROM meeting WHERE id = {meeting[0]}")
                        db.commit()
                        await asyncio.sleep(1)

                        cursor.execute(f"UPDATE mentors SET number_of_rescued=number_of_rescued+0.5 WHERE mentor_telegram = '{tg_mentor}'")
                        db.commit()
                        await asyncio.sleep(1)


# функция для удаления лишних людей из таблицы Username - ID раз в неделю
async def delete_extra():
    global in_mentors
    global in_users

    while True:
        cursor.execute("SELECT telegram_name FROM telegram_info")
        cursor.fetchall()
        db.commit()

        for username in cursor:
            cursor.execute(f"SELECT EXISTS(SELECT * FROM mentors WHERE mentor_telegram = '@{username}'")
            db.commit()
            if cursor.fetchone()[0] == "1":
                in_mentors = True

            cursor.execute(f"SELECT EXISTS(SELECT * FROM users WHERE user_telegram = '@{username}'")
            db.commit()
            if cursor.fetchone()[0] == "1":
                in_mentors = True

            if in_mentors and in_users is False:
                cursor.execute(f"DELETE FROM telegram_info WHERE telegram_name = '{username}'")
                db.commit()

        await asyncio.sleep(604_800)


async def main():
    loop = asyncio.get_event_loop()

    loop.create_task(checking_applicatoins_for_mentoring())
    loop.create_task(checking_applicatoins_for_meeting())
    loop.create_task(reminder())
    loop.create_task(delete_extra())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
