# 📹 Real-Time Video Calling App

A peer-to-peer video calling application built with Streamlit and WebRTC. Features HD video streaming, audio communication, and a user-friendly interface.

## ✨ Features

- **Real-time video and audio streaming** using WebRTC technology
- **Multiple modes**: Video call, audio only, or video without audio
- **Peer-to-peer connection** for secure, direct communication
- **HD video quality** with adjustable settings
- **Mirror video option** for better user experience
- **Low latency** real-time communication
- **Browser-based** - no installation required for end users

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Webcam and microphone
- Modern web browser (Chrome, Edge, or Firefox recommended)

### Installation

1. Clone or download this repository

2. Create a virtual environment (recommended):
```bash
python -m venv .venv
```

3. Activate the virtual environment:
   - **Windows**:
     ```bash
     .venv\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     source .venv/bin/activate
     ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the App

1. Start the Streamlit server:
```bash
streamlit run app.py
```

2. The app will open in your default browser at `http://localhost:8501`

3. Click the **START** button to begin streaming

4. Allow camera and microphone permissions when prompted

## 🎯 How to Use

### For Video Calls

1. Open the app in your browser
2. Click **START** to begin your video stream
3. Share the URL with others you want to call
4. They open the same URL in their browser
5. Both parties will see each other's video feeds

### Testing Locally

To test the app by yourself:
- Open the app URL in two different browser tabs, OR
- Use one normal window and one incognito/private window
- Click START in both windows
- You'll see yourself in both windows when connected

### Available Modes

- **Video Call**: Full video and audio streaming
- **Audio Only**: Voice call without video
- **Video Only (No Audio)**: Video streaming without audio

## 🔧 Configuration

### Video Settings

Adjust settings in the sidebar:
- **Mirror my video**: Flip your video horizontally
- **Video Quality**: Adjust quality from 10% to 100%

### Advanced Options

The app uses Google's STUN servers by default for NAT traversal. You can modify the RTC configuration in `app.py` if needed.

## 🐛 Troubleshooting

### Video not working?

- Ensure your browser has camera/microphone permissions
- Try using Chrome or Edge browser (best WebRTC support)
- Check if other applications are using your camera
- Refresh the page and try again

### Connection issues?

- Use a wired internet connection for better stability
- Close bandwidth-heavy applications
- Check your firewall settings

### Windows-specific issues?

If you see asyncio errors in the console, they're usually non-fatal. The app should still work. If problems persist:
- Try using a different browser
- Update your dependencies: `pip install --upgrade -r requirements.txt`

## 📦 Dependencies

Main packages used:
- **Streamlit**: Web application framework
- **streamlit-webrtc**: WebRTC integration for Streamlit
- **aiortc**: Python WebRTC implementation
- **PyAV**: Audio/video processing
- **OpenCV**: Image processing

See `requirements.txt` for the complete list.

## 🔒 Security & Privacy

- All video/audio streams use **peer-to-peer connections**
- Data is **encrypted** using WebRTC's built-in encryption
- No video or audio is stored on any server
- STUN servers are only used for connection establishment

## 🌐 Browser Compatibility

| Browser | Support |
|---------|---------|
| Chrome  | ✅ Excellent |
| Edge    | ✅ Excellent |
| Firefox | ✅ Good |
| Safari  | ⚠️ Limited |
| IE      | ❌ Not supported |

## 📝 License

This project is open source and available for personal and commercial use.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 💡 Future Enhancements

Potential features to add:
- Screen sharing capability
- Recording functionality
- Text chat alongside video
- Virtual backgrounds
- Multiple participants support
- Connection quality indicators

## 📧 Support

If you encounter any issues or have questions, please check the troubleshooting section above or open an issue.

---

Built with ❤️ using Streamlit and WebRTC
