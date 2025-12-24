"""
COMPLETE E-COMMERCE PAYMENT AUTOMATION SYSTEM
==============================================
This shows how big platforms like Amazon verify payments automatically.
NO MANUAL CHECKING NEEDED!

Run this file: python payment_system.py
Then visit: http://localhost:5000
"""

from flask import Flask, request, jsonify, render_template_string
import requests
import sqlite3
from datetime import datetime
import threading
import time

# ============================================
# CONFIGURATION
# ============================================
FAPSHI_BASE_URL = "https://live.fapshi.com"
FAPSHI_API_KEY = "FAK_4a22fcf5748fa13bb5d34081c6f43b01"
FAPSHI_API_USER = "5c6cc9f6-ad70-47fe-b39e-9185df8e31fb"

app = Flask(__name__)

# ============================================
# DATABASE SETUP
# ============================================
def init_db():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE,
            customer_email TEXT,
            customer_phone TEXT,
            amount INTEGER,
            trans_id TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ============================================
# HTML TEMPLATE WITH TAILWIND CSS
# ============================================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Automated Payment System</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-purple-600 via-blue-600 to-indigo-800 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="text-center mb-12">
            <h1 class="text-5xl font-bold text-white mb-4">
                🚀 Automated Payment System
            </h1>
            <p class="text-xl text-white opacity-90">
                How Amazon & Big E-commerce Verify Payments (Zero Manual Work!)
            </p>
        </div>

        <!-- Explanation Cards -->
        <div class="grid md:grid-cols-2 gap-6 mb-8">
            <!-- Method 1: Webhooks -->
            <div class="bg-white rounded-2xl shadow-2xl p-8 transform hover:scale-105 transition">
                <div class="flex items-center mb-4">
                    <span class="bg-green-500 text-white px-4 py-2 rounded-full text-sm font-bold">
                        METHOD 1: WEBHOOKS
                    </span>
                    <span class="ml-2 text-green-600">⚡ Real-time</span>
                </div>
                <h2 class="text-2xl font-bold mb-4 text-gray-800">Instant Notifications</h2>
                <div class="space-y-3 text-gray-700">
                    <div class="flex items-start">
                        <span class="text-2xl mr-3">1️⃣</span>
                        <p>Customer pays via MTN MOMO</p>
                    </div>
                    <div class="flex items-start">
                        <span class="text-2xl mr-3">2️⃣</span>
                        <p>Fapshi <strong>instantly calls YOUR server</strong></p>
                    </div>
                    <div class="flex items-start">
                        <span class="text-2xl mr-3">3️⃣</span>
                        <p>Your system auto-updates order status</p>
                    </div>
                    <div class="flex items-start">
                        <span class="text-2xl mr-3">4️⃣</span>
                        <p>Customer gets product/service immediately</p>
                    </div>
                </div>
                <div class="mt-6 p-4 bg-green-50 rounded-lg border-l-4 border-green-500">
                    <p class="text-sm font-semibold text-green-800">
                        ✅ Used by: Amazon, Shopify, Stripe, PayPal
                    </p>
                </div>
            </div>

            <!-- Method 2: Polling -->
            <div class="bg-white rounded-2xl shadow-2xl p-8 transform hover:scale-105 transition">
                <div class="flex items-center mb-4">
                    <span class="bg-yellow-500 text-white px-4 py-2 rounded-full text-sm font-bold">
                        METHOD 2: POLLING
                    </span>
                    <span class="ml-2 text-yellow-600">🔄 Backup</span>
                </div>
                <h2 class="text-2xl font-bold mb-4 text-gray-800">Scheduled Checks</h2>
                <div class="space-y-3 text-gray-700">
                    <div class="flex items-start">
                        <span class="text-2xl mr-3">1️⃣</span>
                        <p>Background job runs every 5 minutes</p>
                    </div>
                    <div class="flex items-start">
                        <span class="text-2xl mr-3">2️⃣</span>
                        <p>Checks all pending orders in database</p>
                    </div>
                    <div class="flex items-start">
                        <span class="text-2xl mr-3">3️⃣</span>
                        <p>Asks Fapshi: "Is payment complete?"</p>
                    </div>
                    <div class="flex items-start">
                        <span class="text-2xl mr-3">4️⃣</span>
                        <p>Updates status if changed</p>
                    </div>
                </div>
                <div class="mt-6 p-4 bg-yellow-50 rounded-lg border-l-4 border-yellow-500">
                    <p class="text-sm font-semibold text-yellow-800">
                        ⚠️ Safety net in case webhooks fail
                    </p>
                </div>
            </div>
        </div>

        <!-- Test the System -->
        <div class="bg-white rounded-2xl shadow-2xl p-8 mb-8">
            <h2 class="text-3xl font-bold mb-6 text-gray-800 text-center">
                🛒 Test the System (Simulate Customer Checkout)
            </h2>
            
            <form id="checkoutForm" class="max-w-md mx-auto space-y-4">
                <div>
                    <label class="block text-gray-700 font-semibold mb-2">Phone Number</label>
                    <input type="text" id="phone" value="653288958" 
                        class="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:outline-none">
                </div>
                
                <div>
                    <label class="block text-gray-700 font-semibold mb-2">Email</label>
                    <input type="email" id="email" value="mushiehedison66@gmail.com"
                        class="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:outline-none">
                </div>
                
                <div>
                    <label class="block text-gray-700 font-semibold mb-2">Amount (XAF)</label>
                    <input type="number" id="amount" value="500" min="100"
                        class="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:outline-none">
                </div>
                
                <button type="submit" 
                    class="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-4 rounded-lg font-bold text-lg hover:shadow-xl transform hover:scale-105 transition">
                    💳 Initiate Payment
                </button>
            </form>
            
            <div id="result" class="mt-6 hidden"></div>
        </div>

        <!-- Recent Orders -->
        <div class="bg-white rounded-2xl shadow-2xl p-8">
            <h2 class="text-3xl font-bold mb-6 text-gray-800 text-center">
                📦 Recent Orders (Auto-Updated!)
            </h2>
            <div id="ordersList" class="space-y-4">
                <p class="text-center text-gray-500">No orders yet. Create one above!</p>
            </div>
            <button onclick="loadOrders()" 
                class="mt-6 w-full bg-gray-200 hover:bg-gray-300 text-gray-800 py-3 rounded-lg font-semibold transition">
                🔄 Refresh Orders
            </button>
        </div>

        <!-- Stats -->
        <div class="grid md:grid-cols-3 gap-6 mt-8">
            <div class="bg-gradient-to-br from-green-500 to-green-700 rounded-2xl shadow-xl p-6 text-white">
                <div class="text-5xl font-bold mb-2">0ms</div>
                <div class="text-lg opacity-90">Manual Work Needed</div>
            </div>
            <div class="bg-gradient-to-br from-blue-500 to-blue-700 rounded-2xl shadow-xl p-6 text-white">
                <div class="text-5xl font-bold mb-2">100%</div>
                <div class="text-lg opacity-90">Automated</div>
            </div>
            <div class="bg-gradient-to-br from-purple-500 to-purple-700 rounded-2xl shadow-xl p-6 text-white">
                <div class="text-5xl font-bold mb-2">24/7</div>
                <div class="text-lg opacity-90">Always Running</div>
            </div>
        </div>
    </div>

    <script>
        // Submit checkout form
        document.getElementById('checkoutForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const phone = document.getElementById('phone').value;
            const email = document.getElementById('email').value;
            const amount = document.getElementById('amount').value;
            
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '<p class="text-center text-gray-600">Processing payment...</p>';
            resultDiv.classList.remove('hidden');
            
            try {
                const response = await fetch('/checkout', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ phone, email, amount: parseInt(amount) })
                });
                
                const data = await response.json();
                
                resultDiv.innerHTML = `
                    <div class="p-6 bg-green-50 border-2 border-green-500 rounded-lg">
                        <h3 class="text-2xl font-bold text-green-800 mb-4">✅ Payment Initiated!</h3>
                        <div class="space-y-2 text-gray-700">
                            <p><strong>Order ID:</strong> ${data.order_id}</p>
                            <p><strong>Transaction ID:</strong> ${data.trans_id}</p>
                            <p class="mt-4 p-3 bg-yellow-100 rounded">${data.message}</p>
                        </div>
                        <button onclick="checkStatus('${data.order_id}')" 
                            class="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700">
                            Check Status
                        </button>
                    </div>
                `;
                
                // Auto-refresh orders
                setTimeout(loadOrders, 2000);
                
            } catch (error) {
                resultDiv.innerHTML = `
                    <div class="p-6 bg-red-50 border-2 border-red-500 rounded-lg">
                        <p class="text-red-800">Error: ${error.message}</p>
                    </div>
                `;
            }
        });
        
        // Load all orders
        async function loadOrders() {
            try {
                const response = await fetch('/orders');
                const orders = await response.json();
                
                const ordersDiv = document.getElementById('ordersList');
                
                if (orders.length === 0) {
                    ordersDiv.innerHTML = '<p class="text-center text-gray-500">No orders yet.</p>';
                    return;
                }
                
                ordersDiv.innerHTML = orders.map(order => `
                    <div class="border-2 ${getStatusColor(order.status)} rounded-lg p-4">
                        <div class="flex justify-between items-center">
                            <div>
                                <p class="font-bold text-lg">${order.order_id}</p>
                                <p class="text-sm text-gray-600">${order.email}</p>
                                <p class="text-sm text-gray-600">${order.amount} XAF</p>
                            </div>
                            <div class="text-right">
                                <span class="px-4 py-2 rounded-full font-bold ${getStatusBadge(order.status)}">
                                    ${order.status.toUpperCase()}
                                </span>
                                <p class="text-xs text-gray-500 mt-2">${new Date(order.created_at).toLocaleString()}</p>
                            </div>
                        </div>
                    </div>
                `).join('');
                
            } catch (error) {
                console.error('Error loading orders:', error);
            }
        }
        
        // Check single order status
        async function checkStatus(orderId) {
            try {
                const response = await fetch(`/order/${orderId}`);
                const order = await response.json();
                
                alert(`Order Status: ${order.status.toUpperCase()}\nAmount: ${order.amount} XAF`);
                loadOrders();
                
            } catch (error) {
                alert('Error checking status');
            }
        }
        
        function getStatusColor(status) {
            const colors = {
                'pending': 'border-yellow-300 bg-yellow-50',
                'successful': 'border-green-500 bg-green-50',
                'failed': 'border-red-500 bg-red-50'
            };
            return colors[status] || 'border-gray-300';
        }
        
        function getStatusBadge(status) {
            const badges = {
                'pending': 'bg-yellow-500 text-white',
                'successful': 'bg-green-500 text-white',
                'failed': 'bg-red-500 text-white'
            };
            return badges[status] || 'bg-gray-500 text-white';
        }
        
        // Auto-refresh orders every 10 seconds
        setInterval(loadOrders, 10000);
        
        // Load orders on page load
        loadOrders();
    </script>
</body>
</html>
'''

# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    """Main dashboard"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/checkout', methods=['POST'])
def checkout():
    """Process customer checkout"""
    data = request.get_json()
    
    # Generate unique order ID
    order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Save order to database
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO orders (order_id, customer_email, customer_phone, amount)
        VALUES (?, ?, ?, ?)
    ''', (order_id, data['email'], data['phone'], data['amount']))
    conn.commit()
    conn.close()
    
    # Initiate payment with Fapshi
    payment_url = f"{FAPSHI_BASE_URL}/direct-pay"
    headers = {
        "apikey": FAPSHI_API_KEY,
        "apiuser": FAPSHI_API_USER,
        "Content-Type": "application/json"
    }
    
    payload = {
        "amount": data['amount'],
        "phone": data['phone'],
        "medium": "mobile money",
        "email": data['email'],
        "externalId": order_id,
        "description": f"Order {order_id}"
    }
    
    response = requests.post(payment_url, json=payload, headers=headers)
    result = response.json()
    
    # Update order with transaction ID
    trans_id = result.get('transId')
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('UPDATE orders SET trans_id = ? WHERE order_id = ?', 
              (trans_id, order_id))
    conn.commit()
    conn.close()
    
    return jsonify({
        "order_id": order_id,
        "trans_id": trans_id,
        "message": "Payment initiated! Check your phone (653288958) for USSD prompt."
    })


@app.route('/webhook/fapshi', methods=['POST'])
def fapshi_webhook():
    """
    Webhook endpoint - Fapshi calls this automatically when payment status changes
    In production, set this URL in your Fapshi dashboard
    """
    try:
        payload = request.get_json()
        
        trans_id = payload.get('transId')
        status = payload.get('status')
        external_id = payload.get('externalId')
        
        print("\n" + "="*60)
        print("WEBHOOK RECEIVED (Automated!)")
        print("="*60)
        print(f"Order ID: {external_id}")
        print(f"Transaction ID: {trans_id}")
        print(f"Status: {status}")
        print("="*60 + "\n")
        
        # Update order status
        conn = sqlite3.connect('orders.db')
        c = conn.cursor()
        c.execute('''
            UPDATE orders 
            SET status = ?, updated_at = ?
            WHERE order_id = ?
        ''', (status.lower(), datetime.now(), external_id))
        conn.commit()
        conn.close()
        
        if status == "SUCCESSFUL":
            print(f"[AUTO] Order {external_id} fulfilled automatically!")
            # Your business logic here
        
        return jsonify({"status": "received"}), 200
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/orders', methods=['GET'])
def get_all_orders():
    """Get all orders"""
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('SELECT * FROM orders ORDER BY created_at DESC LIMIT 20')
    orders = c.fetchall()
    conn.close()
    
    return jsonify([{
        "order_id": o[1],
        "email": o[2],
        "phone": o[3],
        "amount": o[4],
        "trans_id": o[5],
        "status": o[6],
        "created_at": o[7]
    } for o in orders])


@app.route('/order/<order_id>', methods=['GET'])
def get_order_status(order_id):
    """Get single order status"""
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,))
    order = c.fetchone()
    conn.close()
    
    if order:
        return jsonify({
            "order_id": order[1],
            "email": order[2],
            "amount": order[4],
            "status": order[6],
            "created_at": order[7]
        })
    else:
        return jsonify({"error": "Order not found"}), 404


# ============================================
# BACKGROUND JOB: Polling (Method 2)
# ============================================
def check_payment_status(trans_id):
    """Query Fapshi API for payment status"""
    url = f"{FAPSHI_BASE_URL}/payment-status/{trans_id}"
    headers = {
        "apikey": FAPSHI_API_KEY,
        "apiuser": FAPSHI_API_USER,
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None


def polling_job():
    """Background job that checks pending payments every 5 minutes"""
    while True:
        try:
            time.sleep(300)  # 5 minutes
            
            conn = sqlite3.connect('orders.db')
            c = conn.cursor()
            c.execute("SELECT order_id, trans_id FROM orders WHERE status = 'pending'")
            pending_orders = c.fetchall()
            
            for order_id, trans_id in pending_orders:
                if trans_id:
                    status_data = check_payment_status(trans_id)
                    if status_data:
                        new_status = status_data.get('status', '').lower()
                        
                        if new_status != 'pending':
                            c.execute('''
                                UPDATE orders 
                                SET status = ?, updated_at = ?
                                WHERE order_id = ?
                            ''', (new_status, datetime.now(), order_id))
                            
                            print(f"[POLLING] Updated {order_id} to {new_status}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Polling error: {e}")


# ============================================
# START SERVER
# ============================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("E-COMMERCE AUTOMATED PAYMENT SYSTEM")
    print("="*60)
    print("How Amazon Verifies Payments (ZERO Manual Work!)")
    print("="*60)
    print("\nServer running at: http://localhost:5000")
    print("\nEndpoints:")
    print("  GET  / - Dashboard")
    print("  POST /checkout - Create order & initiate payment")
    print("  POST /webhook/fapshi - Webhook (auto-called by Fapshi)")
    print("  GET  /orders - View all orders")
    print("  GET  /order/<id> - Check order status")
    print("="*60 + "\n")
    
    # Start background polling job
    polling_thread = threading.Thread(target=polling_job, daemon=True)
    polling_thread.start()
    print("[STARTED] Background polling job (checks every 5 minutes)")
    
    # Run Flask app
    app.run(debug=True, port=5000, use_reloader=False)