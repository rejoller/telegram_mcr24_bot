from google_connections import get_votes_data
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from datetime import datetime, timedelta
import csv
import time
from google_connections import get_authorized_client_and_spreadsheet, search_yandex_2023_values, search_in_pokazatel_504p, search_in_ucn2, search_schools_values, get_votes_data, search_in_results, load_otpusk_data, search_values, search_values_levenshtein, search_szoreg_values, get_value
import asyncio
from additional import normalize_text_v2, split_message, create_excel_file_2
import json
import html
from weather import get_weather
import re
import logging
import os
import traceback
import tempfile
import shutil





bot_token = '6235250605:AAE6zT8AjON9SucXqbLlRvtcJTrEJ1fZ0BA'
bot = Bot(token=bot_token)
dp = Dispatcher(bot, storage=MemoryStorage())


info_text_storage = {}
user_messages = {}
additional_info_storage = {}
espd_info_storage = {}
szoreg_info_storage = {}
schools_info_storage = {}
message_storage = {}
survey_data_storage = {}
response_storage = {}


def log_user_data(user_id, first_name, last_name, username, message_text):
    file_path = 'users_data.csv'
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Проверяем, существует ли файл. Если нет, создаем его с заголовками
    try:
        with open(file_path, 'x', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'User ID', 'First Name', 'Last Name', 'Username', 'Message'])
    except FileExistsError:
        pass

    # Записываем данные пользователя в файл
    with open(file_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([current_time, user_id, first_name, last_name, username, message_text])

# Функция для сохранения данных пользователя из сообщения
async def log_user_data_from_message(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username
    message_text = message.text

    log_user_data(user_id, first_name, last_name, username, message_text)





class Form(StatesGroup):
    waiting_for_number = State()




@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    user_first_name = message.from_user.first_name
    await message.answer(
        f'Привет, {user_first_name}!\nЯ бот который может поделиться с тобой информацией о связи в Красноярском крае. Для этого введи название населенного пункта или муниципального образования (например "Курагино" или "Абанский")\nЧтобы узнать информацию о сотовой связи, выбери /2g /3g или /4g. Чтобы получить информацию о населенных пунктах без сотовой связи жми /nomobile \n\n'
        'Чтобы узнать о подключении к ТОРКНД, введи сообщение "тор" и наименование муниципального образования. '
        'Например, "тор Енисейский".\n'
        'Если нужна статистика по всему краю, жми /knd_kraj\n\n'
        'Чтобы узнать, кто сегодня в отпуске, жми /otpusk\n'

        'Если остались вопросы, пиши @rejoller.')


@dp.message_handler(commands=['votes'])
async def send_votes(message: types.Message):
    try:
        gc, spreadsheet = await get_authorized_client_and_spreadsheet()
        data = await get_votes_data(spreadsheet)
        excel_data = create_excel_file_2(data)  # убрали headers здесь
        await log_user_data_from_message(message)
        # Сохраняем данные Excel во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp:
            temp.write(excel_data.read())
            temp_filename = temp.name

        # Переименовываем файл перед отправкой
        final_filename = "Голосование УЦН 2_0 2024.xlsx"
        shutil.move(temp_filename, final_filename)

        # Отправляем файл
        with open(final_filename, "rb") as temp:
            await bot.send_document(message.chat.id, temp, caption='Информация о голосовании УЦН 2.0 2024')

        # Удаляем файл после отправки
        os.remove(final_filename)

    except Exception as e:
        tb = traceback.format_exc()  # Получить трассировку стека
        print("An error occurred while handling /votes:", tb)  # Печатает трассировку стека
        await message.reply(f'Произошла ошибка при обработке вашего запроса: {e}\n{tb}')  # Включает ошибку и трассировку стека в ответ пользователю




def get_employees_on_vacation(otpusk_data, days_ahead=3):
    today = datetime.today().date()
    future_vacation_start = today + timedelta(days=days_ahead)
    employees_on_vacation = []
    employees_starting_vacation_soon = []

    for row_idx, row in enumerate(otpusk_data):
        if row_idx == 0:  # пропустить заголовки таблицы
            continue
        if len(row) >= 5:
            try:
                start_date = datetime.strptime(row[3], "%d.%m.%Y").date()
                end_date = datetime.strptime(row[4], "%d.%m.%Y").date()

                if start_date <= today <= end_date:
                    employees_on_vacation.append(row)

                if today < start_date <= future_vacation_start:
                    employees_starting_vacation_soon.append(row)

            except ValueError:
                pass  # игнорировать строки с неправильным форматом даты

    return employees_on_vacation, employees_starting_vacation_soon


@dp.message_handler(commands=['otpusk'])
async def handle_otpusk_command(message: types.Message, days_ahead=30):
    # Загрузка данных из файла с информацией об отпусках
    print ('отпуск запущен')
    #await message.reply('Загружаю данные')
    await bot.send_message(message.chat.id, '🏝Загружаю️')
    await log_user_data_from_message(message)
    otpusk_data = await load_otpusk_data()


    # Получение списка сотрудников, которые сегодня в отпуске и уходят в отпуск в ближайшие 14 дней
    employees_on_vacation, employees_starting_vacation_soon = get_employees_on_vacation(otpusk_data, days_ahead)

    response = ""

    if employees_on_vacation:
        response += '*Сегодня в отпуске*😎\n\n'
        for row in employees_on_vacation:
            response += f"{row[0]}, {row[1]}\n"
            response += f"  - Дата начала отпуска: {row[3]}\n"
            response += f"  - Дата окончания отпуска: {row[4]}\n\n"

    if employees_starting_vacation_soon:
        response += f"\n*Сотрудники, уходящие в отпуск в ближайшие {days_ahead} дней*\n\n"
        for emp_row in employees_starting_vacation_soon:
            response += f"{emp_row[0]}, {emp_row[1]}\n"
            response += f"  - Дата начала отпуска: {emp_row[3]}\n"
            response += f"  - Дата окончания отпуска: {emp_row[4]}\n\n"

    if not response:
        response = "Сегодня никто не в отпуске, и никто не уходит в отпуск в ближайшие 14 дней."

    #response += f"\n\nЕсли нужен справочник, жми /employee"

    # Отправка запроса в GPT API
    #gpt_response = await send_request_to_otpusk_command(message.chat.id, response)
    #print(response)
    messages = split_message(response)

    # Отправка обработанной информации пользователю
    for msg in messages:
        #await message.reply(msg, parse_mode='Markdown')
        await bot.send_message(message.chat.id, msg, parse_mode='Markdown')




@dp.message_handler()
async def handle_text(message: types.Message, state: FSMContext):
    user_state = await state.get_state()
    if user_state == Form.waiting_for_number.state:
        return



    print ('основная работает')
    global info_text_storage
    user_first_name = message.from_user.first_name
    await log_user_data_from_message(message)
    chat_id = message.chat.id



    user_id = message.from_user.id  # Получаем user_id
   # if user_id == 964635576:
    #    await bot.send_message(message.chat.id, "Для того чтобы пользоваться ботом отправьте сообщение муниципалам")
      #  return  # Завершаем выполнение функции
    votes_response = ""
    response = ''
    ucn2_response = ""
    operators_response = ''
    survey_results_values = ''

    base_text = f'С'
    final_text = f'🧐Секундочку, {user_first_name}'
    await bot.send_message(message.chat.id, f'🧐Секундочку, {user_first_name}')
    # Замеряем время выполнения функции search_values
    start_time = time.time()

    gc, spreadsheet = await get_authorized_client_and_spreadsheet()
    found_values_a = await search_values(message.text, spreadsheet)



   # found_values_a, found_values_s = await search_values(message.text)
   # found_mszu_values = await check_mszu_column_b(message.text)

    end_time = time.time()
    execution_time = end_time - start_time
    print("Время выполнения функции search_values: ", execution_time, "секунд")

    if not found_values_a:
        # Проверяем метод Левенштейна с 70% совпадениями
        levenshtein_matches = await search_values_levenshtein(message.text, spreadsheet, threshold=0.4, max_results=5)

        if levenshtein_matches:
            unique_matches = set(levenshtein_matches)  # Используем множество, чтобы убрать повторяющиеся значения
            first_match = list(unique_matches)  # Преобразуем обратно в список
            formatted_matches = "\n".join([f'`{match}`' for match in first_match])  # Создаем строки с обратными кавычками для каждого значения
            await bot.send_message(message.chat.id, f'Проверьте правильность написания и попробуйте еще раз. Возможно вы имели в виду:\n(нажмите на населенный пункт, чтобы скопировать)\n\n{formatted_matches}', parse_mode='Markdown')
        else:
            await bot.send_message(message.chat.id, 'Не удалось найти информацию по данному запросу.\nПроверьте, правильно ли введено название населенного пункта и попробуйте еще раз')
        return

    # Если соответствие найдено в столбце A
    allowed_users = {964635576, 1063749463, 374056328, 572346758, 434872315, 1045874687, 1063749463, 487922464, 371098269}
    if found_values_a:
        found_values = found_values_a
        await state.update_data(found_values=found_values)
      #  await bot.send_message(chat_id="430334520", text="Света, ты получаешь минус один балл!")
       # await bot.send_message(chat_id="964635576", text="Света, ты получаешь минус один балл!")



        if len(found_values) == 1:
            latitude = found_values[0][7]  # Широта находится в столбце H таблицы goroda2.0
            longitude = found_values[0][8]



            weather_info = await get_weather(latitude, longitude, "7cc8daec601b8354e0bc6350592d6f98")
            yandex_2023_response = ''
            pokazatel_504p_lines = []
           # ucn2_values = await search_in_ucn2(found_values[0][4])
           # yandex_2023_values = await search_yandex_2023_values(found_values[0][4])
            #pokazatel_504p_values = await search_in_pokazatel_504p(found_values[0][4])  # Используйте значение из столбца 4 в found_values_a



            if len(found_values) > 0 and len(found_values[0]) > 4:
                # Подразумевается, что если условие выполнено, то можно безопасно обращаться к found_values[5][4]

                ucn2_values, yandex_2023_values, pokazatel_504p_values, survey_results_values  = await asyncio.gather(
                    search_in_ucn2(found_values[0][4], spreadsheet),
                    search_yandex_2023_values(found_values[0][4], spreadsheet),
                    search_in_pokazatel_504p(found_values[0][4], spreadsheet),
                    search_in_results(found_values[0][4], spreadsheet)
                )
            else:
                # Если условие не выполнено, значит индекса [5][4] нет, и нужно обойтись без search_in_results
                ucn2_values, yandex_2023_values, pokazatel_504p_values = await asyncio.gather(
                    search_in_ucn2(found_values[0][4], spreadsheet),
                    search_yandex_2023_values(found_values[0][4], spreadsheet),
                    search_in_pokazatel_504p(found_values[0][4], spreadsheet)
                )
                survey_results_values = None




            if found_values_a:
                for row in found_values_a:
                    # Создаем словарь с операторами и их значениями, используя метод get для безопасного обращения к элементам списка
                    operators = {
                        "Tele2": row[39] if len(row) > 39 else None,
                        "Мегафон": row[40] if len(row) > 40 else None,
                        "Билайн": row[41] if len(row) > 41 else None,
                        "МТС": row[42] if len(row) > 42 else None,
                    }

                    operators_response = '\nОценка жителей:\n'

                    # Список для хранения ответов от операторов
                    operator_responses = []

                    for operator_name, operator_value in operators.items():

                        if operator_value:  # Проверка на наличие значения (не None и не пустая строка)
                            # Переводим значение в строку, чтобы избежать ошибок при выполнении метода replace
                            operator_value_str = str(operator_value)

                            # Пытаемся найти качество сигнала
                            signal_quality = re.search(r'Отсутствует|Низкое|Среднее|Хорошее', operator_value_str, re.IGNORECASE)
                            if signal_quality:
                                signal_quality = signal_quality.group()
                                if "Отсутствует" in signal_quality:
                                    signal_level = "🔴Отсутствует"
                                elif "Низкое" in signal_quality:
                                    signal_level = "🟠Низкое"
                                elif "Среднее" in signal_quality:
                                    signal_level = "🟡Среднее"
                                elif "Хорошее" in signal_quality:
                                    signal_level = "🟢Хорошее"
                                else:
                                    signal_level = "❓Неизвестно"

                                # Заменяем найденное качество сигнала на его эмодзи-эквивалент
                                operator_value_str = operator_value_str.replace(signal_quality, signal_level)
                            else:
                                operator_value_str = operator_value_str

                            # Заменяем "(" и ")" на " "
                            operator_value_str = operator_value_str.replace("(", " ").replace(")", " ")
                            operator_responses.append(f'{operator_name}: {operator_value_str}\n')
                        else:
                            # Если нет данных по оператору, не добавляем его в ответ
                            continue



                    # Если нет данных ни по одному оператору, добавляем сообщение об отсутствии данных
                    if not operator_responses:
                        operators_response += 'Нет данных\n'
                    else:
                        operators_response += ''.join(operator_responses)

                    response += operators_response




            if yandex_2023_values:
                yandex_2023_response = '\n\n\n<b>Информация из таблицы 2023</b>\n\n'
                for row in yandex_2023_values:
                    yandex_2023_response += f'Тип подключения: {row[4]}\nОператор: {row[15]}\nСоглашение: {row[7]}\nПодписание соглашения с МЦР: {row[8]}\nПодписание соглашения с АГЗ: {row[9]}\nДата подписания контракта: {row[11]}\nДата установки АМС: {row[12]}\nДата монтажа БС: {row[13]}\nЗапуск услуг: {row[14]}\n\n'
            if pokazatel_504p_values:
                for index in range(6, 10):
                    if len(pokazatel_504p_values[0]) > index and pokazatel_504p_values[0][index] and pokazatel_504p_values[0][index].strip():
                        value = pokazatel_504p_values[0][index]
                        if "Хорошее" in value:
                            value = value.replace("Хорошее", "🟢Хорошее")
                        if "Низкое" in value:
                            value = value.replace("Низкое", "🟠Низкое")
                        pokazatel_504p_lines.append(value)
            if ucn2_values:
                for row in ucn2_values:
                    ucn2_response = ''

                    if 4 < len(row) and row[4]:  # Проверка наличия значения
                        ucn2_response += '  Информация от Теле2:\n    -СМР: ' + row[4] + '\n'
                    if 5 < len(row) and row[5]:  # Проверка наличия значения
                        ucn2_response += '    -Запуск: ' + row[5] + '\n'
                    if 6 < len(row) and row[6]:  # Проверка наличия значения
                        ucn2_response += '    -Комментарии: ' + row[6] + '\n'

                    if ucn2_response:  # Если ucn2_response не пуст, добавить вводную строку в начало
                        ucn2_response = '\n\n\n<b>УЦН 2.0 2023</b>\n' + ucn2_response
                        response += ucn2_response







                response += ucn2_response

            pokazatel_504p_response = "\n".join(pokazatel_504p_lines) if pokazatel_504p_lines else "🔴отсутствует"


            if "4G" in pokazatel_504p_response:
                votes_response = ""
            else:
                # Теперь этот код выполняется только если "4G" не найдено в pokazatel_504p_response
                try:
                    if len(found_values[0]) > 38:  # Убедитесь, что у вас достаточно данных в строке
                        votes = found_values[0][34] or "неизвестно"
                        update_time = found_values[0][35] or "неизвестно"
                        rank = found_values[0][36] or "неизвестно"
                        same_votes_np = found_values[0][38] or "неизвестно"

                        if votes != "неизвестно" and update_time != "неизвестно" and rank != "неизвестно" and same_votes_np != "неизвестно":
                            votes_response = f'\n\n<b>Голосование УЦН 2.0 2024</b>\n\n📊Количество голосов: <b>{votes}</b> (такое же количество голосов имеют {same_votes_np} населённых пунктов)\n🏆Место в рейтинге: {rank}\nДата обновления информации: {update_time}'
                        else:
                            print("Debug: Не все данные для блока голосования были найдены.")
                except Exception as e:
                    print(f"Debug: Ошибка при извлечении данных о голосах: {e}")


          #  operators_response = await generate_operators_response([found_values_a])
            #print('operators_response', operators_response)  # Добавлено для отладки




          #  response = f'{found_values[0][1]}* ({weather_info})\n\n👥Население (2010 г.): {found_values[0][2]} чел.\n👥Население (2020 г.): {found_values[0][5]} чел.\n\nСотовая связь: {pokazatel_504p_response}\nИнтернет: {get_value(found_values[0], 9)}\n\nКоличество таксофонов: {get_value(found_values[0], 12)}{yandex_2023_response}{ucn2_response}\nЧтобы узнать кто сегодня в отпуске жми /otpusk \nЕсли нужен справочник, жми /employee'




          #  response = f'<b>{found_values[0][1]}</b> {weather_info}\n\n👥Население (2010 г.): {found_values[0][2]} чел.\n👥Население (2020 г.): {found_values[0][5]} чел.\n\n<b>Сотовая связь:</b>\n{pokazatel_504p_response}\n{operators_response}\n\nИнтернет: {await get_value(found_values[0], 9)}\n\nКоличество таксофонов: {await get_value(found_values[0], 12)}{yandex_2023_response}{ucn2_response}{votes_response}\n\nЕсли хочешь узнать о голосовании УЦН 2.0 2024 жми /votes\n\nБот для проведения опросов жителей - <a href="http://t.me/providers_rating_bot">@providers_rating_bot</a>'


            response = f'<b>{found_values[0][1]}</b>  {weather_info}'

            selsovet_info = []
            arctic_info = []
            taksofony_info = []
            tanya_sub_info_year = []
            tanya_sub_info_provider = []
            internet_info = []
            population_2010 = []
            population_2020 = []
            itog_ucn_2023 = []
            
            
            try:
                selsovet_info, tanya_sub_info_year, tanya_sub_info_provider, taksofony_info, arctic_info, internet_info, population_2010, population_2020, itog_ucn_2023 = await asyncio.gather(
                    get_value(found_values[0], 20),
                    get_value(found_values[0], 13),
                    get_value(found_values[0], 14),
                    get_value(found_values[0], 12),
                    get_value(found_values[0], 6),
                    get_value(found_values[0], 9),
                    get_value(found_values[0], 2),
                    get_value(found_values[0], 5),
                    get_value(found_values[0], 24),
                    return_exceptions=True  # Возврат исключений как объектов
                )
            except Exception as e:
                print(f"Произошла ошибка: {e}")


            if selsovet_info:
                response += f'\n{selsovet_info}'
            if arctic_info:
                response += f'\n❄️️арктическая зона❄️️'
            response += f'\n\n👥население 2010 г: {population_2010} чел.\n👥население 2020 г: {population_2020} чел.\n\n'

            if taksofony_info:
                response += f'\n☎️таксофон: {taksofony_info}'

            response += f'\n🌐интернет: {internet_info}️'
            response += f'\n\n📱<b>Сотовая связь:</b>\n{pokazatel_504p_response}'




            if tanya_sub_info_year and tanya_sub_info_provider:
                response += f'\n\nнаселенный пункт был подключен в рамках государственной программый "Развитие информационного общества" в {tanya_sub_info_year} году, оператор {tanya_sub_info_provider}'

            if itog_ucn_2023:
                response += f'\n\nкомментарий Минцифры России об УЦН 2024: {itog_ucn_2023}'
            response += f'\n{operators_response}\n'



            response += f'{yandex_2023_response}{ucn2_response}{votes_response}\nЕсли хочешь узнать о голосовании УЦН 2.0 2024 жми /votes\n\nБот для проведения опросов жителей - <a href="http://t.me/providers_rating_bot">@providers_rating_bot</a>'

            info_text_storage[message.chat.id] = response


            await bot.send_location(message.chat.id, latitude, longitude)
           # response = await send_request_to_gpt(chat_id, response)
           # await bot.send_message(chat_id="374056328", text="ку-ку")

            messages = split_message(response)



            for msg in messages:
                await bot.send_message(message.chat.id, msg, parse_mode='HTML', disable_web_page_preview=True)



            szoreg_values, schools_values = await asyncio.gather(

                search_szoreg_values(found_values[0][4], spreadsheet),
                search_schools_values(found_values[0][4], spreadsheet)
            )


            inline_keyboard = types.InlineKeyboardMarkup(row_width=3)

            if message.from_user.id in allowed_users:
                button_digital_ministry_info = types.InlineKeyboardButton("😈Подготовить ответ на обращение(БЕТА)", callback_data=json.dumps({"type": "digital_ministry_info", "chat_id": message.chat.id}))
                inline_keyboard.add(button_digital_ministry_info)
                #button_digital_ministry_info_post = types.InlineKeyboardButton("Сделать пост ВК", callback_data=json.dumps({"type": "digital_ministry_info_post", "chat_id": message.chat.id}))
                #inline_keyboard.add(button_digital_ministry_info_post)




            survey_data_storage[message.chat.id] = survey_results_values

            if survey_results_values:
                survey_inline_keyboard = types.InlineKeyboardMarkup()
                button_survey_results = types.InlineKeyboardButton("Показать результаты опроса", callback_data=json.dumps({"type": "survey_chart", "chat_id": message.chat.id}))
                survey_inline_keyboard.add(button_survey_results)
                await bot.send_message(message.chat.id, "Найдены результаты опроса. Хотите посмотреть?", reply_markup=survey_inline_keyboard)



          #  if szofed_values or espd_values or szoreg_values or schools_values or info_text_storage:
            if  szoreg_values or schools_values or info_text_storage:

                if szoreg_values:
                    szoreg_response = '🏢<b> Учреждения, подключенные по госпрограмме</b> \n\n'
                    for i, row in enumerate(szoreg_values, 1):
                        szoreg_response += f'\n{i}. <b>Тип:</b> {row[7]}\n<b>Наименование:</b> {row[8]}\n<b>Адрес:</b> {row[5]} \n<b>Тип подключения:</b> {row[6]}\n<b>Пропускная способность:</b> {row[9]}\n<b>Комментарии:</b> {row[10]}\n'

                    callback_data = json.dumps({"type": "szoreg_info", "chat_id": message.chat.id})
                    szoreg_info_storage[message.chat.id] = szoreg_response
                    button_szoreg_info = types.InlineKeyboardButton("🏢Список учреждений",callback_data=callback_data)
                    inline_keyboard.add(button_szoreg_info)

                if schools_values:
                    schools_response = '🏫<b>Школы:</b>\n'
                    for i, row in enumerate(schools_values, 1):
                        schools_response += f'\n{i} '
                        if len(row) > 7:
                            schools_response += f'<b>{html.escape(row[12])}</b>\n'
                        if len(row) > 12:
                            schools_response += f'\n{html.escape(row[7])}\n'
                        if len(row) > 14:
                            schools_response += f'\n{html.escape(row[14])}, '
                        if len(row) > 13:
                            schools_response += f'{html.escape(row[13])} Мб/с\n'
                        if len(row) > 20:
                            schools_response += f'{html.escape(row[20])}'
                        schools_response += '\n'

                    callback_data = json.dumps({"type": "schools_info", "chat_id": message.chat.id})
                    schools_info_storage[message.chat.id] = schools_response
                    button_schools_info = types.InlineKeyboardButton("🏫Школы",callback_data=callback_data)
                    inline_keyboard.add(button_schools_info)

                await bot.send_message(message.chat.id, "⬇️Дополнительная информация⬇️", reply_markup=inline_keyboard)
            response_storage[message.chat.id] = response

        if len(found_values) > 1:
            values = [(await get_value(row, 1), await get_value(row, 2)) for row in found_values]
            values_with_numbers = [f"{i + 1}. {value[0]}" for i, value in enumerate(values)]
            msg = '\n'.join(values_with_numbers)

            messages = split_message(f'Найдено несколько населенных пунктов с таким названием. \n\n{msg}')

            for msg in messages:
                await bot.send_message(message.chat.id, msg)

            buttons = [str(i + 1) for i in range(len(found_values))]
            buttons.append("Отмена")
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)

            keyboard.add(*buttons)
            await bot.send_message(message.chat.id, 'Выберите номер необходимого населенного пункта:', reply_markup=keyboard)
            await Form.waiting_for_number.set()








@dp.message_handler(state=Form.waiting_for_number)
async def handle_choice(message: types.Message, state: FSMContext):
    start_time = time.time()
    try:
        data = await state.get_data()
        found_values = data.get('found_values')

        index_text = message.text
        user_first_name = message.from_user.first_name
        chat_id = message.chat.id
        response = ""
        pokazatel_504p_lines = []
        votes_response = ""
        yandex_2023_response = ""
        ucn2_response = ""

        # Проверки ввода пользователя
        if index_text == "Отмена":
            await bot.send_message(chat_id, 'Поиск отменен.', reply_markup=types.ReplyKeyboardRemove())
            await state.reset_state()
            return
        if not index_text.isdigit():
            await bot.send_message(chat_id, 'Введено некорректное значение. Пожалуйста, введите число.')
            return

        index = int(index_text)
        if index <= 0 or index > len(found_values):
            await bot.send_message(chat_id, f'Введено некорректное значение. Пожалуйста, введите число в диапазоне от 1 до {len(found_values)}.')
            return

        selected_np = found_values[index - 1]
        latitude = selected_np[7]
        longitude = selected_np[8]

        # Получаем все необходимые данные асинхронно
        gc, spreadsheet = await get_authorized_client_and_spreadsheet()

        weather_info, yandex_2023_values, pokazatel_504p_values, survey_results_values, ucn2_values = await asyncio.gather(
            get_weather(latitude, longitude, "7cc8daec601b8354e0bc6350592d6f98"),
            search_yandex_2023_values(selected_np[4], spreadsheet),
            search_in_pokazatel_504p(selected_np[4], spreadsheet),
            search_in_results(selected_np[4], spreadsheet),

            search_in_ucn2(selected_np[4], spreadsheet)
        )

        # Создаем словарь с операторами и их значениями
        operators = {
            "Tele2": selected_np[39] if len(selected_np) > 39 else None,
            "Мегафон": selected_np[40] if len(selected_np) > 40 else None,
            "Билайн": selected_np[41] if len(selected_np) > 41 else None,
            "МТС": selected_np[42] if len(selected_np) > 42 else None,
        }

        operators_response = '\nОценка жителей:\n'

        # Список для хранения ответов от операторов
        operator_responses = []

        for operator_name, operator_value in operators.items():

            if operator_value:  # Проверка на наличие значения (не None и не пустая строка)
                # Переводим значение в строку, чтобы избежать ошибок при выполнении метода replace
                operator_value_str = str(operator_value)

                # Пытаемся найти качество сигнала
                signal_quality = re.search(r'Отсутствует|Низкое|Среднее|Хорошее', operator_value_str, re.IGNORECASE)
                if signal_quality:
                    signal_quality = signal_quality.group()
                    if "Отсутствует" in signal_quality:
                        signal_level = "🔴Отсутствует"
                    elif "Низкое" in signal_quality:
                        signal_level = "🟠Низкое"
                    elif "Среднее" in signal_quality:
                        signal_level = "🟡Среднее"
                    elif "Хорошее" in signal_quality:
                        signal_level = "🟢Хорошее"
                    else:
                        signal_level = "❓Неизвестно"

                    # Заменяем найденное качество сигнала на его эмодзи-эквивалент
                    operator_value_str = operator_value_str.replace(signal_quality, signal_level)
                else:
                    operator_value_str = operator_value_str

                # Заменяем "(" и ")" на " "
                operator_value_str = operator_value_str.replace("(", " ").replace(")", " ")
                operator_responses.append(f'{operator_name}: {operator_value_str}\n')
            else:
                # Если нет данных по оператору, не добавляем его в ответ
                continue

        # Если нет данных ни по одному оператору, добавляем сообщение об отсутствии данных
        if not operator_responses:
            operators_response += 'Нет данных\n'
        else:
            operators_response += ''.join(operator_responses)

        response += operators_response

        if yandex_2023_values:
            yandex_2023_response = '\n\n<b>Информация из таблицы 2023</b>\n\n'
            for row in yandex_2023_values:
                yandex_2023_response += f'Тип подключения: {row[4]}\nОператор: {row[15]}\nСоглашение: {row[7]}\nПодписание соглашения с МЦР: {row[8]}\nПодписание соглашения с АГЗ: {row[9]}\nДата подписания контракта: {row[11]}\nДата установки АМС: {row[12]}\nДата монтажа БС: {row[13]}\nЗапуск услуг: {row[14]}\n\n'

        if len(pokazatel_504p_values) > 0:
            for i in range(6, 10):
                if len(pokazatel_504p_values[0]) > i and pokazatel_504p_values[0][i] and pokazatel_504p_values[0][i].strip():
                    value = pokazatel_504p_values[0][i]
                    value = value.replace("Хорошее", "🟢Хорошее").replace("Низкое", "🟠Низкое")
                    pokazatel_504p_lines.append(f"{value}")

        pokazatel_504p_response = "\n".join(pokazatel_504p_lines) if pokazatel_504p_lines else "🔴отсутствует"

        if "4G" in pokazatel_504p_response:
            votes_response = ""
        else:
            if len(selected_np) > 38:
                votes = selected_np[34] or "неизвестно"  # Количество голосов находится в 35-ом столбце
                update_time = selected_np[35] or "неизвестно"  # Время обновления находится в 36-ом столбце
                rank = selected_np[36] or "неизвестно"  # Рейтинг находится в 37-ом столбце
                same_votes_np = selected_np[38] or "неизвестно"  # Количество НП с таким же количеством голосов находится в 39-ом столбце
                if votes != "неизвестно" and update_time != "неизвестно" and rank != "неизвестно" and same_votes_np != "неизвестно":
                    votes_response = f'\n\n<b>Голосование УЦН 2.0 2024</b>\n\n📊Количество голосов: <b>{votes}</b> (такое же количество голосов имеют {same_votes_np} населённых пунктов)\n🏆Место в рейтинге: {rank}\nДата обновления информации: {update_time}'
                else:
                    print("Debug: Не все данные для блока голосования были найдены.")
        response += votes_response

        if ucn2_values:
            for row in ucn2_values:
                ucn2_response = ''

                if 4 < len(row) and row[4]:  # Проверка наличия значения
                    ucn2_response += '  Информация от Теле2:\n    -СМР: ' + row[4] + '\n'
                if 5 < len(row) and row[5]:  # Проверка наличия значения
                    ucn2_response += '    -Запуск: ' + row[5] + '\n'
                if 6 < len(row) and row[6]:  # Проверка наличия значения
                    ucn2_response += '    -Комментарии: ' + row[6] + '\n'

                if ucn2_response:  # Если ucn2_response не пуст, добавить вводную строку в начало
                    ucn2_response = '\n\n\n<b>УЦН 2.0 2023</b>\n' + ucn2_response
                    response += ucn2_response
        survey_data_storage[message.chat.id] = survey_results_values
        selsovet_info = []
        arctic_info = []
        taksofony_info = []
        tanya_sub_info_year = []
        tanya_sub_info_provider = []
        internet_info = []
        population_2010 = []
        population_2020 = []
        itog_ucn_2023 = []
        
        try:
            selsovet_info, tanya_sub_info_year, tanya_sub_info_provider, taksofony_info, arctic_info, internet_info, population_2010, population_2020, itog_ucn_2023 = await asyncio.gather(
                get_value(found_values[index - 1], 20),
                get_value(found_values[index - 1], 13),
                get_value(found_values[index - 1], 14),
                get_value(found_values[index - 1], 12),
                get_value(found_values[index - 1], 6),
                get_value(found_values[index - 1], 9),
                get_value(found_values[index - 1], 2),
                get_value(found_values[index - 1], 5),
                get_value(found_values[index - 1], 24),
                return_exceptions=True  # Возврат исключений как объектов
            )
        except Exception as e:
            print(f"Произошла ошибка: {e}")
        print(population_2020)
     #   response = f'<b>{await get_value(found_values[index - 1], 1)}</b> {weather_info}\n\n👥Население (2010 г): {await get_value(found_values[index - 1], 2)} чел.\n👥Население(2020 г): {await get_value(found_values[index - 1], 5)} чел.\n\n<b>Сотовая связь:</b>\n{pokazatel_504p_response}\n{operators_response}\n\nИнтернет: {await get_value(found_values[index - 1], 9)}\n\nКоличество таксофонов: {await get_value(found_values[index - 1], 12)}{ucn2_response}{yandex_2023_response}{votes_response}\n\nЕсли хочешь узнать о голосовании УЦН 2.0 2024 жми /votes\nБот для проведения опросов жителей - <a href="http://t.me/providers_rating_bot">@providers_rating_bot</a>'

        response = f'<b>{await get_value(found_values[index - 1], 1)}</b>  {weather_info}'
            
        if selsovet_info:
            response += f'\n{selsovet_info}'


        if arctic_info:
            response += f'\n❄️️арктическая зона❄️️'


        response += f'\n\n👥население 2010 г: {population_2010} чел.\n👥население 2020 г: {population_2020} чел.'

        if taksofony_info:
                response += f'\n☎️таксофон: {taksofony_info}'

        response += f'\n🌐интернет: {internet_info}️'
        response += f'\n\n📱<b>Сотовая связь:</b>\n{pokazatel_504p_response}'


        if tanya_sub_info_year and tanya_sub_info_provider:
            response += f'\n\nнаселенный пункт был подключен в рамках государственной программый "Развитие информационного общества" в {tanya_sub_info_year} году, оператор {tanya_sub_info_provider}'

        if itog_ucn_2023:
            response += f'\n\nкомментарий Минцифры России об УЦН 2024: {itog_ucn_2023}'

        response += f'\n{operators_response}\n'

        response += f'{ucn2_response}{yandex_2023_response}{votes_response}\nЕсли хочешь узнать о голосовании УЦН 2.0 2024 жми /votes\nБот для проведения опросов жителей - <a href="http://t.me/providers_rating_bot">@providers_rating_bot</a>'

        info_text_storage[message.chat.id] = response


        await bot.send_message(message.chat.id, "<b>Выбранный населенный пункт</b>", parse_mode='HTML', reply_markup=types.ReplyKeyboardRemove())
        await bot.send_location(message.chat.id, latitude, longitude)
        #response = await send_request_to_gpt(chat_id, response)
        messages = split_message(response)


        allowed_users = {964635576, 1063749463, 374056328, 572346758, 434872315, 1045874687, 1063749463, 487922464, 371098269}
        for msg in messages:
            await bot.send_message(message.chat.id, msg, parse_mode='HTML', disable_web_page_preview=True)

        szoreg_values, schools_values = await asyncio.gather(


            search_szoreg_values(selected_np[4], spreadsheet),
            search_schools_values(selected_np[4], spreadsheet)

        )
        await state.reset_state()
        inline_keyboard = types.InlineKeyboardMarkup()

        if survey_results_values:
            survey_inline_keyboard = types.InlineKeyboardMarkup()
            button_survey_results = types.InlineKeyboardButton("Показать результаты опроса", callback_data=json.dumps({"type": "survey_chart", "chat_id": message.chat.id}))
            survey_inline_keyboard.add(button_survey_results)
            await bot.send_message(message.chat.id, "Найдены результаты опроса. Хотите посмотреть?", reply_markup=survey_inline_keyboard)

        if message.from_user.id in allowed_users:
            button_digital_ministry_info = types.InlineKeyboardButton("😈Подготовить ответ на обращение(БЕТА)", callback_data=json.dumps({"type": "digital_ministry_info", "chat_id": message.chat.id}))
            inline_keyboard.add(button_digital_ministry_info)

        if szoreg_values:
            szoreg_response = '🏢<b>Учреждения, подключенные по госпрограмме</b>\n\n'
            for i, row in enumerate(szoreg_values, 1):
                szoreg_response += f'\n{i}. <b>Тип:</b> {row[7]}\n<b>Наименование:</b> {row[8]}\n<b>Адрес:</b> {row[5]} \n<b>Тип подключения:</b> {row[6]}\n<b>Пропускная способность:</b> {row[9]}\n<b>Комментарии:</b> {row[10]}\n'

            callback_data = json.dumps({"type": "szoreg_info", "chat_id":message.chat.id})
            szoreg_info_storage[message.chat.id] = szoreg_response
            button_szoreg_info = types.InlineKeyboardButton("🏢Список учреждений", callback_data=callback_data)
            inline_keyboard.add(button_szoreg_info)

        if schools_values:
            schools_response = '🏫<b>Школы:</b>\n'
            for i, row in enumerate(schools_values, 1):
                schools_response += f'\n\n{i}. '
                if len(row) > 7:
                    schools_response += f'<b>{html.escape(row[12])}</b>\n'
                if len(row) > 12:
                    schools_response += f'\n{html.escape(row[7])}\n'
                if len(row) > 14:
                    schools_response += f'\n{html.escape(row[14])}, '
                if len(row) > 13:
                    schools_response += f'{html.escape(row[13])} Мб/с\n'
                if len(row) > 20:
                    schools_response += f'{html.escape(row[20])}'
                schools_response += '\n'

            callback_data = json.dumps({"type": "schools_info", "chat_id": message.chat.id})
            schools_info_storage[message.chat.id] = schools_response
            button_schools_info = types.InlineKeyboardButton("🏫Школы",callback_data=callback_data)
            inline_keyboard.add(button_schools_info)

        await bot.send_message(message.chat.id, "⬇️Дополнительная информация⬇️", reply_markup=inline_keyboard)

    except ValueError:

        await bot.send_message(message.chat.id, 'Введено некорректное значение. Пожалуйста, введите число в диапазоне от 1 до {}.'.format(len(found_values)))




async def handle_additional_info(query):
    chat_id = json.loads(query.data)["chat_id"]
    if chat_id in additional_info_storage:
        response = additional_info_storage[chat_id]
        messages = split_message(response)
        for message_group in messages:
            msg = ''.join(message_group)
            if msg.strip():  # Проверка, что сообщение не пустое
                await bot.send_message(chat_id, msg, parse_mode='Markdown')

        await bot.answer_callback_query(query.id)
    else:
        await bot.answer_callback_query(query.id, "Дополнительная информация недоступна.")




async def handle_szoreg_info(query):
    chat_id = json.loads(query.data)["chat_id"]
    if chat_id in szoreg_info_storage:
        response = szoreg_info_storage[chat_id]
        messages = split_message(response)
        for message_group in messages:
            msg = ''.join(message_group)
            if msg.strip():  # Проверка, что сообщение не пустое
                await bot.send_message(chat_id, msg, parse_mode='HTML')

        await bot.answer_callback_query(query.id)
    else:
        await bot.answer_callback_query(query.id, "Информация из таблицы СЗО (региональный контракт) недоступна.")


async def handle_schools_info(query):
    chat_id = json.loads(query.data)["chat_id"]
    if chat_id in schools_info_storage:
        response = schools_info_storage[chat_id]
        messages = split_message(response)
        for message_group in messages:
            msg = ''.join(message_group)
            if msg.strip():  # Проверка, что сообщение не пустое
                await bot.send_message(chat_id, msg, parse_mode='HTML')

        await bot.answer_callback_query(query.id)
    else:
        await bot.answer_callback_query(query.id, "Информация из таблицы по школам недоступна.")




from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
from itertools import chain
import pandas as pd
import json


async def handle_survey_chart(query):
    print("handle_survey_chart called with query data:", query.data)
    chat_id = json.loads(query.data)["chat_id"]

    if chat_id in survey_data_storage:
        logging.info("Data found for chat_id %s", chat_id)
        survey_data = survey_data_storage[chat_id]

        data_list = []

        # Создание списка словарей с данными для каждой строки
        for data_row in survey_data:
            # Убедимся, что у нас есть достаточно данных для каждого столбца
            data_row += [None] * (14 - len(data_row))

            row_data = {
                "Дата": data_row[0],
                "ID": data_row[1],
                "Имя": data_row[2],
                "Фамилия": data_row[3],
                "Ник": data_row[4],
                "Ключ": data_row[5],
                "Уровень_Tele2": data_row[6],
                "Качество_Tele2": data_row[7],
                "Уровень_Megafon": data_row[8],
                "Качество_Megafon": data_row[9],
                "Уровень_Beeline": data_row[10],
                "Качество_Beeline": data_row[11],
                "Уровень_MTS": data_row[12],
                "Качество_MTS": data_row[13],
            }
            data_list.append(row_data)

        # Преобразование данных в DataFrame
        data_df = pd.DataFrame(data_list)
        print("DataFrame created with data:", data_df)

        title = "Результаты опроса"  # Установите нужный заголовок для графика

        # Перебираем все строки в DataFrame
                # Перебираем все строки в DataFrame
      #  for idx, row in data_df.iterrows():
        try:
            #print(f"Calling create_individual_radar_chart for row {idx}...")
            await create_individual_radar_chart(chat_id, data_df, title)  # передаем весь DataFrame, а не одну строку
        except Exception as e:
            print("An error occurred:", e)
            logging.error("An error occurred: %s", e, exc_info=True)

    else:
        print(f"No data found for chat_id {chat_id}")



async def create_individual_radar_chart(chat_id, data_df, title):
    print("create_individual_radar_chart called with data:", data_df)

    # Создайте новое изображение с белым фоном
    img_width, img_height = 1000, 600
    img = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(img)

    # Добавьте заголовок
    title_font_path = "fonts/ofont.ru_Geologica.ttf"
    title_font = ImageFont.truetype(title_font_path, 30)
    text_font = ImageFont.truetype(title_font_path, 18)

    title_bbox = draw.textbbox((0,0), title, font=title_font)
    title_width, title_height = title_bbox[2] - title_bbox[0], title_bbox[3] - title_bbox[1]
    draw.text(((img_width - title_width) // 2, 20), title, fill="black", font=title_font)

    # Загрузите логотипы и уменьшите их
    logo_paths = [
        'logos/tele2_1.png',
        'logos/megafon_1.png',
        'logos/beeline_1.png',
        'logos/mts_1.png',
    ]

    logos = []
    resize_factors = [0.1, 0.1, 0.1*2, 0.1/3] # Уменьшаем МТС в 3 раза меньше и увеличиваем Билайн в 2 раза больше
    for i, path in enumerate(logo_paths):
        logo = Image.open(path)
        logo_width, logo_height = logo.size
        logos.append(logo.resize((int(logo_width * resize_factors[i]), int(logo_height * resize_factors[i]))))

    # Добавьте логотипы
    column_width = img_width // 4
    for i, logo in enumerate(logos):
        x = column_width * i + (column_width - logo.width) // 2
        y = 100
        if i in [1, 2]:  # индексы для Билайн и Мегафон
            # Создаем отдельное изображение для наложения
            logo_img = Image.new('RGBA', (img_width, img_height), (255, 255, 255, 0))
            logo_img.paste(logo, (x, y))

            # Накладываем логотип на основное изображение
            img = Image.alpha_composite(img.convert('RGBA'), logo_img).convert('RGB')
        else:
            # Для других логотипов просто вставляем их
            img.paste(logo, (x, y))

    # Создаем новый объект draw для текущего изображения
    draw = ImageDraw.Draw(img)

    # Сформулируйте текст для каждой строки в data_df и добавьте его на график
    operator_columns = [
        ('Уровень_Tele2', 'Качество_Tele2'),
        ('Уровень_Megafon', 'Качество_Megafon'),
        ('Уровень_Beeline', 'Качество_Beeline'),
        ('Уровень_MTS', 'Качество_MTS')
    ]

    y_start = y + logos[0].height + 20
    y_step = 20

    for idx, row_series in data_df.iterrows():
        for i, (level_column, quality_column) in enumerate(operator_columns):
            # Проверка на наличие данных для каждого оператора
            if pd.notnull(row_series[level_column]) or pd.notnull(row_series[quality_column]):
                text = f"{row_series.get(level_column, 'Нет данных')} {row_series.get(quality_column, 'Нет данных')}"
            else:
                text = "Нет данных"

            x = column_width * i + (column_width - logos[i].width) // 2  # Исправляем позиционирование текста
            y_text = y_start + idx * y_step
            
            draw.text((x, y_text), text, fill="black", font=text_font)

    # Сохраните и отправьте изображение
    temp_file_path = "temp_survey_result.png"
    img.save(temp_file_path)

    # Отправляем изображение пользователю
    await bot.send_photo(chat_id, open(temp_file_path, 'rb'))

    # Удаляем временный файл
    os.remove(temp_file_path)






dp.register_callback_query_handler(handle_additional_info, lambda query: json.loads(query.data)["type"] == "additional_info")
#dp.register_callback_query_handler(handle_espd_info, lambda query: json.loads(query.data)["type"] == "espd_info")
dp.register_callback_query_handler(handle_szoreg_info, lambda query: json.loads(query.data)["type"] == "szoreg_info")
dp.register_callback_query_handler(handle_schools_info, lambda query: json.loads(query.data)["type"] == "schools_info")
#dp.register_callback_query_handler(handle_digital_ministry_info, lambda query: json.loads(query.data)["type"] == "digital_ministry_info")
#dp.register_callback_query_handler(handle_digital_ministry_info_post, lambda query: json.loads(query.data)["type"] == "digital_ministry_info_post")
dp.register_callback_query_handler(handle_survey_chart, lambda query: json.loads(query.data)["type"] == "survey_chart")