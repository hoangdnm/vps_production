import websocket
import json
import threading
import time
import logging
from logging.handlers import RotatingFileHandler
import signal
import sys
from datetime import datetime
import os

# Cấu hình logging cho production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('data_collector.log', maxBytes=50*1024*1024, backupCount=10),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BitgetDataCollectorProduction:
    def __init__(self):
        self.ws = None
        self.is_running = False
        self.data_file = "trading_data.json"
        self.trading_data = []
        self.max_records = 10000  # Giới hạn cao cho production
        self.reconnect_count = 0
        self.max_reconnects = 100  # Cho phép reconnect nhiều lần
        
        # Theo dõi nhiều symbol cho production
        self.symbols = [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT", "DOTUSDT",
            "BNBUSDT", "XRPUSDT", "MATICUSDT", "LINKUSDT", "AVAXUSDT"
        ]
        
    def load_existing_data(self):
        """Load existing data from file"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.trading_data = json.load(f)
                logger.info(f"Loaded {len(self.trading_data)} records from file")
        except FileNotFoundError:
            self.trading_data = []
            logger.info("Creating new data file for production")
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self.trading_data = []
    
    def save_data(self):
        """Save data to file with rotation"""
        try:
            # Rotate data để tránh file quá lớn
            if len(self.trading_data) > self.max_records:
                # Backup file cũ
                backup_file = f"trading_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                if os.path.exists(self.data_file):
                    os.rename(self.data_file, backup_file)
                    logger.info(f"Backed up old data to {backup_file}")
                
                # Giữ lại 80% records mới nhất
                keep_records = int(self.max_records * 0.8)
                self.trading_data = self.trading_data[-keep_records:]
                logger.info(f"Rotated data, keeping {keep_records} latest records")
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.trading_data, f, indent=2, ensure_ascii=False)
            
            # Log statistics
            if len(self.trading_data) % 100 == 0:  # Log mỗi 100 records
                logger.info(f"Saved {len(self.trading_data)} records to file")
                
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def on_message(self, ws, message):
        """Handle WebSocket messages"""
        try:
            data = json.loads(message)
            
            # Handle subscription responses
            if 'event' in data:
                if data['event'] == 'subscribe':
                    symbol = data.get('arg', {}).get('instId', 'Unknown')
                    logger.info(f"[PRODUCTION] Successfully subscribed to {symbol}")
                elif data['event'] == 'error':
                    logger.error(f"Subscription error: {data}")
                return
            
            # Handle trade data
            if 'data' in data and 'arg' in data:
                arg = data['arg']
                symbol = arg.get('instId', 'Unknown')
                trades = data['data']
                
                for trade in trades:
                    trade_record = {
                        "timestamp": datetime.now().isoformat(),
                        "symbol": symbol,
                        "data": {
                            "price": trade.get('price'),
                            "size": trade.get('size'),
                            "side": trade.get('side'),
                            "tradeId": trade.get('tradeId'),
                            "ts": trade.get('ts')
                        }
                    }
                    
                    self.trading_data.append(trade_record)
                    
                    # Log chỉ trades lớn để tránh spam
                    try:
                        size_float = float(trade.get('size', 0))
                        price_float = float(trade.get('price', 0))
                        value = size_float * price_float
                        
                        if value > 1000:  # Log trades > $1000
                            logger.info(f"[PRODUCTION] Large trade: {symbol} - ${value:.2f} - {trade.get('side')}")
                    except:
                        pass
                
                # Save data periodically
                if len(self.trading_data) % 50 == 0:  # Save every 50 trades
                    self.save_data()
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.warning(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        
        # Auto-reconnect with exponential backoff
        if self.is_running and self.reconnect_count < self.max_reconnects:
            self.reconnect_count += 1
            wait_time = min(60, 2 ** min(self.reconnect_count, 6))  # Max 60s wait
            logger.info(f"Reconnecting in {wait_time} seconds... (attempt {self.reconnect_count})")
            threading.Timer(wait_time, self.connect).start()
        elif self.reconnect_count >= self.max_reconnects:
            logger.error("Maximum reconnection attempts reached. Stopping collector.")
            self.stop()
    
    def on_open(self, ws):
        """Handle WebSocket open"""
        logger.info("[PRODUCTION] WebSocket connected successfully")
        self.reconnect_count = 0  # Reset reconnect counter
        
        # Subscribe to trades for each symbol
        for i, symbol in enumerate(self.symbols):
            subscribe_msg = {
                "op": "subscribe",
                "args": [{
                    "instType": "SPOT",
                    "channel": "trade", 
                    "instId": symbol
                }]
            }
            
            # Send subscription with delay to avoid rate limiting
            def send_subscription(msg, delay):
                time.sleep(delay)
                if self.ws and self.is_running:
                    self.ws.send(json.dumps(msg))
            
            threading.Timer(i * 0.2, send_subscription, args=[subscribe_msg, 0]).start()
    
    def connect(self):
        """Connect to Bitget WebSocket"""
        try:
            logger.info("[PRODUCTION] Connecting to Bitget WebSocket...")
            
            # Bitget WebSocket URL - V2 API
            ws_url = "wss://ws.bitget.com/v2/ws/public"
            
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            
            # Run WebSocket with keep-alive
            self.ws.run_forever(
                ping_interval=30,  # Send ping every 30 seconds
                ping_timeout=10    # Wait 10 seconds for pong
            )
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            if self.is_running:
                # Retry connection after delay
                threading.Timer(10.0, self.connect).start()
    
    def start(self):
        """Start the data collector"""
        try:
            self.is_running = True
            
            # Load existing data
            self.load_existing_data()
            
            logger.info("=" * 60)
            logger.info("BITGET DATA COLLECTOR - PRODUCTION MODE")
            logger.info("=" * 60)
            logger.info(f"Tracking symbols: {', '.join(self.symbols)}")
            logger.info(f"Data file: {self.data_file}")
            logger.info(f"Max records: {self.max_records}")
            logger.info(f"Auto-rotation enabled")
            logger.info(f"Production logging enabled")
            logger.info("=" * 60)
            
            # Start periodic data save (every 5 minutes)
            def periodic_save():
                while self.is_running:
                    time.sleep(300)  # 5 minutes
                    if self.is_running:
                        self.save_data()
                        logger.info(f"Periodic save: {len(self.trading_data)} records in memory")
            
            save_thread = threading.Thread(target=periodic_save, daemon=True)
            save_thread.start()
            
            # Connect to WebSocket
            self.connect()
            
        except Exception as e:
            logger.error(f"Error starting collector: {e}")
    
    def stop(self):
        """Stop the data collector"""
        logger.info("Stopping production data collector...")
        self.is_running = False
        
        if self.ws:
            self.ws.close()
        
        # Final data save
        self.save_data()
        logger.info("Production data collector stopped!")

def signal_handler(sig, frame):
    """Handle graceful shutdown signals"""
    logger.info("Received shutdown signal...")
    collector.stop()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    collector = BitgetDataCollectorProduction()
    
    try:
        collector.start()
    except KeyboardInterrupt:
        collector.stop()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        collector.stop()
