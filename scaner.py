def send_request_to_vision(text):
    messages = [
        {"role": "system", "content": "ты создан для того чтобы распознавать файлы для их вставки в документ ворд. В основном ты распознаешь отсканированную информацию с официальных писем. распознавай как самый превосходный сканер на планете. не вставляй лишние переносы строк, так как это портит вид итогового документа. Учти что в документе выравнивание текста должно быть по ширине и текст должен выглядеть красиво."},
        {"role": "user", "content": text},
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",
        messages=messages,
        max_tokens=1500,
        n=1,
        temperature=1,
    )
    return response['choices'][0]['message']['content']

@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_docs(message: types.Message):
    doc_id = message.document.file_id
    file_info = await bot.get_file(doc_id)
    downloaded_file = await bot.download_file(file_info.file_path)

    # Создание директории, если она не существует
    dir_path = '/home/rejoller/mcrbot/'
    os.makedirs(dir_path, exist_ok=True)

    # Сохранение файла на диск
    file_path = os.path.join(dir_path, 'file.pdf')
    with open(file_path, 'wb') as f:
        f.write(downloaded_file.read())

    # Конвертация PDF в список изображений
    images = convert_from_path(file_path)

    # Создание нового Word документа
    doc = Document()
    creds = service_account.Credentials.from_service_account_file(
            '/home/rejoller/mcrbot/credentials.json')

    client = vision.ImageAnnotatorClient(credentials=creds)
    full_text = ""
    for image in images:
        # Convert PIL Image to Bytes
        byte_arr = io.BytesIO()
        image.save(byte_arr, format='PNG')
        byte_arr = byte_arr.getvalue()
        image = vision.Image(content=byte_arr)

        # Делаем запрос к Google Cloud Vision API
        response = client.text_detection(image=image)
        texts = response.text_annotations

        # Сортируем блоки текста по их вертикальному положению на странице
        texts.sort(key=lambda text: text.bounding_poly.vertices[0].y)

        # Добавляем каждый блок текста в общий текст
        for text in texts:
            normalized_text = unicodedata.normalize('NFKD', text.description)
            cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', normalized_text)
            full_text += " " + cleaned_text

    # Дополнительная нормализация текста с помощью GPT-3.5-turbo
    gpt_normalized_text = send_request_to_vision(full_text)

    paragraph = doc.add_paragraph(gpt_normalized_text)

    # Установка стиля и форматирования
    run = paragraph.runs[0]
    run.font.name = 'Times New Roman'
    run.font.size = Pt(14)
    paragraph_format = paragraph.paragraph_format
    paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
    paragraph_format.line_spacing = 1
    paragraph_format.first_line_indent = Cm(1.25)

    # Save the Word document to a temporary file
    doc_path = os.path.join(dir_path, 'temp.docx')
    doc.save(doc_path)

    # Send the Word document back to the user
    with open(doc_path, "rb") as doc_file:
        await bot.send_document(message.chat.id, doc_file)
