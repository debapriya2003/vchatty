# ============================================
# FILE 1: signaling_server.py
# Run this FIRST: python signaling_server.py
# ============================================
"""
WebSocket Signaling Server for WebRTC Video Calling
This server coordinates connection between peers
"""

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store connected clients
clients = {}
rooms = {}

async def handle_client(websocket, path):
    client_id = None
    room_id = None
    
    try:
        logger.info(f"New connection from {websocket.remote_address}")
        
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type')
                
                if msg_type == 'join':
                    # Client joining a room
                    client_id = data['client_id']
                    room_id = data['room_id']
                    
                    clients[client_id] = {
                        'ws': websocket,
                        'room_id': room_id,
                        'name': data.get('name', 'Anonymous')
                    }
                    
                    if room_id not in rooms:
                        rooms[room_id] = set()
                    rooms[room_id].add(client_id)
                    
                    logger.info(f"Client {client_id} joined room {room_id}")
                    
                    # Notify all other clients in the room
                    for other_id in rooms[room_id]:
                        if other_id != client_id and other_id in clients:
                            await clients[other_id]['ws'].send(json.dumps({
                                'type': 'peer_joined',
                                'peer_id': client_id,
                                'peer_name': data.get('name', 'Anonymous')
                            }))
                    
                    # Send list of existing peers to new client
                    existing_peers = [
                        {'id': pid, 'name': clients[pid]['name']} 
                        for pid in rooms[room_id] 
                        if pid != client_id and pid in clients
                    ]
                    
                    await websocket.send(json.dumps({
                        'type': 'room_joined',
                        'peers': existing_peers
                    }))
                
                elif msg_type in ['offer', 'answer', 'ice_candidate']:
                    # Forward WebRTC signaling data to target peer
                    target_id = data.get('target')
                    
                    if target_id and target_id in clients:
                        data['from'] = client_id
                        await clients[target_id]['ws'].send(json.dumps(data))
                        logger.info(f"Forwarded {msg_type} from {client_id} to {target_id}")
                
                elif msg_type == 'leave':
                    # Client leaving room
                    if room_id and room_id in rooms:
                        rooms[room_id].discard(client_id)
                        
                        # Notify others
                        for other_id in rooms[room_id]:
                            if other_id in clients:
                                await clients[other_id]['ws'].send(json.dumps({
                                    'type': 'peer_left',
                                    'peer_id': client_id
                                }))
                        
                        if not rooms[room_id]:
                            del rooms[room_id]
                    
                    logger.info(f"Client {client_id} left room {room_id}")
            
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
            except Exception as e:
                logger.error(f"Error handling message: {e}")
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed for {client_id}")
    
    finally:
        # Cleanup on disconnect
        if client_id:
            if client_id in clients:
                del clients[client_id]
            
            if room_id and room_id in rooms:
                rooms[room_id].discard(client_id)
                
                # Notify others about disconnect
                for other_id in rooms[room_id]:
                    if other_id in clients:
                        try:
                            await clients[other_id]['ws'].send(json.dumps({
                                'type': 'peer_left',
                                'peer_id': client_id
                            }))
                        except:
                            pass
                
                if not rooms[room_id]:
                    del rooms[room_id]
            
            logger.info(f"Cleaned up client {client_id}")

async def main():
    logger.info("Starting WebSocket signaling server on ws://localhost:8765")
    async with websockets.serve(handle_client, "localhost", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
