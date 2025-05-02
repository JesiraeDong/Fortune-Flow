# Fortune Flow - Customer Feedback System

A real-time customer feedback system that analyzes sentiment and dispenses fortune cookies based on feedback.

## Project Structure

```
Fortune-Flow/
├── server/                    # Server-side components (Mac)
│   ├── sub.py                # Main server application
│   ├── publisher.py          # Feedback publisher
│   ├── sentiment.py          # Sentiment analysis module
│   ├── models.py             # Database models
│   ├── requirements.txt      # Server dependencies
│   ├── templates/            # HTML templates
│   └── static/               # Static assets
│
└── raspberry/                # Raspberry Pi components
    ├── servo_controller.py   # Servo motor controller
    └── requirements.txt      # Raspberry Pi dependencies
```

## Setup Instructions

### Server Setup (Mac)

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the server:
```bash
python sub.py
```

### Raspberry Pi Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the servo controller:
```bash
python servo_controller.py
```

## Usage

1. Start the server on your Mac
2. Start the servo controller on your Raspberry Pi
3. Run the publisher script to submit feedback:
```bash
python publisher.py
```

## Dependencies

### Server Dependencies
- Flask
- Flask-SocketIO
- SQLAlchemy
- NLTK
- Plotly
- Flask-CORS

### Raspberry Pi Dependencies
- RPi.GPIO
- python-socketio
- eventlet

## License

MIT License 