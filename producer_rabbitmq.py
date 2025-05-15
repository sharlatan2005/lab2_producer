import sqlite3
import pika
import json
import time
import ssl

class SQLiteToRabbitMQ:
    def __init__(self, db_path, queue_name, rabbitmq_host='localhost', 
                 rabbitmq_user='guest', rabbitmq_pass='guest'):
        self.db_path = db_path
        self.queue_name = queue_name
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_user = rabbitmq_user
        self.rabbitmq_pass = rabbitmq_pass 

        self.ssl_context = ssl.create_default_context(
            cafile="/etc/rabbitmq/certs/server.crt"  # Используем серверный сертификат как CA
        )
        self.ssl_context.check_hostname = False  # Отключаем проверку имени хоста
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED  # Но проверяем сертификат

        # Подключаемся к RabbitMQ
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.rabbitmq_host,
                credentials=pika.PlainCredentials(
                    self.rabbitmq_user, 
                    self.rabbitmq_pass
                ),
                ssl_options=pika.SSLOptions(self.ssl_context)
            )
        )

        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name, durable=True)
        
        # Для проверки доставки
        self.delivered_messages = set()
        self.confirm_delivery = False
        
    def get_table_columns(self, table_name):
        """Получаем список колонок таблицы"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            return [column[1] for column in cursor.fetchall()]
    
    def send_data(self, table_name, batch_size=100):
        """Отправка данных из SQLite в RabbitMQ"""
        columns = self.get_table_columns(table_name)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT * FROM {table_name}")
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                
                for row in rows:
                    message = {col: row[col] for col in columns}
                    msg_id = str(row['id']) if 'id' in columns else str(time.time())
                    
                    self.channel.basic_publish(
                        exchange='',
                        routing_key=self.queue_name,
                        body=json.dumps(message),
                        properties=pika.BasicProperties(
                            message_id=msg_id,
                            delivery_mode=2  # persistent message
                        )
                    )
                    self.delivered_messages.add(msg_id)
                    print(f"Sent message ID: {msg_id}")
        
        print("All data sent to RabbitMQ")
    
    def close(self):
        self.connection.close()