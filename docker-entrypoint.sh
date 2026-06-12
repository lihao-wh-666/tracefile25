#!/bin/bash
set -e

echo "[Entrypoint] Starting Platform Jumper - Environment: ${APP_ENV:-unknown}"

VNC_PORT=${VNC_PORT:-5900}
VNC_PASSWORD=${VNC_PASSWORD:-}
DISPLAY_NUM=${DISPLAY_NUM:-99}
export DISPLAY=:${DISPLAY_NUM}

start_xvfb() {
    echo "[Entrypoint] Starting Xvfb on display :${DISPLAY_NUM} (${SCREEN_WIDTH}x${SCREEN_HEIGHT}x24)"
    Xvfb ${DISPLAY} -screen 0 ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x24 \
        -ac +extension GLX +render -noreset > /tmp/xvfb.log 2>&1 &
    XVFB_PID=$!
    sleep 1
    if ! kill -0 $XVFB_PID 2>/dev/null; then
        echo "[Entrypoint][ERROR] Xvfb failed to start"
        cat /tmp/xvfb.log
        exit 1
    fi
    echo "[Entrypoint] Xvfb started (PID: $XVFB_PID)"
}

start_vnc() {
    if [ "${ENABLE_VNC:-false}" = "true" ] || [ "${ENABLE_VNC}" = "1" ]; then
        echo "[Entrypoint] Starting VNC server on port ${VNC_PORT}"
        if [ -n "$VNC_PASSWORD" ]; then
            mkdir -p ~/.vnc
            x11vnc -storepasswd "$VNC_PASSWORD" ~/.vnc/passwd > /dev/null 2>&1
            x11vnc -display ${DISPLAY} -forever -shared -rfbport ${VNC_PORT} \
                -rfbauth ~/.vnc/passwd -bg -o /tmp/vnc.log
        else
            echo "[Entrypoint][WARNING] VNC started without password"
            x11vnc -display ${DISPLAY} -forever -shared -rfbport ${VNC_PORT} \
                -bg -o /tmp/vnc.log
        fi
        sleep 1
        echo "[Entrypoint] VNC server started"
    fi
}

start_fluxbox() {
    if [ "${ENABLE_WM:-false}" = "true" ]; then
        echo "[Entrypoint] Starting Fluxbox window manager"
        fluxbox > /tmp/fluxbox.log 2>&1 &
        sleep 1
        echo "[Entrypoint] Fluxbox started"
    fi
}

handle_signal() {
    echo "[Entrypoint] Received shutdown signal, cleaning up..."
    kill -TERM $APP_PID 2>/dev/null || true
    wait $APP_PID 2>/dev/null
    echo "[Entrypoint] Shutdown complete"
    exit 0
}

trap handle_signal SIGTERM SIGINT

if [ "${APP_ENV}" = "testing" ]; then
    echo "[Entrypoint] Testing mode - running health check simulation"
    exec "$@"
fi

start_xvfb
start_vnc
start_fluxbox

echo "[Entrypoint] Launching application: $*"
"$@" &
APP_PID=$!

wait $APP_PID
APP_EXIT_CODE=$?

echo "[Entrypoint] Application exited with code: $APP_EXIT_CODE"
exit $APP_EXIT_CODE
