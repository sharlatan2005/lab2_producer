from fastapi import FastAPI, HTTPException, Request
import logging
import traceback
import sys
from config import SOCKET_HOST, SOCKET_PORT
from producer_socket import SQLiteSocketServer

from config import RABBITMQ_USER, RABBITMQ_PASS, RABBITMQ_HOST, QUEUE_NAME
from producer_rabbitmq import SQLiteToRabbitMQ

from config import SQLITE_PATH, SQLITE_TABLE_NAME

from config import TRANSPORT

import threading
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Вывод в консоль
        logging.FileHandler('app.log')      # Сохранение в файл
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post('/send_data_to_normalize')
def normalize(request: Request):
    try:
        logger.info(f"Received request from {request.client.host}")
        logger.info(f"TRANSPORT mode: {TRANSPORT}")
        
        if TRANSPORT == 'rabbitmq':
            logger.info("Initializing RabbitMQ transfer...")
            transfer = SQLiteToRabbitMQ(
                db_path=SQLITE_PATH,
                queue_name=QUEUE_NAME,
                rabbitmq_host=RABBITMQ_HOST,
                rabbitmq_user=RABBITMQ_USER,
                rabbitmq_pass=RABBITMQ_PASS
            )
            logger.info("RabbitMQ client created, sending data...")
            transfer.send_data(SQLITE_TABLE_NAME)
            transfer.close()
            logger.info("Data sent successfully via RabbitMQ")
            
        elif TRANSPORT == 'socket':
            logger.info("Starting socket server...")
            global socket_server, server_thread
            
            if socket_server and socket_server._running:
                logger.warning("Socket server already running")
                raise HTTPException(status_code=400, detail="Server already running")
            
            socket_server = SQLiteSocketServer(
                db_name=SQLITE_PATH,
                table_name=SQLITE_TABLE_NAME,
                host=SOCKET_HOST,
                port=SOCKET_PORT
            )
            
            server_thread = threading.Thread(target=socket_server.start, daemon=True)
            server_thread.start()
            logger.info(f"Socket server started on {SOCKET_HOST}:{SOCKET_PORT}")
            
            return {"status": "Socket server started"}
            
    except HTTPException:
        raise
    except Exception as e:
        # Детальное логирование ошибки
        logger.error(f"ERROR in normalize endpoint: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        
        # Возвращаем детальную ошибку (только для отладки!)
        raise HTTPException(
            status_code=500, 
            detail={
                "error": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc() if TRANSPORT == 'socket' else None
            }
        )
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)