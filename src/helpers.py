import asyncio
import sys
import time
import random
import json

async def ainput(string: str):
    await asyncio.get_event_loop().run_in_executor(
            None, lambda s=string: sys.stdout.write(s+' '))
    return await asyncio.get_event_loop().run_in_executor(
            None, sys.stdin.readline)

def generate_signature(text, dtype=1, destinatary=-1, nodeId=None):
    data = {
        'dtype'         : dtype,
        'timestamp'     : int(time.time() * 1000),
        'messageId'     : f'92{int(time.time()) ^ int(random.randint(0,0xFFFFFFFF))}',
        'content'       : { 'message' : text },
        'address'       : '0.0.0.0',
        'instance'      : -1,
        'origin'        : -1,
        'destinatary'   : destinatary,
        'nodeId'        : nodeId
    }
    return json.dumps(data)
