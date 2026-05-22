#!/bin/bash

# 1. Start X virtual framebuffer (Xvfb) on display :99
echo "Starting Xvfb..."
Xvfb :99 -screen 0 1280x850x24 &
sleep 1

# 2. Start Fluxbox window manager
echo "Starting Fluxbox..."
fluxbox &
sleep 1

# 3. Start VNC server sharing display :99 on port 5900
echo "Starting VNC server..."
x11vnc -display :99 -forever -shared -bg -nopw -rfbport 5900 &
sleep 1

# 4. Start noVNC proxy to map VNC to HTTP port 6080
echo "Starting noVNC..."
websockify --web /usr/share/novnc 6080 localhost:5900 &
sleep 1

# 5. Run the FastAPI application
echo "Starting Automation Engine API..."
exec python apps/automation-engine/api/main.py
