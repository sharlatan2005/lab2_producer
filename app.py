from fastapi import FastAPI, HTTPException

from config import SOCKET_HOST, SOCKET_PORT
from producer_socket import SQLiteSocketServer

from config import RABBITMQ_USER, RABBITMQ_PASS, RABBITMQ_HOST, QUEUE_NAME
from producer_rabbitmq import SQLiteToRabbitMQ

from config import SQLITE_PATH, SQLITE_TABLE_NAME

from config import TRANSPORT

import threading

app = FastAPI()

socket_server = None
server_thread = None

@app.post('/send_data_to_normalize')
def normalize():
    try:
        if TRANSPORT == 'rabbitmq':
            transfer = SQLiteToRabbitMQ(
                db_path=SQLITE_PATH,
                queue_name=QUEUE_NAME,
                rabbitmq_host=RABBITMQ_HOST,
                rabbitmq_user=RABBITMQ_USER,
                rabbitmq_pass=RABBITMQ_PASS
            )
            transfer.send_data(SQLITE_TABLE_NAME)
                
            transfer.close()
        elif TRANSPORT == 'socket':
            global socket_server, server_thread
            
            if socket_server and socket_server._running:
                raise HTTPException(status_code=400, detail="Server already running")
            
            socket_server = SQLiteSocketServer(
                db_name=SQLITE_PATH,
                table_name=SQLITE_TABLE_NAME,
                host=SOCKET_HOST,
                port=SOCKET_PORT
            )
            
            server_thread = threading.Thread(target=socket_server.start, daemon=True)
            server_thread.start()
            
            return {"status": "Socket server started"}
    except Exception as e:
        print(f'{e}')
        raise HTTPException(status_code=500, detail=f"Normalization failed: {e}")
        raise e

@app.post('/stop_socket_server')
def stop_socket_server():
    if not socket_server or not socket_server._running:
        raise HTTPException(status_code=400, detail="Server not running")
    
    socket_server.stop()
    return {"status": "Socket server stopped"}

@app.get('/server_status')
def get_server_status():
    return {
        "is_running": socket_server._running if socket_server else False
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
    