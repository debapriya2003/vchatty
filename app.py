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


# ============================================
# FILE 2: app.py (Streamlit Video Call App)
# Run this AFTER starting signaling server: streamlit run app.py
# ============================================
"""
import streamlit as st
import streamlit.components.v1 as components
import uuid

# Page config
st.set_page_config(
    page_title="P2P Video Call",
    page_icon="📹",
    layout="wide"
)

# Generate unique client ID
if 'client_id' not in st.session_state:
    st.session_state.client_id = str(uuid.uuid4())

def main():
    st.title("📹 Peer-to-Peer Video Calling App")
    st.markdown("*With Custom WebSocket Signaling Server*")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Room Settings")
        
        user_name = st.text_input("Your Name", value="User")
        room_id = st.text_input("Room ID", value="room-123")
        
        st.markdown("---")
        st.info(f'''
        **Share this Room ID:** `{room_id}`
        
        Others can join by entering the same Room ID.
        ''')
        
        st.markdown("---")
        st.subheader("🎥 Settings")
        enable_video = st.checkbox("Enable Video", value=True)
        enable_audio = st.checkbox("Enable Audio", value=True)
        
        st.markdown("---")
        server_status = st.empty()
    
    # Check if signaling server is running
    try:
        import websocket
        ws = websocket.create_connection("ws://localhost:8765", timeout=2)
        ws.close()
        server_status.success("✅ Signaling Server: Connected")
    except:
        server_status.error("❌ Signaling Server: Not Running")
        st.error('''
        **Signaling server is not running!**
        
        Please start the signaling server first:
        ```bash
        python signaling_server.py
        ```
        ''')
        st.stop()
    
    # Video call interface
    video_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: #1a1a1a;
                font-family: Arial, sans-serif;
            }}
            #container {{
                padding: 20px;
            }}
            #videos {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }}
            .video-box {{
                position: relative;
                background: #2a2a2a;
                border-radius: 12px;
                overflow: hidden;
                aspect-ratio: 16/9;
            }}
            video {{
                width: 100%;
                height: 100%;
                object-fit: cover;
            }}
            .video-label {{
                position: absolute;
                bottom: 10px;
                left: 10px;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 8px 15px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            #local-video-box {{
                border: 3px solid #00ff00;
            }}
            #controls {{
                display: flex;
                justify-content: center;
                gap: 15px;
                flex-wrap: wrap;
            }}
            button {{
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
            }}
            #join-btn {{
                background: #28a745;
                color: white;
            }}
            #leave-btn {{
                background: #dc3545;
                color: white;
                display: none;
            }}
            .toggle-btn {{
                background: #6c757d;
                color: white;
            }}
            .toggle-btn.active {{
                background: #28a745;
            }}
            button:hover {{
                opacity: 0.9;
                transform: scale(1.05);
            }}
            button:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
                transform: none;
            }}
            #status {{
                text-align: center;
                color: white;
                font-size: 18px;
                margin: 20px 0;
                padding: 15px;
                background: rgba(255,255,255,0.1);
                border-radius: 8px;
            }}
        </style>
    </head>
    <body>
        <div id="container">
            <div id="status">Click "Join Room" to start</div>
            
            <div id="controls">
                <button id="join-btn">🎥 Join Room</button>
                <button id="leave-btn">📞 Leave Room</button>
                <button id="toggle-video" class="toggle-btn active">📹 Video</button>
                <button id="toggle-audio" class="toggle-btn active">🎤 Audio</button>
            </div>
            
            <div id="videos">
                <div id="local-video-box" class="video-box">
                    <video id="local-video" autoplay muted playsinline></video>
                    <div class="video-label">You ({user_name})</div>
                </div>
            </div>
        </div>
        
        <script>
            const CLIENT_ID = "{st.session_state.client_id}";
            const ROOM_ID = "{room_id}";
            const USER_NAME = "{user_name}";
            const WS_URL = "ws://localhost:8765";
            
            let ws = null;
            let localStream = null;
            let peerConnections = {{}};
            
            const configuration = {{
                iceServers: [
                    {{ urls: 'stun:stun.l.google.com:19302' }},
                    {{ urls: 'stun:stun1.l.google.com:19302' }}
                ]
            }};
            
            const joinBtn = document.getElementById('join-btn');
            const leaveBtn = document.getElementById('leave-btn');
            const toggleVideoBtn = document.getElementById('toggle-video');
            const toggleAudioBtn = document.getElementById('toggle-audio');
            const statusDiv = document.getElementById('status');
            const videosDiv = document.getElementById('videos');
            const localVideo = document.getElementById('local-video');
            
            let videoEnabled = {str(enable_video).lower()};
            let audioEnabled = {str(enable_audio).lower()};
            
            // Join room
            joinBtn.onclick = async () => {{
                try {{
                    statusDiv.textContent = 'Getting media devices...';
                    
                    localStream = await navigator.mediaDevices.getUserMedia({{
                        video: videoEnabled,
                        audio: audioEnabled
                    }});
                    
                    localVideo.srcObject = localStream;
                    
                    // Connect to signaling server
                    ws = new WebSocket(WS_URL);
                    
                    ws.onopen = () => {{
                        statusDiv.textContent = 'Connected to signaling server';
                        ws.send(JSON.stringify({{
                            type: 'join',
                            client_id: CLIENT_ID,
                            room_id: ROOM_ID,
                            name: USER_NAME
                        }}));
                    }};
                    
                    ws.onmessage = handleSignalingMessage;
                    
                    ws.onerror = (error) => {{
                        statusDiv.textContent = 'WebSocket error: ' + error;
                    }};
                    
                    ws.onclose = () => {{
                        statusDiv.textContent = 'Disconnected from server';
                    }};
                    
                    joinBtn.style.display = 'none';
                    leaveBtn.style.display = 'inline-block';
                    
                }} catch(error) {{
                    statusDiv.textContent = 'Error: ' + error.message;
                    alert('Failed to access camera/microphone: ' + error.message);
                }}
            }};
            
            // Handle signaling messages
            async function handleSignalingMessage(event) {{
                const data = JSON.parse(event.data);
                
                switch(data.type) {{
                    case 'room_joined':
                        statusDiv.textContent = `In room: ${{ROOM_ID}} | Peers: ${{data.peers.length}}`;
                        
                        // Create peer connections for existing peers
                        for (const peer of data.peers) {{
                            await createPeerConnection(peer.id, peer.name, true);
                        }}
                        break;
                    
                    case 'peer_joined':
                        statusDiv.textContent = `${{data.peer_name}} joined the room`;
                        await createPeerConnection(data.peer_id, data.peer_name, false);
                        break;
                    
                    case 'offer':
                        await handleOffer(data);
                        break;
                    
                    case 'answer':
                        await handleAnswer(data);
                        break;
                    
                    case 'ice_candidate':
                        await handleIceCandidate(data);
                        break;
                    
                    case 'peer_left':
                        handlePeerLeft(data.peer_id);
                        break;
                }}
            }}
            
            // Create peer connection
            async function createPeerConnection(peerId, peerName, createOffer) {{
                const pc = new RTCPeerConnection(configuration);
                peerConnections[peerId] = pc;
                
                // Add local stream tracks
                localStream.getTracks().forEach(track => {{
                    pc.addTrack(track, localStream);
                }});
                
                // Handle incoming tracks
                pc.ontrack = (event) => {{
                    const remoteStream = event.streams[0];
                    addRemoteVideo(peerId, peerName, remoteStream);
                }};
                
                // Handle ICE candidates
                pc.onicecandidate = (event) => {{
                    if (event.candidate) {{
                        ws.send(JSON.stringify({{
                            type: 'ice_candidate',
                            target: peerId,
                            candidate: event.candidate
                        }}));
                    }}
                }};
                
                // Create offer if initiator
                if (createOffer) {{
                    const offer = await pc.createOffer();
                    await pc.setLocalDescription(offer);
                    
                    ws.send(JSON.stringify({{
                        type: 'offer',
                        target: peerId,
                        sdp: offer
                    }}));
                }}
            }}
            
            // Handle offer
            async function handleOffer(data) {{
                const peerId = data.from;
                let pc = peerConnections[peerId];
                
                if (!pc) {{
                    await createPeerConnection(peerId, 'Remote User', false);
                    pc = peerConnections[peerId];
                }}
                
                await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
                const answer = await pc.createAnswer();
                await pc.setLocalDescription(answer);
                
                ws.send(JSON.stringify({{
                    type: 'answer',
                    target: peerId,
                    sdp: answer
                }}));
            }}
            
            // Handle answer
            async function handleAnswer(data) {{
                const pc = peerConnections[data.from];
                if (pc) {{
                    await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
                }}
            }}
            
            // Handle ICE candidate
            async function handleIceCandidate(data) {{
                const pc = peerConnections[data.from];
                if (pc && data.candidate) {{
                    await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
                }}
            }}
            
            // Add remote video
            function addRemoteVideo(peerId, peerName, stream) {{
                let videoBox = document.getElementById(`remote-${peerId}`);
                
                if (!videoBox) {{
                    videoBox = document.createElement('div');
                    videoBox.id = `remote-${peerId}`;
                    videoBox.className = 'video-box';
                    videoBox.innerHTML = `
                        <video autoplay playsinline></video>
                        <div class="video-label">${{peerName}}</div>
                    `;
                    videosDiv.appendChild(videoBox);
                }}
                
                const video = videoBox.querySelector('video');
                video.srcObject = stream;
            }}
            
            // Handle peer left
            function handlePeerLeft(peerId) {{
                if (peerConnections[peerId]) {{
                    peerConnections[peerId].close();
                    delete peerConnections[peerId];
                }}
                
                const videoBox = document.getElementById(`remote-${peerId}`);
                if (videoBox) {{
                    videoBox.remove();
                }}
                
                statusDiv.textContent = 'A peer left the room';
            }}
            
            // Leave room
            leaveBtn.onclick = () => {{
                if (ws) {{
                    ws.send(JSON.stringify({{
                        type: 'leave'
                    }}));
                    ws.close();
                }}
                
                // Close all peer connections
                Object.values(peerConnections).forEach(pc => pc.close());
                peerConnections = {{}};
                
                // Stop local stream
                if (localStream) {{
                    localStream.getTracks().forEach(track => track.stop());
                    localVideo.srcObject = null;
                }}
                
                // Remove remote videos
                document.querySelectorAll('[id^="remote-"]').forEach(el => el.remove());
                
                joinBtn.style.display = 'inline-block';
                leaveBtn.style.display = 'none';
                statusDiv.textContent = 'Left the room';
            }};
            
            // Toggle video
            toggleVideoBtn.onclick = () => {{
                if (localStream) {{
                    const videoTrack = localStream.getVideoTracks()[0];
                    if (videoTrack) {{
                        videoTrack.enabled = !videoTrack.enabled;
                        toggleVideoBtn.classList.toggle('active');
                    }}
                }}
            }};
            
            // Toggle audio
            toggleAudioBtn.onclick = () => {{
                if (localStream) {{
                    const audioTrack = localStream.getAudioTracks()[0];
                    if (audioTrack) {{
                        audioTrack.enabled = !audioTrack.enabled;
                        toggleAudioBtn.classList.toggle('active');
                    }}
                }}
            }};
        </script>
    </body>
    </html>
    '''
    
    components.html(video_html, height=800, scrolling=False)
    
    # Instructions
    st.markdown("---")
    with st.expander("📖 How to Use"):
        st.markdown('''
        ### Setup:
        1. **Start the signaling server** (in a separate terminal):
           ```bash
           python signaling_server.py
           ```
        
        2. **Run the Streamlit app**:
           ```bash
           streamlit run app.py
           ```
        
        3. **Test the video call**:
           - Open the app in two different browser tabs/windows
           - Or share the URL with someone on the same network
           - Both users enter the same Room ID
           - Click "Join Room"
           - You should see each other's video!
        
        ### Features:
        - ✅ Real peer-to-peer video calling
        - ✅ Works on local network
        - ✅ Multiple participants support
        - ✅ Toggle video/audio on/off
        - ✅ No external services needed
        
        ### Troubleshooting:
        - Make sure signaling server is running first
        - Allow camera/microphone permissions
        - Use Chrome or Edge browser
        - Check if port 8765 is available
        ''')

if __name__ == "__main__":
    main()
"""
