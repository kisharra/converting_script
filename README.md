# 📁 Проект: Конвертация видео

## 📑 Оглавление

* [db\_handler.py](#db_handlerpy)
* [single\_handler.py](#single_handlerpy)
* [dir\_handler.py](#dir_handlerpy)
* [main\_handler.py](#main_handlerpy)


---

## 📄 `db_handler.py`

Файл содержит класс `Db_query`, предназначенный для работы с SQLite и MariaDB базами данных. Обеспечивает создание таблиц, вставку и выборку данных, а также обновление статуса задач конвертации.

### `class Db_query`

**Инициализация:**

```python
Db_query(config: dict)
```

* **config**: словарь с настройками путей к SQLite и параметрами подключения MariaDB.
* Инициализирует:

  * путь к SQLite-файлу базы данных
  * параметры подключения к MariaDB

---

### `def table_exists(self, table_name)`

* **Параметры**: `table_name` (str) — имя таблицы
* **Возвращает**: `bool` — существует ли таблица в SQLite

### `def create_table(self)`

* **Параметры**: нет
* **Возвращает**: None
* Создаёт таблицы `Files` и `ConversionTasks`, если они не существуют

### `def save_file_data(self, data, streams, is_film, is_serial)`

* **Параметры**:

  * `data`: dict — данные о видео
  * `streams`: list — список потоков
  * `is_film`, `is_serial`: bool — флаги типа видео
* **Возвращает**: None
* Добавляет запись в таблицу `Files`, если такой ещё нет

### `def save_data_if_comment(self, data, streams, is_film, is_serial)`

* **Параметры**:

  * `data`: dict
  * `streams`: list
  * `is_film`, `is_serial`: bool
* **Возвращает**: None
* Аналогично `save_file_data`, но устанавливает `IsConverted=True`

### `def interrupted_program(self, current_time, file_id)`

* **Параметры**:

  * `current_time`: datetime
  * `file_id`: int
* **Возвращает**: None
* Обновляет статус задачи как "прерванная" с установкой времени окончания

### `def select_data(self)`

* **Параметры**: нет
* **Возвращает**: list — все записи из таблицы `Files`

### `def select_single_data(self, filename)`

* **Параметры**: `filename` (str)
* **Возвращает**: list — запись из таблицы `Files` по имени файла

### `def select_directory_data(self, directory)`

* **Параметры**: `directory` (str)
* **Возвращает**: list — записи `Files`, чьи имена начинаются с указанного пути

### `def update_status_of_conversion(self, file_id, status, current_time)`

* **Параметры**:

  * `file_id`: int
  * `status`: str
  * `current_time`: datetime
* **Возвращает**: None
* Вставляет новую задачу конвертации в `ConversionTasks`

### `def update_status_first_check(self, file_id, status, start_time, end_time)`

* **Параметры**:

  * `file_id`: int
  * `status`: str
  * `start_time`, `end_time`: datetime
* **Возвращает**: None
* Вставляет задачу с началом и концом выполнения

### `def update_isconverted_after_fail_check(self, file_id, is_converted)`

* **Параметры**:

  * `file_id`: int
  * `is_converted`: bool
* **Возвращает**: None
* Обновляет флаг `IsConverted` в `Files`

### `def update_status_ending_conversion(self, status, current_time, check_result, file_id)`

* **Параметры**:

  * `status`: str
  * `current_time`: datetime
  * `check_result`: str
  * `file_id`: int
* **Возвращает**: None
* Обновляет статус, время окончания и проверку целостности

### `def update_files_table(self, output_file, is_conveted, nb_streams, size, bitrate, streams, file_id)`

* **Параметры**:

  * `output_file`: str
  * `is_conveted`: bool
  * `nb_streams`: int
  * `size`: int
  * `bitrate`: int
  * `streams`: str (JSON)
  * `file_id`: int
* **Возвращает**: None
* Обновляет запись `Files` новыми параметрами видео

### `def update_of_checking_integrity(self, status, current_time, check_result, file_id)`

* **Параметры**:

  * `status`: str
  * `current_time`: datetime
  * `check_result`: str
  * `file_id`: int
* **Возвращает**: None
* То же, что `update_status_ending_conversion` — дублирование

### `def update_url_file(self, filename, output_file)`

* **Параметры**:

  * `filename`: str
  * `output_file`: str
* **Возвращает**: None
* Обновляет URL в таблице `video_series_files` MariaDB

### `def global_interrupted_query(self, current_time)`

* **Параметры**: `current_time` (datetime)
* **Возвращает**: list — записи с задачами, которые были в статусе `converting`
* Массово обновляет задачи со статусом `converting` на `interrupted`

---

## 📄 `single_handler.py`

Файл реализует класс `ConvertTask`, который отвечает за конвертацию видеофайлов, проверку целостности и обновление соответствующих записей в базе данных.

### `class ConvertTask`

**Инициализация:**

```python
ConvertTask(config: dict)
```

* **config**: словарь с конфигурацией проекта
* Инициализирует:

  * пути к временным и рабочим файлам
  * подключение к базе данных
  * параметры ffmpeg
  * объект `Get_Info`

---

### `def signal_handler(self, signum, frame)`

* **Параметры**:

  * `signum`: int — сигнал
  * `frame`: frame — текущий стек вызовов
* **Возвращает**: None
* Устанавливает флаг `self.interrupted = True`

### `def set_pdeathsig(self)`

* **Параметры**: нет
* **Возвращает**: None
* Устанавливает сигнал родительского завершения процесса (PR\_SET\_PDEATHSIG)

### `def create_pid_file(self)`

* **Параметры**: нет
* **Возвращает**: str — путь к PID-файлу
* Создаёт пустой PID-файл, если не существует

### `def clear_pid_file(self, file_path)`

* **Параметры**: `file_path` (str)
* **Возвращает**: None
* Очищает содержимое PID-файла

### `def check_integrity(self, output_file)`

* **Параметры**: `output_file` (str)
* **Возвращает**: tuple\[bool, str] — статус и результат проверки
* Запускает ffmpeg-проверку на целостность файла

### `def run_ffmpeg(self, input_file, output_file, bitrate, audio_stream_index)`

* **Параметры**:

  * `input_file`: str
  * `output_file`: str
  * `bitrate`: str
  * `audio_stream_index`: int
* **Возвращает**: tuple\[bool, str] — статус выполнения и результат
* Выполняет конвертацию видео через ffmpeg

### `def get_data(self, file_data)`

* **Параметры**: `file_data` (str) — имя файла
* **Возвращает**: list — список файлов, подлежащих конвертации, с индексами аудиодорожек

### `def convert_files(self, file_data)`

* **Параметры**: `file_data` (str) — имя видеофайла
* **Возвращает**: None
* Основной метод конвертации:

  * Проверка целостности исходного файла
  * Запуск ffmpeg
  * Проверка выходного файла
  * Перемещение, переименование, удаление оригинала
  * Обновление таблиц Files и Ministra

---

## 📄 `dir_handler.py`

Файл `dir_handler.py` реализует расширенную версию `ConvertTask` с поддержкой многопроцессной обработки файлов и функцией параллельной конвертации видео в заданной директории.

### `class ConvertTask`

**Инициализация:**

```python
ConvertTask(config: dict)
```

* **config**: словарь конфигурации
* Инициализирует:

  * пути и конфигурации ffmpeg
  * объект базы данных `Db_query`
  * объект `Get_Info`
  * многопоточный замок `pid_lock`

### `def signal_handler(self, signum, frame)`

* **Параметры**:

  * `signum`: int
  * `frame`: frame
* **Возвращает**: None
* Обрабатывает прерывание по сигналу SIGINT

### `def set_pdeathsig(self)`

* **Параметры**: нет
* **Возвращает**: None
* Устанавливает родительский сигнал завершения процесса (PR\_SET\_PDEATHSIG)

### `def create_pid_file(self)`

* **Параметры**: нет
* **Возвращает**: str — путь к PID-файлу
* Создаёт пустой PID-файл

### `def clear_pid_file(self, file_path)`

* **Параметры**: `file_path` (str)
* **Возвращает**: None
* Очищает PID-файл

### `def check_integrity(self, output_file)`

* **Параметры**: `output_file` (str)
* **Возвращает**: tuple\[bool, str] — результат проверки
* Проверка целостности видео через ffmpeg

### `def run_ffmpeg(self, input_file, output_file, bitrate, audio_stream_index)`

* **Параметры**:

  * `input_file`: str
  * `output_file`: str
  * `bitrate`: str
  * `audio_stream_index`: int
* **Возвращает**: tuple\[bool, str] — результат конвертации
* Запускает ffmpeg-процесс с заданными параметрами

### `def get_data(self, file_data)`

* **Параметры**: `file_data` (str) — путь к директории
* **Возвращает**: list — список файлов с параметрами для обработки

### `def convert_files(self, file_id, IsFilm, filename, selected_index)`

* **Параметры**:

  * `file_id`: int
  * `IsFilm`: bool
  * `filename`: str
  * `selected_index`: int
* **Возвращает**: None
* Конвертирует один файл, проводит проверку до/после, обновляет БД и удаляет исходник

### `def parallel_convert(self, directory)`

* **Параметры**: `directory` (str)
* **Возвращает**: None
* Разбивает список файлов на группы по 2 и обрабатывает их параллельно с помощью `multiprocessing.Pool`
* Обрабатывает прерывания, чистит временные директории, обновляет статусы задач

---

## 📄 `server_handler.py`

Файл `server_handler.py` реализует класс `ConvertTask` для серверной обработки видеофайлов. Отличается поддержкой внешнего флага `stop_event`, позволяющего безопасно прервать выполнение.

### `class ConvertTask`

**Инициализация:**

```python
ConvertTask(config: dict, stop_event: threading.Event)
```

* **config**: dict — конфигурационные параметры
* **stop\_event**: threading.Event — флаг прерывания процесса извне

### `def create_pid_file(self)`

* **Параметры**: нет
* **Возвращает**: str — путь к созданному PID-файлу
* Создаёт пустой PID-файл, если не существует

### `def clear_pid_file(self, file_path)`

* **Параметры**: `file_path`: str
* **Возвращает**: None
* Очищает содержимое файла PID

### `def check_integrity(self, output_file)`

* **Параметры**: `output_file`: str
* **Возвращает**: tuple(bool, str)
* Выполняет ffmpeg-проверку целостности, логирует результат, управляется `stop_event`

### `def run_ffmpeg(self, input_file, output_file, bitrate, audio_stream_index)`

* **Параметры**:

  * `input_file`: str
  * `output_file`: str
  * `bitrate`: str
  * `audio_stream_index`: int
* **Возвращает**: tuple(bool, str)
* Выполняет ffmpeg-конвертацию файла, управляется через `stop_event`

### `def get_data(self, file_data)`

* **Параметры**: `file_data`: str — путь к файлу
* **Возвращает**: list\[list] — метаданные, флаг фильма, имя, индекс аудио
* Получает список подходящих файлов из базы и определяет подходящую аудиодорожку

### `def convert_files(self, file_data)`

* **Параметры**: `file_data`: str — имя файла
* **Возвращает**: None
* Полный цикл обработки файла:

  * Проверка на повреждение до
  * Конвертация через ffmpeg
  * Повторная проверка результата
  * Обновление таблиц `Files`, `ConversionTasks` и `Ministra`
  * Очистка временных файлов даже в случае ошибки
  * Реагирует на `stop_event` для безопасного выхода

---


