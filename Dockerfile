FROM python:3.9-slim

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for PyQt5, OpenCV, and VNC
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxcb-xinerama0 \
    libxkbcommon-x11-0 \
    libxkbcommon0 \
    libdbus-1-3 \
    libpulse-mainloop-glib0 \
    procps \
    libxcb1 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-cursor0 \
    libxcb-util1 \
    libxcb-glx0 \
    libfontconfig1 \
    libx11-xcb1 \
    x11vnc \
    xvfb \
    novnc \
    supervisor \
    fluxbox \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Chinese fonts separately to improve build stability
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

# Install GStreamer, audio support and ffmpeg for audio playback
RUN apt-get update && apt-get install -y --no-install-recommends \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-tools \
    gstreamer1.0-alsa \
    libgstreamer1.0-0 \
    pulseaudio \
    alsa-utils \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set up environment variables for display and OpenGL software rendering
ENV DISPLAY=:0
ENV RESOLUTION=1920x1080
ENV LIBGL_ALWAYS_SOFTWARE=1
ENV MESA_GL_VERSION_OVERRIDE=3.3
ENV QT_X11_NO_MITSHM=1

# Create app directory
WORKDIR /app

# Copy requirements first to cache dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Copy application code
COPY . .

# Store default data files in /app/data_default (survives volume mount)
# At runtime, these will be copied to /app/data if that directory is empty
RUN cp -r /app/data /app/data_default && \
    echo "Default data files stored in /app/data_default" && \
    ls -la /app/data_default/

# Convert milestone coin sound effect if WAV exists  
RUN if [ -f /app/assets/milestone_coin.wav ]; then \
        ffmpeg -i /app/assets/milestone_coin.wav -codec:a libmp3lame -qscale:a 2 -y /app/assets/milestone.mp3 && \
        echo "✓ Converted milestone coin sound to MP3"; \
    fi

# Setup VNC and Supervisor
RUN mkdir -p /root/.vnc \
    && echo "password" | x11vnc -storepasswd -stdin /root/.vnc/passwd \
    && chmod 600 /root/.vnc/passwd

# Create supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Configure Fluxbox to use Chinese font
RUN mkdir -p /root/.fluxbox && \
    echo '[style] (WenQuanYi Zen Hei)' > /root/.fluxbox/init && \
    echo 'session.styleFile: /usr/share/fluxbox/styles/Makro' >> /root/.fluxbox/init && \
    echo 'session.screen0.toolbar.visible: false' >> /root/.fluxbox/init && \
    echo '*font: WenQuanYi Zen Hei-10' > /root/.fluxbox/overlay && \
    echo 'window.font: WenQuanYi Zen Hei-10' >> /root/.fluxbox/overlay && \
    echo 'menu.title.font: WenQuanYi Zen Hei-10' >> /root/.fluxbox/overlay && \
    echo 'toolbar.clock.font: WenQuanYi Zen Hei-10' >> /root/.fluxbox/overlay

# Create index.html to auto-redirect to VNC interface with auto-connect
RUN echo '<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0; url=vnc.html?autoconnect=true&resize=scale" /></head><body><p>Redirecting to VNC interface...</p></body></html>' > /usr/share/novnc/index.html

# Expose VNC web port
EXPOSE 8080

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
