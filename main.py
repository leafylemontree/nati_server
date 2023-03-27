from src import SocketServer

async def listener(s, data):
    return



sv = SocketServer(
            host='localhost',
            port=31000,
            callback=listener,
            verbose=True,  
            sender=True
        )
sv.start()
