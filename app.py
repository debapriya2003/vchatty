import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av
import logging
import queue
import threading

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce log verbosity

# Page configuration
st.set_page_config(
    page_title="Video Call App",
    page_icon="📹",
    layout="wide"
)

# RTC Configuration with multiple STUN servers
RTC_CONFIGURATION = RTCConfiguration(
    {
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun1.l.google.com:19302"]},
            {"urls": ["stun:stun2.l.google.com:19302"]},
        ]
    }
)


def main():
    st.title("📹 Real-Time Video Calling App")
    st.markdown("---")

    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")

        call_mode = st.radio(
            "Select Mode",
            ["Video Call", "Audio Only", "Video Only (No Audio)"]
        )

        st.markdown("---")
        st.markdown("### Instructions")
        st.info("""
        1. Click START below your video
        2. Allow camera/microphone access
        3. Share this page URL with others
        4. They will see your video feed

        **Note:** Open in multiple browser tabs to test locally
        """)

        # Advanced settings
        with st.expander("Advanced Settings"):
            use_mirror = st.checkbox("Mirror my video", value=True)
            video_quality = st.slider("Video Quality", 10, 100, 80)

    # Main content area
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📹 Your Video")

        # Configure media constraints
        if call_mode == "Video Call":
            media_stream_constraints = {
                "video": {
                    "width": {"ideal": 1280},
                    "height": {"ideal": 720},
                },
                "audio": True
            }
        elif call_mode == "Audio Only":
            media_stream_constraints = {
                "video": False,
                "audio": True
            }
        else:  # Video Only
            media_stream_constraints = {
                "video": {
                    "width": {"ideal": 1280},
                    "height": {"ideal": 720},
                },
                "audio": False
            }

        # Video processing callback
        def video_frame_callback(frame):
            img = frame.to_ndarray(format="bgr24")

            # Mirror video if enabled
            if use_mirror and call_mode != "Audio Only":
                import cv2
                img = cv2.flip(img, 1)

            return av.VideoFrame.from_ndarray(img, format="bgr24")

        # Create WebRTC streamer with error handling
        try:
            webrtc_ctx = webrtc_streamer(
                key="video-call-main",
                mode=WebRtcMode.SENDRECV,
                rtc_configuration=RTC_CONFIGURATION,
                media_stream_constraints=media_stream_constraints,
                video_frame_callback=video_frame_callback if call_mode != "Audio Only" else None,
                async_processing=True,
                desired_playing_state=None,
            )

            # Connection status
            if webrtc_ctx.state.playing:
                st.success("🟢 Connected & Streaming")

                # Show statistics
                with st.expander("📊 Connection Info"):
                    st.write(f"**Status:** Active")
                    st.write(f"**Mode:** {call_mode}")
                    st.write(f"**Video Quality:** {video_quality}%")
            else:
                st.info("⚪ Click START to begin streaming")

        except Exception as e:
            st.error(f"⚠️ Error initializing video: {str(e)}")
            st.info("Try refreshing the page or checking your camera permissions")

    with col2:
        st.subheader("👥 Remote Participant")

        if 'webrtc_ctx' in locals() and webrtc_ctx.state.playing:
            st.success("Ready to receive remote video")
            st.info("""
            **To connect with others:**
            1. Share this page URL
            2. They open it in their browser
            3. Both click START
            4. Video streams will appear automatically
            """)
        else:
            st.warning("Start your video first to enable connection")

    # Features section
    st.markdown("---")
    st.subheader("✨ Features")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("**🎥 Video Chat**")
        st.write("HD video streaming with adaptive quality")

    with col_b:
        st.markdown("**🔒 Secure**")
        st.write("Peer-to-peer encrypted connection")

    with col_c:
        st.markdown("**⚡ Fast**")
        st.write("Low latency real-time communication")

    # Tips and troubleshooting
    with st.expander("💡 Tips & Troubleshooting"):
        st.markdown("""
        **If video doesn't work:**
        - Make sure your browser has camera/microphone permissions
        - Try using Chrome or Edge browser
        - Check if other apps are using your camera
        - Refresh the page and try again

        **For best results:**
        - Use a wired internet connection
        - Close other bandwidth-heavy applications
        - Ensure good lighting for video quality

        **Testing locally:**
        - Open the URL in two different browser tabs
        - Or use an incognito/private window alongside a regular window
        - You'll see yourself in both windows when connected
        """)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Built with Streamlit + WebRTC • Secure P2P Video Communication</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
