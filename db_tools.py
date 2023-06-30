import os
import subprocess
import gzip
import shutil
import argparse
import smbclient
from datetime import datetime
import logging
from pathlib import Path
import shlex


# Константы для операций
BACKUP = 'backup'
RESTORE = 'restore'

# Класс для хранения констант
class Config:
    DB_PORT = 5432
    SHARE_USER = "SHARE_USER"
    SHARE_PASS = "SHARE_PASS"
    SHARE_HOST = "SHARE_HOST"
    SHARE_NAME = "SHARE_NAME"
    CLIENT_NAME = "db_tools" # Укажите имя клиента. Это может быть любое имя.

    # Константы для сообщений об ошибках
    RESTORE_FILE_ERROR = "You must provide a --restore_file for restore operation"
    INVALID_OPERATION_ERROR = f"Invalid operation. Please choose either '{BACKUP}' or '{RESTORE}'"

# Настройка логирования
logging.basicConfig(filename='db_tools.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

# Функция для создания парсера аргументов командной строки
def define_parser():
    parser = argparse.ArgumentParser(description="PostgreSQL backup and restore script")
    parser.add_argument('--db_name', type=str, help="Database name", required=True)
    parser.add_argument('--db_user', type=str, help="Database user", required=True)
    parser.add_argument('--db_pass', type=str, help="Database password", required=True)
    parser.add_argument('--db_host', type=str, help="Database host", required=True)
    parser.add_argument('--db_port', type=int, default=Config.DB_PORT, help="Database port")
    parser.add_argument('--share_user', type=str, default=Config.SHARE_USER, help="Windows share user")
    parser.add_argument('--share_pass', type=str, default=Config.SHARE_PASS, help="Windows share password")
    parser.add_argument('--share_host', type=str, default=Config.SHARE_HOST, help="Windows share host")
    parser.add_argument('--share_name', type=str, default=Config.SHARE_NAME, help="Windows share name")
    parser.add_argument('operation', type=str, choices=[BACKUP, RESTORE], help="Operation: backup or restore")
    parser.add_argument('--restore_file', type=str, help="File to restore from (required for restore operation)")
    return parser

# Функция для парсинга аргументов командной строки
def parse_arguments(parser):
    try:
        return parser.parse_args()
    except Exception as e:
        logging.error(f"Failed to parse command line arguments: {e}")
        exit(1)

# Функция для запуска команды и обработки ошибок
def run_command(command, env=None):
    # Обновляем окружение с добавлением новых переменных, если они предоставлены
    env = {**os.environ, **(env or {})}
    
    try:
        # Разделяем команду на список аргументов
        args = shlex.split(command)
        
        # Запуск процесса с перенаправлением вывода в лог
        process = subprocess.Popen(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        # Если есть вывод, записываем его в лог
        if stdout:
            logging.info(stdout.decode())
        if stderr:
            logging.error(stderr.decode())

        # Если процесс завершился с ошибкой, вызываем исключение
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)

    except subprocess.CalledProcessError as e:
        logging.error(f"Error occurred during executing command: {command}\nError message: {e}")
        exit(1)


# Функция для установления SMB соединения
def create_smb_session(args):
    smbclient.register_session(args.share_host, username=args.share_user, password=args.share_pass)

# Функции для отправки и получения файлов через SMB
def send_file_smb(args, local_file_path, remote_file_path, remote_share_name):
    with open(local_file_path, 'rb') as file_obj:
        with smbclient.open_file(f"\\\\{args.share_host}\\{remote_share_name}\\{remote_file_path}", mode='wb') as remote_file:
            shutil.copyfileobj(file_obj, remote_file)

def get_file_smb(args, local_file_path, remote_file_path, remote_share_name):
    with smbclient.open_file(f"\\\\{args.share_host}\\{remote_share_name}\\{remote_file_path}", mode='rb') as remote_file:
        with open(local_file_path, 'wb') as file_obj:
            shutil.copyfileobj(remote_file, file_obj)


# Функция для создания резервной копии базы данных
def backup_db(args):
    # Создание имени файла резервной копии
    backup_file = Path(f"{args.db_name}_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    backup_file_gz = backup_file.with_suffix('.gz')

    # Формирование команды для pg_dump
    pg_dump_command = f"pg_dump -U {args.db_user} -h {args.db_host} -p {args.db_port} -F c -b -v -f {backup_file} {args.db_name}"

    # Установка пароля для pg_dump и запуск команды
    run_command(pg_dump_command, env={'PGPASSWORD': args.db_pass})

    # Сжатие файла резервной копии с помощью gzip
    with open(backup_file, 'rb') as f_in, gzip.open(backup_file_gz, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

    os.remove(backup_file)

    # Отправка файла резервной копии на удалённый SMB сервер
    smbclient.register_session(args.share_host, username=args.share_user, password=args.share_pass)
    send_file_smb(args, str(backup_file_gz), str(backup_file_gz), args.share_name) # Пути к файлам и имя SMB-шары


# Функция для восстановления базы данных
def restore_db(args):
    # Получение имени файла для восстановления
    restore_file_gz = Path(args.restore_file)
    restore_file = restore_file_gz.with_suffix('')

    # Скачивание файла резервной копии с удалённого SMB сервера
    smbclient.register_session(args.share_host, username=args.share_user, password=args.share_pass)
    get_file_smb(args, str(restore_file_gz), args.restore_file, args.share_name) # Пути к файлам и имя SMB-шары

    # Распаковка файла резервной копии
    with gzip.open(restore_file_gz, 'rb') as f_in, open(restore_file, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

    os.remove(restore_file_gz)

    # Формирование команды для pg_restore и запуск команды
    pg_restore_command = f"pg_restore -U {args.db_user} -h {args.db_host} -p {args.db_port} -F c -d {args.db_name} {restore_file}"
    run_command(pg_restore_command, env={'PGPASSWORD': args.db_pass})

    # Удаление локальной копии файла резервной копии
    os.remove(restore_file)


# Основная функция
def main():
    # Получение аргументов командной строки
    parser = define_parser()
    args = parse_arguments(parser)

    # Выбор операции в зависимости от введенного ключа
    if args.operation.lower() == BACKUP:
        backup_db(args)
    elif args.operation.lower() == RESTORE:
        if args.restore_file is None:
            print(Config.RESTORE_FILE_ERROR)  # Или замените logging.error на print
            logging.error(Config.RESTORE_FILE_ERROR)
            exit(1)
        restore_db(args)
    else:
        logging.error(Config.INVALID_OPERATION_ERROR)

if __name__ == "__main__":
    main()
