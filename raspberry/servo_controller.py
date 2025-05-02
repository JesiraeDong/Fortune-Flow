import RPi.GPIO as GPIO
import socketio
import time
from datetime import datetime

# Configure GPIO
SERVO_PIN = 17  # Use Servo 1 pin on Cricket HAT

# Clean up any existing GPIO setup
GPIO.cleanup()

# Configure GPIO with warnings disabled
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)
servo = GPIO.PWM(SERVO_PIN, 50)  # 50 Hz frequency
servo.start(0)  # Initialize servo position

# Initialize Socket.IO client with proper configuration
sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=1)

def rotate_servo():
    """Rotate servo motor 180 degrees and return to original position"""
    try:
        print("🔄 Rotating servo motor...")
        print(f"Current time: {datetime.now()}")
        
        # Move to 180 degrees (adjusted duty cycle)
        print("Moving to 180 degrees...")
        servo.ChangeDutyCycle(10.0)  # Adjusted from 12.5 to 10.0
        time.sleep(1.5)  # Increased wait time
        
        # Return to 0 degrees (adjusted duty cycle)
        print("Returning to 0 degrees...")
        servo.ChangeDutyCycle(5.0)  # Adjusted from 2.5 to 5.0
        time.sleep(1.5)  # Increased wait time
        
        # Stop the servo
        print("Stopping servo...")
        servo.ChangeDutyCycle(0)
        print("✅ Servo rotation complete")
    except Exception as e:
        print(f"❌ Error controlling servo: {str(e)}")
        print(f"Error occurred at: {datetime.now()}")

@sio.event
def connect():
    print("✅ Connected to server!")
    print(f"Connection time: {datetime.now()}")

@sio.event
def disconnect():
    print("❌ Disconnected from server")
    print(f"Disconnection time: {datetime.now()}")

@sio.event
def connect_error(data):
    print(f"❌ Connection error: {data}")
    print(f"Error time: {datetime.now()}")

@sio.on('rotate_servo')
def handle_rotate_servo(data):
    """Handle servo rotation request from server"""
    print(f"📥 Received rotation request at {datetime.now()}")
    print(f"📥 Rotation request data: {data}")
    rotate_servo()

def main():
    print("🔄 Fortune Cookie Servo Controller")
    print("--------------------------------")
    print(f"Start time: {datetime.now()}")
    
    try:
        # Connect to the Flask-SocketIO server
        # Using the server's IP address
        server_url = 'http://172.28.229.89:5001'
        print(f"🔄 Connecting to server at {server_url}...")
        sio.connect(server_url)
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        if sio.connected:
            sio.disconnect()
        servo.stop()
        GPIO.cleanup()

if __name__ == '__main__':
    main() 