from flask import Flask, jsonify, request
import json
import os
import logging
from logging.handlers import RotatingFileHandler
import signal
import sys
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)

# Cấu hình logging cho production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('api_server.log', maxBytes=50*1024*1024, backupCount=10),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Production configuration
PRODUCTION_CONFIG = {
    "max_records_per_request": 1000,
    "default_limit": 100,
    "cache_timeout": 60,  # seconds
    "enable_cors": True
}

# Simple cache để tối ưu performance
data_cache = {
    "data": [],
    "timestamp": 0.0,
    "stats": {},
    "stats_timestamp": 0.0
}

def get_cached_data():
    """Get cached data or load from file"""
    current_time = time.time()
    
    if (not data_cache["data"] or 
        data_cache["timestamp"] == 0.0 or 
        current_time - data_cache["timestamp"] > PRODUCTION_CONFIG["cache_timeout"]):
        
        try:
            if os.path.exists('trading_data.json'):
                with open('trading_data.json', 'r', encoding='utf-8') as f:
                    data_cache["data"] = json.load(f)
                    data_cache["timestamp"] = current_time
                    logger.info(f"Refreshed cache with {len(data_cache['data'])} records")
            else:
                data_cache["data"] = []
                data_cache["timestamp"] = current_time
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            data_cache["data"] = []
    
    return data_cache["data"]

def get_cached_stats():
    """Get cached statistics"""
    current_time = time.time()
    
    if (not data_cache["stats"] or 
        data_cache["stats_timestamp"] == 0.0 or 
        current_time - data_cache["stats_timestamp"] > PRODUCTION_CONFIG["cache_timeout"]):
        
        data = get_cached_data()
        if data:
            symbols = {}
            latest_timestamp = None
            total_volume = 0
            
            for trade in data:
                symbol = trade.get('symbol', 'Unknown')
                if symbol not in symbols:
                    symbols[symbol] = {"count": 0, "volume": 0}
                symbols[symbol]["count"] += 1
                
                # Calculate volume
                try:
                    price = float(trade.get('data', {}).get('price', 0))
                    size = float(trade.get('data', {}).get('size', 0))
                    volume = price * size
                    symbols[symbol]["volume"] += volume
                    total_volume += volume
                except:
                    pass
                
                # Track latest timestamp
                timestamp = trade.get('timestamp', '')
                if not latest_timestamp or timestamp > latest_timestamp:
                    latest_timestamp = timestamp
            
            data_cache["stats"] = {
                "total_trades": len(data),
                "symbols_count": len(symbols),
                "symbols_breakdown": symbols,
                "latest_trade_time": latest_timestamp,
                "total_volume_usd": total_volume,
                "data_file_size": os.path.getsize('trading_data.json') if os.path.exists('trading_data.json') else 0
            }
            data_cache["stats_timestamp"] = current_time
        else:
            data_cache["stats"] = {
                "total_trades": 0,
                "symbols_count": 0,
                "symbols_breakdown": {},
                "latest_trade_time": None,
                "total_volume_usd": 0,
                "data_file_size": 0
            }
    
    return data_cache["stats"]

@app.after_request
def after_request(response):
    """Add CORS headers for production"""
    if PRODUCTION_CONFIG["enable_cors"]:
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

@app.route('/')
def home():
    stats = get_cached_stats()
    return jsonify({
        "message": "Trading API Server - VPS PRODUCTION MODE",
        "mode": "production",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "/api/trading": "GET - Get all trading data (with pagination)",
            "/api/trading/latest": "GET - Get latest trades",
            "/api/trading/symbol/<symbol>": "GET - Get trades by symbol",
            "/api/trading/stats": "GET - Get comprehensive statistics",
            "/api/health": "GET - Health check",
            "/api/info": "GET - Server information"
        },
        "quick_stats": {
            "total_trades": stats["total_trades"],
            "active_symbols": stats["symbols_count"],
            "last_update": stats["latest_trade_time"]
        },
        "server_info": {
            "timestamp": datetime.now().isoformat(),
            "cache_enabled": True,
            "max_records_per_request": PRODUCTION_CONFIG["max_records_per_request"]
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Comprehensive health check"""
    data = get_cached_data()
    stats = get_cached_stats()
    
    # Check if data is recent (within last hour)
    data_freshness = "unknown"
    if stats.get("latest_trade_time"):
        try:
            latest_time_str = str(stats["latest_trade_time"])
            if latest_time_str and latest_time_str != "None":
                latest_time = datetime.fromisoformat(latest_time_str)
                now = datetime.now()
                diff = now - latest_time
                if diff.total_seconds() < 3600:  # 1 hour
                    data_freshness = "fresh"
                elif diff.total_seconds() < 7200:  # 2 hours
                    data_freshness = "stale"
                else:
                    data_freshness = "very_stale"
        except Exception as e:
            logger.debug(f"Error parsing timestamp: {e}")
            data_freshness = "unknown"
    
    health_status = "healthy" if data_freshness in ["fresh", "stale"] else "warning"
    
    return jsonify({
        "status": health_status,
        "mode": "production",
        "timestamp": datetime.now().isoformat(),
        "data_status": {
            "total_records": len(data),
            "freshness": data_freshness,
            "last_trade": stats["latest_trade_time"]
        },
        "cache_status": {
            "enabled": True,
            "last_refresh": datetime.fromtimestamp(data_cache["timestamp"]).isoformat() if data_cache["timestamp"] > 0 else None
        },
        "disk_status": {
            "data_file_exists": os.path.exists('trading_data.json'),
            "data_file_size_mb": round(float(stats.get("data_file_size", 0)) / (1024*1024), 2)
        }
    })

@app.route('/api/info', methods=['GET'])
def server_info():
    """Server information and configuration"""
    return jsonify({
        "server": {
            "mode": "production",
            "version": "1.0.0",
            "start_time": datetime.now().isoformat(),
            "python_version": sys.version
        },
        "configuration": PRODUCTION_CONFIG,
        "features": {
            "caching": True,
            "pagination": True,
            "filtering": True,
            "statistics": True,
            "cors": PRODUCTION_CONFIG["enable_cors"]
        }
    })

@app.route('/api/trading', methods=['GET'])
def get_trading_data():
    """Get trading data with pagination"""
    try:
        # Get parameters
        limit = request.args.get('limit', default=PRODUCTION_CONFIG["default_limit"], type=int)
        offset = request.args.get('offset', default=0, type=int)
        symbol = request.args.get('symbol', type=str)
        
        # Validate parameters
        limit = min(limit, PRODUCTION_CONFIG["max_records_per_request"])
        offset = max(offset, 0)
        
        data = get_cached_data()
        
        # Filter by symbol if specified
        if symbol:
            data = [trade for trade in data if trade.get('symbol', '').upper() == symbol.upper()]
        
        # Apply pagination
        total_records = len(data)
        paginated_data = data[offset:offset + limit]
        
        return jsonify({
            "status": "success",
            "mode": "production",
            "message": "Trading data retrieved successfully",
            "data": paginated_data,
            "pagination": {
                "total_records": total_records,
                "returned_records": len(paginated_data),
                "offset": offset,
                "limit": limit,
                "has_more": offset + limit < total_records
            },
            "filters": {
                "symbol": symbol
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in trading API: {e}")
        return jsonify({
            "status": "error",
            "mode": "production",
            "message": f"Internal server error",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/trading/latest', methods=['GET'])
def get_latest_trades():
    """Get latest trades"""
    try:
        limit = request.args.get('limit', default=50, type=int)
        limit = min(limit, 500)  # Max 500 for latest
        
        data = get_cached_data()
        latest_data = data[-limit:] if len(data) >= limit else data
        
        return jsonify({
            "status": "success",
            "mode": "production",
            "message": f"Latest {len(latest_data)} trades",
            "data": latest_data,
            "total_records": len(latest_data),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in latest trades API: {e}")
        return jsonify({
            "status": "error",
            "mode": "production",
            "message": "Internal server error"
        }), 500

@app.route('/api/trading/symbol/<symbol>', methods=['GET'])
def get_trades_by_symbol(symbol):
    """Get trades by specific symbol"""
    try:
        limit = request.args.get('limit', default=100, type=int)
        limit = min(limit, PRODUCTION_CONFIG["max_records_per_request"])
        
        data = get_cached_data()
        filtered_data = [trade for trade in data if trade.get('symbol', '').upper() == symbol.upper()]
        
        # Get latest records
        if limit > 0:
            filtered_data = filtered_data[-limit:]
        
        return jsonify({
            "status": "success",
            "mode": "production",
            "message": f"Trading data for {symbol.upper()}",
            "symbol": symbol.upper(),
            "data": filtered_data,
            "total_records": len(filtered_data),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in symbol trading API: {e}")
        return jsonify({
            "status": "error",
            "mode": "production",
            "message": "Internal server error"
        }), 500

@app.route('/api/trading/stats', methods=['GET'])
def get_trading_stats():
    """Get comprehensive trading statistics"""
    try:
        stats = get_cached_stats()
        
        return jsonify({
            "status": "success",
            "mode": "production",
            "message": "Trading statistics",
            "stats": stats,
            "cache_info": {
                "cached": True,
                "cache_age_seconds": time.time() - data_cache["stats_timestamp"] if data_cache["stats_timestamp"] else 0
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in stats API: {e}")
        return jsonify({
            "status": "error",
            "mode": "production",
            "message": "Internal server error"
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "mode": "production",
        "message": "Endpoint not found",
        "available_endpoints": [
            "/api/trading",
            "/api/trading/latest", 
            "/api/trading/symbol/<symbol>",
            "/api/trading/stats",
            "/api/health",
            "/api/info"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "mode": "production",
        "message": "Internal server error",
        "timestamp": datetime.now().isoformat()
    }), 500

def cleanup():
    """Cleanup on shutdown"""
    logger.info("Shutting down production API server...")

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    cleanup()
    sys.exit(0)

if __name__ == '__main__':
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("=" * 60)
        logger.info("TRADING API SERVER - VPS PRODUCTION MODE")
        logger.info("=" * 60)
        logger.info("Configuration:")
        for key, value in PRODUCTION_CONFIG.items():
            logger.info(f"  {key}: {value}")
        logger.info("=" * 60)
        
        # Start Flask server for production
        logger.info("Starting production API server on 0.0.0.0:5000...")
        app.run(
            debug=False, 
            port=5000, 
            host='0.0.0.0', 
            threaded=True,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        cleanup()
