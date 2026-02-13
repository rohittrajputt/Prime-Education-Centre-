import webview
import threading
import time
import sys
from app import app

def start_flask():
    # Start Flask without debug mode to avoid issues in the background thread
    app.run(port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    # 1. Start Flask in a background thread
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # 2. Wait a moment for server to initialize
    time.sleep(1)

    # 3. Create a webview window
    print("Launching Desktop App...")
    window = webview.create_window(
        'Prime Education Centre', 
        'http://127.0.0.1:5000',
        width=1200,
        height=800,
        resizable=True,
        confirm_close=True
    )

    # 4. Start the GUI
    webview.start()
    sys.exit()
