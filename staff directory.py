def set_main_menu_button_active(chat_id, active):
    global is_main_menu_button_active
    is_main_menu_button_active[chat_id] = active


def create_go_main_menu_inline_button():
    inline_keyboard = types.InlineKeyboardMarkup()
    main_menu_button = types.InlineKeyboardButton("Выйти из справочника", callback_data="go_main_menu")
    inline_keyboard.add(main_menu_button)
    return inline_keyboard


@dp.callback_query_handler(lambda call: call.data == "go_main_menu")
async def go_main_menu_callback_handler(call):
    set_main_menu_button_active(call.message.chat.id, False)
    await bot.send_message(call.message.chat.id,
                           "Вы вышли из справочника\n\nВведите название населенного пункта, чтобы получить информацию о связи\nЧтобы узнать, кто сегодня в отпуске, жми /otpusk\nСправочник: /employee \nЕсли остались вопросы, пиши @rejoller.")
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    remove_employee_data(call.message.chat.id)
    # Здесь вызвать функцию для отправки главного меню, например:
    # await send_main_menu(call.message)


@dp.callback_query_handler(lambda call: call.data == "go_main_menu")
async def process_go_main_menu_callback(call):
    await go_main_menu_callback_handler(call)



def remove_employee_data(chat_id):
    if chat_id in stored_employees_data:
        del stored_employees_data[chat_id]

from aiogram.dispatcher.filters import Text


@dp.message_handler(Text(equals='Выйти из справочника'))
async def handle_go_main_menu(message: types.Message):
    set_main_menu_button_active(message.chat.id, False)
    await bot.send_message(message.chat.id,
                           'Вы вышли из справочника\n\nВведите название населенного пункта, чтобы получить информацию о связи\nЧтобы узнать, кто сегодня в отпуске, жми /otpusk\nСправочник: /employee \nЕсли остались вопросы, пиши @rejoller.')
    bot.clear_step_handler(message)
    remove_employee_data(message.chat.id)
    # Здесь вызвать функцию для отправки главного меню, например:
    # await send_main_menu(message)





async def handle_employee_info_message(chat_id, response):
    set_main_menu_button_active(chat_id, True)
    main_menu_inline_button = create_go_main_menu_inline_button()
    msg = await bot.send_message(chat_id, response, parse_mode='HTML', reply_markup=main_menu_inline_button)
    bot.register_next_step_handler(msg, process_employee_name_input)  # добавим вызов функции process_employee_name_input здесь


@dp.message_handler(Text(equals='Выйти из справочника'))
async def process_go_main_menu_callback(message: types.Message):
    if message.text == 'Выйти из справочника':
        await go_main_menu_callback_handler(message)
    else:
        await bot.send_message(message.chat.id, "Введите фамилию сотрудника (и, при необходимости, имя и отчество)")
        dp.register_message_handler(process_employee_name_input, content_types=types.ContentTypes.TEXT, state="*")


import json



stored_employees_data = {}


def search_employee(name_parts):
    try:
        service = get_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID_1,
            range="Справочник!A2:J",
        ).execute()
        rows = result.get('values', [])
    except HttpError as error:
        # print(f"An error occurred: {error}")
        rows = []

    found_employees = []
    for row in rows:
        if row and len(row) > 2 and row[2]:
            fio_parts = re.split(r'\s+', row[2].strip())
            if len(fio_parts) >= len(name_parts) and all(p1.lower() == p2.lower() for p1, p2 in zip(fio_parts, name_parts)):
                found_employees.append(row)

    return found_employees


@dp.message_handler(commands=['employee'])
async def handle_employee_command(message: types.Message):
    global stored_employees_data
    user_first_name = message.from_user.first_name
    name_parts = re.split(r'\s+', message.text[len('/employee'):].strip())

    if len(name_parts) < 1 or len(name_parts[0]) < 2:
        msg = await message.reply(f'{user_first_name}, введите фамилию сотрудника (и, при необходимости, имя и отчество).')
        await msg.register_next_step_handler(process_employee_name_input)
        return

    found_employees = search_employee(name_parts)
    stored_employees_data[message.chat.id] = found_employees
    await process_searched_employee_results(message, found_employees)


async def process_employee_name_input(message: types.Message):
    global stored_employees_data
    name_parts = re.split(r'\s+', message.text.strip())

    if len(name_parts) < 1 or len(name_parts[0]) < 2:
        msg = await message.reply("Введите фамилию сотрудника (и, при необходимости, имя и отчество)")
        await msg.register_next_step_handler(process_employee_name_input)
        return

    found_employees = search_employee(name_parts)
    stored_employees_data[message.chat.id] = found_employees
    await process_searched_employee_results(message, found_employees)


def format_employee_info(employee):
    fio = escape_markdown(employee[2]) if len(employee) > 2 and employee[2] else "-"
    position = escape_markdown(employee[1]) if len(employee) > 1 and employee[1] else "-"
    department = escape_markdown(employee[0]) if len(employee) > 0 and employee[0] else "-"
    place = escape_markdown(employee[5]) if len(employee) > 5 and employee[5] else "-"
    workphone = escape_markdown(employee[3]) if len(employee) > 3 and employee[3] else "-"
    private_phone = escape_markdown(employee[4]) if len(employee) > 4 and employee[4] else "-"
    bd = escape_markdown(employee[7]) if len(employee) > 7 and employee[7] else "-"
    email = escape_markdown(employee[8]) if len(employee) > 8 and employee[8] else "-"
    tg = escape_markdown(employee[9]) if len(employee) > 9 and employee[9] else "-"

    response = (
        f"<b>ФИО:</b> {fio}\n"
        f"<b>Должность:</b> {position}\n"
        f"<b>Отдел:</b> {department}\n"
        f"<b>Место работы:</b> {place}\n"
        f"<b>Рабочий телефон:</b> {workphone}\n"
        f"<b>Сотовый телефон:</b> {private_phone}\n"
        f"<b>ДР:</b> {bd}\n"
        f"<b>Email:</b> {email}\n"
        f"<b>tg:</b> {tg}"
    )
    return response


async def process_searched_employee_results(message: types.Message, found_employees):
    if not found_employees:
        error_response = 'Не удалось найти информацию по данному запросу'
        await handle_employee_info_message(message.chat.id, error_response)
        return

    if len(found_employees) == 1:
        response = format_employee_info(found_employees[0])
        await handle_employee_info_message(message.chat.id, response)

    else:
        inline_keyboard = types.InlineKeyboardMarkup(row_width=1)

        for idx, employee in enumerate(found_employees):
            button_text = employee[2]  # ФИО из таблицы

            callback_data = json.dumps({"type": "employee_info", "index": idx, "chat_id": message.chat.id})
            button = types.InlineKeyboardButton(button_text, callback_data=callback_data)
            inline_keyboard.add(button)

        await bot.send_message(message.chat.id, "Выберите сотрудника из списка:", reply_markup=inline_keyboard)
        create_go_main_menu_inline_button()


@dp.callback_query_handler(lambda call: json.loads(call.data)["type"] == "employee_info")
async def handle_employee_info_call(call: types.CallbackQuery):
    global stored_employees_data
    data = json.loads(call.data)
    index = data["index"]
    chat_id = data["chat_id"]

    found_employees = stored_employees_data.get(chat_id)

    if found_employees and index < len(found_employees):
        employee = found_employees[index]
        response = format_employee_info(employee)
        await handle_employee_info_message(chat_id, response)
    else:
        await bot.send_message(chat_id, "Не удалось получить информацию о сотруднике.")
        send_go_main_menu_button(chat_id)
