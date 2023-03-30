# ГИВЦ ФСН № ОО-2
Скрипт для просмотра статуса и даты загрузки отчёта в личном кабинете `cabinet.miccedu.ru`
## Важно, для корректного использования нужно знать айди, под которыми зарегистрированы ваши организации в системе ГИВЦ
### Установка
```
git clone https://github.com/AndrewTaker/oo2.git
cd oo2
python -m venv venv
source venv/bin/activate # для unix
source venv/scripts/activate # для windows
pip install -m requirements.txt
cd api
python -m main
```
### Настройка
- нужен аккаунт гугл девелопер [ссылка на документацию](https://developers.google.com/workspace/guides/create-credentials#desktop-app);
- нужно знать айди организаций, которые были присвоены в системе ГИВЦ;
- нужен файл `credentials.json` в папке `secrets`;
- нужен файл `.env` в папке `secrets` со следующими переменными:
```
SPREADSHEET_ID=id гугл таблицы
GIVC_LOGIN=логин личного кабинета ГИВЦ
GIVC_PASSWORD=пароль личного кабинета ГИВЦ
```
### Глобальные переменные
```
SCOPES = ['https://www.googleapis.com/auth/spreadsheets'] # тут можно убрать или добавить скоупы, которые вы зарегистрировали

START = datetime.strptime('08:50', "%H:%M").time() # время, в которое скрипт начинает работу
END = datetime.strptime('18:00', "%H:%M").time() # время, в которе скрит заканчивает работу
SLEEP_TIME = 600 # перерыв между запросами статуса отчёта на `cabinet.miccedu.ru` в секундах

CODES_RANGE = 'Sheet1!A2:A163' # диапазон значение с кодам, по ним скрипт будет искать статус отчёта
STATUS_RANGE = 'Sheet1!H2:H163' # диапазон, в который нужно вписать значения статуса отчёта
DATE_RANGE = 'Sheet1!G2:G163' # диапазон, в который нужно вписать значения дату загрузки отчёта
UPDATE_TIME_RANGE = 'Sheet1!J3' # ссылка на ячейку, в которую будет вписано время последнего запроса
```
## todo
- logs;
- better reusability;
- PROBABLY make it possible to parse org ids from cabinet;
- make a stand-alone app?