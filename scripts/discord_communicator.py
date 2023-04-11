import json
import socket
import globals
import asyncio

def send_discord_action(action_object):
    try:
        json_data = json.dumps(action_object)
        globals.s.sendall(json_data.encode())
        return "Discord action sent successfully"
    except socket.error as e:
        return f"Error sending action: {str(e)}"
    
    
async def get_discord_action(action_object):
    try:
        json_data = json.dumps(action_object)
        globals.s.sendall(json_data.encode())
        loop = asyncio.get_event_loop()
        response_bytes = await loop.run_in_executor(None, globals.s.recv, 1024)
        response = response_bytes.decode()
        return response
    except socket.error as e:
        return f"Error sending action: {str(e)}"
