import socketio
import time
from datetime import datetime
import logging
import subprocess
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Socket.IO client
sio = socketio.Client()

def print_message(message):
    """Print a message directly to USB printer"""
    try:
        # Create a temporary file with the message
        temp_file = "/tmp/print_message.txt"
        with open(temp_file, "w", encoding='utf-8') as f:
            f.write("\x1B\x40")  # Initialize printer
            f.write("??????????????????????????????\n")
            f.write("?     Fortune Cookie        ?\n")
            f.write("??????????????????????????????\n\n")
            f.write(f"{message}\n\n")
            f.write("????????????????????????????\n")
            f.write(f"Printed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("????????????????????????????\n\n\n\n")
            f.write("\x0C")  # Form feed
        
        # Print using direct USB command
        result = subprocess.run(['sudo', 'cp', temp_file, '/dev/bus/usb/001/003'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("? Message printed successfully")
            return True
        else:
            logger.error(f"? Print failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"? Print error: {str(e)}")
        return False

@sio.event
def connect():
    logger.info("? Connected to server!")

@sio.event
def disconnect():
    logger.info("? Disconnected from server")

@sio.on('feedback_processed')
def handle_feedback(data):
    try:
        feedback = data.get('feedback', {})
        text = feedback.get('text', '')
        sentiment = feedback.get('sentiment', '')
        tip = feedback.get('suggested_tip', '')
        cookie = feedback.get('cookie_message', '')
        
        message = f"Feedback: {text}\nSentiment: {sentiment}\n{tip}\n{cookie}"
        print_message(message)
    except Exception as e:
        logger.error(f"? Error: {str(e)}")

def main():
    try:
        # Connect to server
        server_url = 'http://10.197.135.18:5001'
        logger.info(f"Connecting to {server_url}...")
        sio.connect(server_url)
        
        # Keep running
        while True:
            if not sio.connected:
                logger.info("Reconnecting...")
                sio.connect(server_url)
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == '__main__':
    main() 
