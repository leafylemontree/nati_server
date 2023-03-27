import asyncio
import socket
import logging
import asyncio
import json
import dataclasses
import os

from src import objects
from src import helpers


@dataclasses.dataclass
class Message:
    dtype:      int
    timestamp:  int
    messageId:  str
    content:    str
    address:    str
    instance:   int
    destinatary:int
    nodeId:     str

class Connection:
    def __init__(self, connection, address):
        self.connection = connection
        self.address    = address

class Instance:
    def __init__(self, instance, conn, addr):
        self.instance   = instance
        self.conn       = conn
        self.addr       = addr


class SocketServer:

    host        : str
    port        : int
    server      = None
    loop        = None
    maxListen   = int
    verbose     : bool
    connections = None

    def __init__(self, host, port, callback, loop=None, maxListen=1, verbose=True, sender=False):
        self.host       = host
        self.port       = port
        self.callback   = callback
        self.loop       = loop
        self.maxListen  = maxListen
        self.verbose    = verbose
        self.connections= []
        self.instances  = {}
        self.messages   = []
        self.senderEn   = sender
        logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s: %(name)s - [%(levelname)s]: %(message)s'
            )

    def start(self):
        os.system('clear')
        if self.loop is None:
            self.loop = asyncio.new_event_loop()
            self.loop.run_until_complete(self.socket_run())
        else:
            self.loop.create_task(self.socket_run())
        
    def log(self, msg, level='INFO'):
        if not self.verbose: return
        if   level == 'DEBUG'   : logging.debug(str(msg))
        elif level == 'INFO'    : logging.info(str(msg))
        elif level == 'WARN'    : logging.warn(str(msg))
        elif level == 'ERROR'   : logging.error(str(msg))
        elif level == 'CRITIAL' : logging.critical(str(msg))
        return

    async def new_connection(self):
        while True:
            data = await self.loop.sock_accept(self.server)
            self.log(f'Attempting to create a coroutine')
            connection = Connection(*data)
            self.connections.append(connection)
            self.loop.create_task(self.listener(*data))

    async def socket_run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.server:

            try:
                self.server.bind((self.host, self.port))
                self.server.listen(self.maxListen)
                self.server.setblocking(False)
                self.log(f'Socket created at {self.host}:{self.port}')

                if self.senderEn: self.loop.create_task(self.sender())    
                await self.new_connection()

            except Exception as e:
                self.log(f'Socket errored! {e}', level='ERROR')
                
    def instance_config(self, instance, conn, addr):
        s_ins = str(instance)
        self.instances[s_ins] = Instance(instance, conn, addr)

    def new_message(self, data):
        l = len(self.messages)
        if l > 10: self.messages.pop(0)
        self.messages.append(data.messageId)
        return

    async def listener(self, conn, addr):
        self.log(f'Connection with {addr}')
        while True:
            try:
                raw  = await self.loop.sock_recv(conn, 4096)
                if raw == b'': return
                data = self.recv_parser(raw)

                await self.callback(self, data)

                if data.dtype == 5:                 self.instance_config(data.content.instance, conn, addr)
                if data.messageId in self.messages: continue
                if data.dtype in [1, 2, 3, 4]:      await self.send_to(raw)
                self.log(f'{addr}: {data}')
                self.new_message(data)
            except Exception as e:
                self.log(f'Listener errored! {e}', level='ERROR')
            except KeyboardInterrupt:
                for c in self.connections:
                    c.connections.close()
                self.server.close()
        return

    async def send_to(self, raw):
        data = json.loads(raw.decode())

        ins = data['destinatary']
        instances = [str(ins)]
        if ins == -1: instances = self.instances.keys()

        # instance = who asked, origin = who ask now, destinatary = who should answer
        origin = data['destinatary']

        for i in instances:
            data['origin']      = origin
            data['destinatary'] = int(i)
            raw_e               = json.dumps(data)
            await self.loop.sock_sendall(self.instances[i].conn, raw_e.encode())
        return

    def recv_parser(self, raw):
        resp = raw.decode()
        data = objects.SocketResponse(**json.loads(resp))
        content = json.loads(data.content)
        
        if   data.dtype == 0 :      content = objects.SocketInfo(**content)
        elif data.dtype == 1 :      content = objects.SocketRequest(**content)
        elif data.dtype == 2 :      content = objects.SocketChat(**content)
        #elif data.dtype == 3 :      content = objects.SocketRaw(**content)
        elif data.dtype == 4 :      content = objects.SocketJoin(**content)
        elif data.dtype == 5 :      content = objects.SocketConfig(**content)

        data.content = content
        return data

    async def sender(self):
        while True:
            text = await helpers.ainput('>> ')
            try:
                for i,instance in self.instances.items():
                    data = helpers.generate_signature(f'{i}:{text}', dtype=2)
                    try:
                        await self.oop.sock_sendall(instance.conn, data.encode('utf-8'))
                    except Exception as e:
                        self.log(f'Send errored! {instance.addr} {e}', level='Error')

            except Exception as e:
                self.log(f'Sender errored! {e}', level='ERROR')
            except KeyboardInterrupt:
                for c in self.connections:
                    c.connections.close()
                self.server.close()
