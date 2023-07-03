# PGRemote: PostgreSQL Remote Tools

PGRemote — это инструмент для удаленного управления сервером PostgreSQL, основанный на скрипте `db_tools.py`. С его помощью вы можете выполнять резервное копирование и восстановление баз данных, сохранять и извлекать данные на/из удаленного SMB-сервера, создавать, удалять и очищать базы данных.

## Введение

`db_tools.py` — это мощный и простой в использовании скрипт для работы с вашими базами данных PostgreSQL. С его помощью вы можете не только резервировать и восстанавливать базы данных, но и создавать новые базы данных, удалять существующие и очищать их от всех данных. Все операции выполняются удаленно, что обеспечивает максимальное удобство и безопасность при работе с базами данных без прямого доступа к серверу PostgreSQL.

## Установка

Для начала работы с PGRemote необходимо установить следующие зависимости. Зависимости, которые не входят в стандартную библиотеку Python, можно установить с помощью pip:

```bash
pip3 install smbclient
```

## Настройка

В скрипте `db_tools.py` определены следующие переменные, которые можно настроить в соответствии с вашими требованиями:

- `DB_PORT = 5432`: Порт, на котором работает ваш сервер PostgreSQL. Это порт по умолчанию, его можно изменить при необходимости.
- `SHARE_USER`: Имя пользователя для доступа к SMB-серверу.
- `SHARE_PASS`: Пароль для доступа к SMB-серверу.
- `SHARE_HOST`: Имя хоста SMB-сервера.
- `SHARE_NAME`: Имя общего доступа на SMB-сервере.
- `CLIENT_NAME = "db_tools"`: Имя клиента. Это может быть любое имя, которое вы выберете. Оно используется для идентификации источника в логах и сообщениях об ошибках.

Пожалуйста, измените эти переменные в соответствии с конфигурацией вашего сервера перед запуском скрипта.

## Использование

### Синтаксис

```bash
python3 db_tools.py --db_name <name> --db_user <user> --db_pass <pass> --db_host <host> <operation> [--restore_file <file>]
```

### Параметры

- `--db_name <name>`: Имя базы данных.
- `--db_user <user>`: Имя пользователя базы данных.
- `--db_pass <pass>`: Пароль пользователя базы данных.
- `--db_host <host>`: Хост базы данных.
- `<operation>`: Операция для выполнения - `backup` или `restore`.
- `--restore_file <file>`: Файл для восстановления. Обязателен для операции `restore`.

### Примеры использования

Создание резервной копии базы данных:

```bash
python3 db_tools.py --db_name mydatabase --db_user myuser --db_pass mypass --db_host localhost backup
```

Восстановление базы данных из резервной копии:

```bash
python3 db_tools.py --db_name mydatabase --db_user myuser --db_pass mypass --db_host localhost restore --restore_file mydatabase_backup.gz
```

Создание базы данных:

```bash
python3 db_tools.py --db_name mydatabase --db_user myuser --db_pass mypass --db_host localhost create
```

Удаление базы данных:

```bash
python3 db_tools.py --db_name mydatabase --db_user myuser --db_pass mypass --db_host localhost drop
```

Очистка(Truncate) базы данных:

```bash
python3 db_tools.py --db_name mydatabase --db_user myuser --db_pass mypass --db_host localhost clean
```

Очистка(Vacuum) базы данных:

```bash
python3 db_tools.py --db_name mydatabase --db_user myuser --db_pass mypass --db_host localhost vacuum
```

## Логирование

Скрипт `db_tools.py` также поддерживает логирование всех выполняемых операций. Это поможет вам отслеживать все действия, выполняемые скриптом, и устранять возможные ошибки.

Логи сохраняются в файл `db_tools.log`, который автоматически создается в каталоге, где находится скрипт. Файл лога обновляется после каждого выполнения скрипта.

## Об авторе

PGRemote был разработан [Мной](https://github.com/LorD-222).