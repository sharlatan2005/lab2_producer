import sqlite3
import socket
import json
import threading

class SQLiteSocketServer:
    def __init__(self, db_name, table_name, host, port):
        self.db_name = db_name
        self.table_name = table_name
        self.host = host
        self.port = port
        self._running = False
        self.server_socket = None

    def get_table_data(self, table_name):
        """Извлекает данные из указанной таблицы SQLite"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row  # Для доступа к столбцам по имени
            cursor = conn.cursor()
            
            # Проверяем существование таблицы
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                raise ValueError(f"Table '{table_name}' does not exist")
            
            # Получаем данные из таблицы
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Конвертируем строки в словари
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            raise Exception(f"Database error: {str(e)}")
        finally:
            if conn:
                conn.close()

    def start(self):
        """Запускает сервер в фоновом режиме"""
        self._running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1)  # Таймаут для периодической проверки флага

        print(f"Socket server started on {self.host}:{self.port}")
        
        while self._running:
            try:
                client_sock, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_sock, addr)).start()
            except socket.timeout:
                continue
            except OSError:
                break  # Сокет был закрыт

    def handle_client(self, client_sock, addr):
        """Обрабатывает одного клиента"""
        try:

            data = self.get_table_data(self.table_name)
            
            for row in data:
                self.send_row(client_sock, row)
                
            client_sock.send(b'END_OF_TRANSMISSION\n')
            
        except Exception as e:
            error_msg = f"ERROR: {str(e)}".encode('utf-8')
            client_sock.send(error_msg + b'\n')
        finally:
            client_sock.close()

    def send_row(self, sock, row):
        """Отправляет одну строку с проверкой типов"""
        try:
            # Преобразуем все числа в int (если возможно)
            processed_row = {
                k: int(v) if isinstance(v, str) and v.isdigit() else v
                for k, v in row.items()
            }
            row_json = json.dumps(processed_row) + '\n'
            sock.send(row_json.encode('utf-8'))
            
            # Ждём подтверждения (таймаут 5 сек)
            sock.settimeout(5.0)
            ack = sock.recv(3)
            if ack != b'ACK':
                raise ConnectionError("Client didn't acknowledge")
                
        except (ValueError, TypeError) as e:
            raise ValueError(f"Data conversion error: {str(e)}")

    def stop(self):
        """Корректно останавливает сервер"""
        self._running = False
        if self.server_socket:
            self.server_socket.close()