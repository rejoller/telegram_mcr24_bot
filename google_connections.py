import gspread
from google.oauth2 import service_account
import gspread_asyncio
import re
from additional import normalize_text_v2, split_message
from config import SPREADSHEET_ID
from fuzzywuzzy import fuzz


SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = 'credentials.json'
creds = None
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)






credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)






async def get_authorized_client_and_spreadsheet():
    agcm = gspread_asyncio.AsyncioGspreadClientManager(lambda: creds)
    gc = await agcm.authorize()
    spreadsheet = await gc.open_by_key(SPREADSHEET_ID)
    return gc, spreadsheet


async def get_value(row, index, default_value=''):
    try:
        return row[index]
    except IndexError:
        return default_value


async def search_szoreg_values(query, spreadsheet):
    try:
        # Сгенерировать ключ для кэширования на основе запроса
     #   cache_key = f"szoreg_values:{query.lower()}"


        # Попытаться получить данные из кэша
     #   cached_data = await storage.get_data(chat=cache_key)
   #     if cached_data:
       #     cached_data = json.loads(cached_data)  # Десериализация данных

       #     return cached_data



        # Если данных в кэше нет, продолжаем поиск в таблице
        result = await spreadsheet.values_batch_get('szoreg!A1:Q10000')
        rows = result.get('valueRanges', [])[0].get('values', [])
        found_values = [row for row in rows if query.lower() == row[0].lower()]

        # Сохранить результаты в кэше перед возвратом
    #    await storage.set_data(chat=cache_key, data=json.dumps(found_values))



        return found_values
    except Exception as e:
        print("An error occurred during search_szoreg_values:", e)
        return None





async def search_yandex_2023_values(query, spreadsheet):
    try:
        # Сгенерировать ключ для кэширования на основе запроса
        #cache_key = f"yandex_2023_values:{query.lower()}"


        # Попытаться получить данные из кэша
       # cached_data = await storage.get_data(chat=cache_key)
       # if cached_data:
       #     cached_data = json.loads(cached_data)  # Десериализация данных

      #     return cached_data


        # Если данных в кэше нет, продолжаем поиск в таблице
        result = await spreadsheet.values_batch_get('2023!A3:P50')
        rows = result.get('valueRanges', [])[0].get('values', [])
        found_values = [row for row in rows if query.lower() == row[0].lower()]

        # Сохранить результаты в кэше перед возвратом
      #  await storage.set_data(chat=cache_key, data=json.dumps(found_values))



        return found_values
    except Exception as e:
        print("An error occurred during search_yandex_2023_values:", e)
        return None


async def search_in_pokazatel_504p(query, spreadsheet):
    try:
        # Сгенерировать ключ для кэширования на основе запроса
       # cache_key = f"pokazatel_504p_values:{query.lower()}"


        # Попытаться получить данные из кэша
      #  cached_data = await storage.get_data(chat=cache_key)
       # if cached_data:
      #      cached_data = json.loads(cached_data)  # Десериализация данных

       #     return cached_data



        # Если данных в кэше нет, продолжаем поиск в таблице
        result = await spreadsheet.values_batch_get('показатель 504-п!A1:K1719')
        rows = result.get('valueRanges', [])[0].get('values', [])
        found_values = [row for row in rows if query.lower() == row[0].lower()]

        # Сохранить результаты в кэше перед возвратом
     #   await storage.set_data(chat=cache_key, data=json.dumps(found_values))



        return found_values
    except Exception as e:
        print("An error occurred during search_in_pokazatel_504p:", e)
        return []


async def search_in_ucn2(query, spreadsheet):
    try:
        # Сгенерировать ключ для кэширования на основе запроса
      #  cache_key = f"ucn2_values:{query.lower()}"


        # Попытаться получить данные из кэша
       # cached_data = await storage.get_data(chat=cache_key)
       # if cached_data:
          #  cached_data = json.loads(cached_data)  # Десериализация данных

           # return cached_data



        # Если данных в кэше нет, продолжаем поиск в таблице
        result = await spreadsheet.values_batch_get('УЦН 2.0 (2023)!A1:K800')
        rows = result.get('valueRanges', [])[0].get('values', [])
        found_values = [row for row in rows if query.lower() == row[0].lower()]

        # Сохранить результаты в кэше перед возвратом
       # await storage.set_data(chat=cache_key, data=json.dumps(found_values))



        return found_values
    except Exception as e:
        print("An error occurred during search_in_ucn2:", e)
        return None


async def search_schools_values(query, spreadsheet):
    try:
        # Сгенерировать ключ для кэширования на основе запроса
      #  cache_key = f"schools_values:{query.lower()}"


        # Попытаться получить данные из кэша
        #cached_data = await storage.get_data(chat=cache_key)
       # if cached_data:
        #   cached_data = json.loads(cached_data)  # Десериализация данных

         #   return cached_data



        # Если данных в кэше нет, продолжаем поиск в таблице
        result = await spreadsheet.values_batch_get('Школы!A1:U1500')
        rows = result.get('valueRanges', [])[0].get('values', [])
        found_values = [row for row in rows if query.lower() == row[0].lower()]

        # Сохранить результаты в кэше перед возвратом
       # await storage.set_data(chat=cache_key, data=json.dumps(found_values))



        return found_values
    except Exception as e:
        print("An error occurred during search_schools_values:", e)
        return None




async def get_votes_data(spreadsheet):
    try:
        result = await spreadsheet.values_batch_get('votes!A2:D2000')
        rows = result.get('valueRanges', [])[0].get('values', [])
        return rows
    except Exception as e:
        print("An error occurred while getting votes data:", e)
        raise e



async def search_in_results(query, spreadsheet):
    try:
        # Сгенерировать ключ для кэширования на основе запроса
        #cache_key = f"results:{query.lower()}"


        # Попытаться получить данные из кэша
        #cached_data = await storage.get_data(chat=cache_key)
        #if cached_data:
         #   cached_data = json.loads(cached_data)  # Десериализация данных

         #   return cached_data


        # Если данных в кэше нет, продолжаем поиск в таблице
        result = await spreadsheet.values_batch_get('Результаты опроса!A1:N')
        rows = result.get('valueRanges', [])[0].get('values', [])
        found_values = [row for row in rows if query.lower() == row[5].lower()]

        # Сохранить результаты в кэше перед возвратом
       # await storage.set_data(chat=cache_key, data=json.dumps(found_values))


        return found_values
    except Exception as e:
        print(f"An error occurred during search_in_results: {e}")
        return None




async def load_otpusk_data():
    agcm = gspread_asyncio.AsyncioGspreadClientManager(lambda: creds)
    gc = await agcm.authorize()
    spreadsheet = await gc.open_by_key(SPREADSHEET_ID)
    sheet = await spreadsheet.worksheet('otpusk')
    rows = await sheet.get('A1:F100')
    return rows
    
    
    
    
async def search_values(query, spreadsheet):
    try:
        # Сгенерировать ключ для кэширования на основе запроса
    #    cache_key = f"values_a:{query.lower()}"
     #   print(f"Cache key in search_values: {cache_key}")

        # Попытаться получить данные из кэша
     #   cached_data = await storage.get_data(chat=cache_key)
     #   if cached_data:
      #      cached_data = json.loads(cached_data)  # Десериализация данных
      #      print("Data found in cache")
      #      return cached_data

      #  print("Data not found in cache, fetching fresh data")

        # Если данных в кэше нет, продолжаем поиск в таблице
        range_name = 'goroda2.0!A1:AQ1721'
        result = await spreadsheet.values_batch_get(range_name)
        rows = result.get('valueRanges', [])[0].get('values', [])
        normalized_query = normalize_text_v2(query.lower())

        found_values_a = []


        for row in rows:
            try:
                if len(row) > 0 and normalized_query == normalize_text_v2(row[0].lower()):
                    found_values_a.append(row)
            except IndexError:
                pass

        # Сохранить результаты в кэше перед возвратом
      #  await storage.set_data(chat=cache_key, data=json.dumps((found_values_a)))
     #   print("Data fetched and saved to cache")

        return found_values_a
    except Exception as e:
        print("An error occurred during search_values:", e)
        return None
        


async def search_values_levenshtein(query, spreadsheet, threshold=0.7, max_results=5):
    try:
        # Открываем конкретный диапазон
        range_name = 'goroda2.0!A1:AM1721'
        result = await spreadsheet.values_batch_get(range_name)
        rows = result.get('valueRanges', [])[0].get('values', [])
        normalized_query = normalize_text_v2(query)

        # Создаем список для хранения всех совпадений
        all_matches = []

        for row in rows:
            try:
                if len(row) > 0:
                    similarity = fuzz.token_sort_ratio(normalized_query, normalize_text_v2(row[0]))
                    if similarity >= (threshold * 100):
                        all_matches.append((row, similarity))
            except IndexError:
                pass

        # Сортируем все совпадения по показателю сходства в обратном порядке (от большего к меньшему)
        sorted_matches = sorted(all_matches, key=lambda x: x[1], reverse=True)

        # Берем до max_results наиболее релевантных результатов
        top_matches = sorted_matches[:max_results]

        # Получаем только значения из первых позиций в каждом совпадении
        found_values_a = [match[0][0] for match in top_matches]

        return found_values_a
    except Exception as e:
        print("An error occurred during search_values_levenshtein:", e)
        return []