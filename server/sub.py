import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from models import db, Feedback
from sentiment import analyze_sentiment
import plotly.express as px
import pandas as pd
from datetime import datetime
import logging
import plotly.graph_objects as go
from flask_cors import CORS
import socket
import paho.mqtt.client as mqtt

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MQTT Configuration
mqtt_broker = "localhost"
mqtt_port = 1883
mqtt_topic = "feedback/updates"

# MQTT Callback functions
def on_connect(client, userdata, flags, rc):
    logger.info(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(mqtt_topic)

def on_message(client, userdata, msg):
    try:
        logger.info(f"Received MQTT message: {msg.payload.decode()}")
        # Handle MQTT message if needed
    except Exception as e:
        logger.error(f"Error processing MQTT message: {str(e)}")

# Initialize MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Connect to MQTT broker
try:
    client.connect(mqtt_broker, mqtt_port, 60)
    client.loop_start()
    logger.info("Connected to MQTT broker")
except Exception as e:
    logger.error(f"Failed to connect to MQTT broker: {str(e)}")
    logger.info("Continuing without MQTT broker connection")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SocketIO with eventlet and proper CORS settings
socketio = SocketIO(
    app,
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    cors_allowed_origins="*",
    ping_timeout=60,
    ping_interval=25,
    host='0.0.0.0',  # Explicitly bind to all interfaces
    always_connect=True,  # Allow connections from any origin
    transports=['websocket', 'polling']  # Allow both WebSocket and polling
)

# Initialize the database
db.init_app(app)

# Create the database tables
with app.app_context():
    db.create_all()

# Get local IP address
logger.info("Server running on all interfaces (0.0.0.0)")

def create_charts():
    """Create charts for the dashboard using plotly."""
    feedbacks = Feedback.query.order_by(Feedback.timestamp.asc()).all()
    
    if not feedbacks:
        return None, None
    
    # Create DataFrame with proper data types
    df = pd.DataFrame([
        {
            'sentiment': f.sentiment,
            'timestamp': pd.to_datetime(f.timestamp),
            'value': 1 if f.sentiment == 'Positive' else (-1 if f.sentiment == 'Negative' else 0),
            'text': f.text
        }
        for f in feedbacks
    ])
    
    # Print debug information for sentiment values
    print("Sentiment values over time:", df[['timestamp', 'sentiment', 'value']].to_dict('records'))
    
    # Create pie chart with better layout
    sentiment_counts = df['sentiment'].value_counts()
    
    # Print debug information
    print("Sentiment counts:", sentiment_counts.to_dict())
    
    # Define consistent color mapping
    color_map = {
        'Positive': '#52c41a',
        'Neutral': '#1890ff',
        'Negative': '#f5222d'
    }
    
    # Only use sentiments that have actual data
    present_sentiments = sentiment_counts.index.tolist()
    present_values = sentiment_counts.values.tolist()  # Convert to list to ensure proper handling
    present_colors = [color_map[sentiment] for sentiment in present_sentiments]
    
    # Create pie chart using plotly express
    pie_fig = go.Figure(data=[go.Pie(
        labels=present_sentiments,
        values=present_values,
        hole=0.3,
        marker_colors=present_colors,
        textinfo='label+percent',
        textposition='outside',
        showlegend=False,
        automargin=True
    )])
    
    # Print debug information
    print("Pie chart data:", {
        'labels': present_sentiments,
        'values': present_values,
        'colors': present_colors
    })
    
    pie_fig.update_layout(
        title={
            'text': 'Sentiment Distribution',
            'x': 0.5,
            'y': 0.95,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20}
        },
        height=400,
        width=500,  # Set explicit width
        margin=dict(t=100, b=50, l=50, r=50),  # Increase margins
        paper_bgcolor='white',
        plot_bgcolor='white',
        showlegend=False,
        autosize=False  # Disable autosize
    )
    
    # Ensure the pie chart is centered and complete
    pie_fig.update_traces(
        rotation=90,  # Rotate to ensure proper orientation
        direction='clockwise',
        hovertemplate='%{label}<br>%{percent}<extra></extra>'
    )
    
    # Create line chart with better visualization
    df = df.sort_values('timestamp')
    
    # Create line chart with individual points
    line_fig = go.Figure()
    
    # Add scatter points for each sentiment
    for sentiment in ['Positive', 'Neutral', 'Negative']:
        sentiment_df = df[df['sentiment'] == sentiment]
        if not sentiment_df.empty:
            line_fig.add_trace(go.Scatter(
                x=sentiment_df['timestamp'],
                y=sentiment_df['value'],
                mode='markers',
                name=sentiment,
                marker=dict(
                    color=color_map[sentiment],
                    size=10
                ),
                text=sentiment_df['text'],
                hovertemplate='%{text}<br>%{x}<extra></extra>'
            ))
    
    # Add rolling average line with proper window size
    window_size = min(3, len(df))  # Use smaller window if less than 3 points
    rolling_mean = df['value'].rolling(window=window_size, min_periods=1).mean()
    
    line_fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=rolling_mean,
        mode='lines',
        name='Trend',
        line=dict(
            color='#722ed1',
            width=2,
            dash='dash'
        ),
        hovertemplate='Trend: %{y:.2f}<extra></extra>'
    ))
    
    # Customize line chart
    line_fig.update_layout(
        title='Sentiment Trend Over Time',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.1,
            xanchor="center",
            x=0.5
        ),
        yaxis=dict(
            range=[-1.2, 1.2],
            ticktext=['Negative', 'Neutral', 'Positive'],
            tickvals=[-1, 0, 1],
            title='Sentiment',
            gridcolor='#f0f0f0'
        ),
        xaxis=dict(
            title='Time',
            gridcolor='#f0f0f0'
        ),
        hovermode='closest',
        height=400,
        paper_bgcolor='white',
        plot_bgcolor='white',
        margin=dict(t=100, b=20, l=20, r=20)
    )
    
    # Convert Plotly figures to JSON-serializable dictionaries
    pie_chart_data = {
        'data': [{
            'type': 'pie',
            'labels': present_sentiments,
            'values': present_values,
            'hole': 0.3,
            'marker': {'colors': present_colors},
            'textinfo': 'label+percent',
            'textposition': 'outside',
            'showlegend': False,
            'automargin': True,
            'rotation': 90,
            'direction': 'clockwise',
            'hovertemplate': '%{label}<br>%{percent}<extra></extra>'
        }],
        'layout': {
            'title': {
                'text': 'Sentiment Distribution',
                'x': 0.5,
                'y': 0.95,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 20}
            },
            'height': 400,
            'width': 500,
            'margin': {'t': 100, 'b': 50, 'l': 50, 'r': 50},
            'paper_bgcolor': 'white',
            'plot_bgcolor': 'white',
            'showlegend': False,
            'autosize': False
        }
    }
    
    # Convert line chart data to JSON-serializable format
    line_chart_data = {
        'data': [],
        'layout': {
            'title': 'Sentiment Trend Over Time',
            'showlegend': True,
            'legend': {
                'orientation': "h",
                'yanchor': "bottom",
                'y': 1.1,
                'xanchor': "center",
                'x': 0.5
            },
            'yaxis': {
                'range': [-1.2, 1.2],
                'ticktext': ['Negative', 'Neutral', 'Positive'],
                'tickvals': [-1, 0, 1],
                'title': 'Sentiment',
                'gridcolor': '#f0f0f0'
            },
            'xaxis': {
                'title': 'Time',
                'gridcolor': '#f0f0f0'
            },
            'hovermode': 'closest',
            'height': 400,
            'paper_bgcolor': 'white',
            'plot_bgcolor': 'white',
            'margin': {'t': 100, 'b': 20, 'l': 20, 'r': 20}
        }
    }
    
    # Add scatter points for each sentiment
    for sentiment in ['Positive', 'Neutral', 'Negative']:
        sentiment_df = df[df['sentiment'] == sentiment]
        if not sentiment_df.empty:
            line_chart_data['data'].append({
                'type': 'scatter',
                'x': sentiment_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'y': sentiment_df['value'].tolist(),
                'mode': 'markers',
                'name': sentiment,
                'marker': {
                    'color': color_map[sentiment],
                    'size': 10
                },
                'text': sentiment_df['text'].tolist(),
                'hovertemplate': '%{text}<br>%{x}<extra></extra>'
            })
    
    # Add trend line
    line_chart_data['data'].append({
        'type': 'scatter',
        'x': df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
        'y': rolling_mean.tolist(),
        'mode': 'lines',
        'name': 'Trend',
        'line': {
            'color': '#722ed1',
            'width': 2,
            'dash': 'dash'
        },
        'hovertemplate': 'Trend: %{y:.2f}<extra></extra>'
    })
    
    return pie_chart_data, line_chart_data

@socketio.on_error()
def error_handler(e):
    """Handle SocketIO errors"""
    logger.error(f"SocketIO error: {str(e)}")
    return False

@socketio.on_error_default
def default_error_handler(e):
    """Handle default SocketIO errors"""
    logger.error(f"Default SocketIO error: {str(e)}")
    return False

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.debug('Client attempting to connect')
    logger.info(f'Client connected from {request.remote_addr}')
    emit('connection_response', {'data': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f'Client disconnected from {request.remote_addr}')

@socketio.on('new_feedback')
def handle_feedback(data):
    """Handle incoming feedback via WebSocket"""
    logger.debug(f'Received feedback data: {data}')
    try:
        feedback_text = data.get('feedback', '')
        logger.info(f'Processing feedback: {feedback_text}')
        
        # Analyze sentiment
        sentiment = analyze_sentiment(feedback_text)
        logger.info(f'Analyzed sentiment: {sentiment}')
        
        # Create new feedback entry
        new_feedback = Feedback(
            text=feedback_text,
            sentiment=sentiment,
            timestamp=datetime.now()
        )
        logger.info('Created new feedback entry')
        
        # Save to database
        db.session.add(new_feedback)
        db.session.commit()
        logger.info('Saved feedback to database')
        
        # Get updated charts
        pie_chart, line_chart = create_charts()
        logger.debug('Charts updated')
        
        # Get all feedback for stats
        all_feedbacks = Feedback.query.all()
        total = len(all_feedbacks)
        positive = sum(1 for f in all_feedbacks if f.sentiment == 'Positive')
        neutral = sum(1 for f in all_feedbacks if f.sentiment == 'Neutral')
        negative = sum(1 for f in all_feedbacks if f.sentiment == 'Negative')
        
        # Define suggested tips based on sentiment
        suggested_tips = {
            "Positive": "💖 Suggested Tip: 25%, 20%, or Custom",
            "Neutral": "🌿 Suggested Tip: 20%, 18%, or Custom",
            "Negative": "�� Suggested Tip: 15% or Custom"
        }
        
        # Prepare feedback data
        feedback_data = {
            'text': feedback_text,
            'sentiment': sentiment,
            'timestamp': datetime.now().isoformat(),
            'suggested_tip': suggested_tips.get(sentiment, '💫 Suggested Tip: Custom'),
            'cookie_message': '🍪 Fortune cookie has been dispensed!'
        }
        
        # Prepare response data
        response_data = {
            'feedback': feedback_data,
            'stats': {
                'total': total,
                'positive': positive,
                'neutral': neutral,
                'negative': negative
            },
            'charts': {
                'pie': pie_chart,
                'line': line_chart
            }
        }
        
        logger.info('Emitting rotate_servo event')
        socketio.emit('rotate_servo', {'timestamp': datetime.now().isoformat()}, broadcast=True)
        logger.info('rotate_servo event emitted')
        
        logger.info('Sending feedback_processed response')
        emit('feedback_processed', response_data)
        logger.info('feedback_processed response sent')
        
        logger.info('Broadcasting chart updates')
        emit('update_charts', response_data, broadcast=True)
        logger.info('Chart updates broadcasted')
        
    except Exception as e:
        logger.error(f'Error processing feedback: {str(e)}')
        emit('feedback_error', str(e))

@app.route('/')
@app.route('/dashboard')
def dashboard():
    # Get all feedback ordered by timestamp
    feedbacks = Feedback.query.order_by(Feedback.timestamp.desc()).all()
    
    # Create charts
    pie_chart, line_chart = create_charts()
    
    # Calculate stats
    total = len(feedbacks)
    positive = sum(1 for f in feedbacks if f.sentiment == 'Positive')
    neutral = sum(1 for f in feedbacks if f.sentiment == 'Neutral')
    negative = sum(1 for f in feedbacks if f.sentiment == 'Negative')
    
    stats = {
        'total': total,
        'positive': positive,
        'neutral': neutral,
        'negative': negative
    }
    
    return render_template(
        'dashboard.html',
        feedbacks=feedbacks,
        pie_chart=pie_chart,
        line_chart=line_chart,
        stats=stats
    )

if __name__ == '__main__':
    logger.info('Starting Flask-SocketIO server...')
    logger.info("Server running on all interfaces (0.0.0.0)")
    socketio.run(app, debug=True, port=5001, host='0.0.0.0', allow_unsafe_werkzeug=True) 