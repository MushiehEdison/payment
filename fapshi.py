"""
FAPSHI PAYMENT LINK SYSTEM - LIVE MODE
========================================
Uses Fapshi's /initiate-pay endpoint to generate payment links
Customer pays on Fapshi's hosted page
Status updates via webhook + polling
"""

from flask import Flask, request, jsonify, render_template_string
import requests
import sqlite3
from datetime import datetime
import threading
import time
import sys
import io

# Fix encoding issues on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ==================== CONFIGURATION ====================
FAPSHI_BASE_URL = "https://live.fapshi.com"  # LIVE MODE
FAPSHI_API_KEY = "FAK_a3fb94b55652b3a77daba299f61a2b83"
FAPSHI_API_USER = "5c6cc9f6-ad70-47fe-b39e-9185df8e31fb"
RENDER_URL = "https://payment-789p.onrender.com"
# ======================================================

app = Flask(__name__)

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS orders')
    c.execute('''
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE,
            customer_email TEXT,
            customer_phone TEXT,
            amount INTEGER,
            trans_id TEXT,
            payment_link TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("[OK] Database initialized!")

init_db()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fapshi Payment Link System</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen p-8">
    <div class="max-w-4xl mx-auto">
        <!-- Header -->
        <div class="text-center mb-12">
            <h1 class="text-5xl font-bold text-gray-800 mb-2">Payment Link System</h1>
            <p class="text-gray-600">Powered by Fapshi - Live Mode</p>
        </div>

        <!-- Payment Form -->
        <div class="bg-white rounded-2xl shadow-xl p-8 mb-8">
            <h2 class="text-2xl font-semibold mb-6">Create Payment Link</h2>
            <form id="checkoutForm" class="space-y-5">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Phone Number</label>
                    <input type="text" id="phone" value="653288958" 
                           class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                           placeholder="6XXXXXXXX">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                    <input type="email" id="email" value="mushiehedison66@gmail.com"
                           class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                           placeholder="email@example.com">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Amount (XAF)</label>
                    <input type="number" id="amount" value="500" min="100"
                           class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                           placeholder="Minimum 100 XAF">
                </div>
                <button type="submit" 
                        class="w-full bg-indigo-600 text-white py-4 rounded-lg font-semibold hover:bg-indigo-700 transition-colors">
                    Generate Payment Link
                </button>
            </form>

            <div id="result" class="mt-6 hidden"></div>
        </div>

        <!-- Orders List -->
        <div class="bg-white rounded-2xl shadow-xl p-8">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-2xl font-semibold">Recent Transactions</h2>
                <button onclick="loadOrders()" class="text-indigo-600 hover:text-indigo-800">
                    Refresh
                </button>
            </div>
            <div id="ordersList" class="space-y-4">
                <p class="text-center text-gray-500 py-8">Loading orders...</p>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('checkoutForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const phone = document.getElementById('phone').value.trim();
            const email = document.getElementById('email').value.trim();
            const amount = document.getElementById('amount').value;

            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '<div class="text-center py-4"><div class="animate-spin inline-block w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full"></div><p class="mt-2 text-gray-600">Creating payment link...</p></div>';
            resultDiv.classList.remove('hidden');

            try {
                const res = await fetch('/checkout', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({phone, email, amount: parseInt(amount)})
                });

                const data = await res.json();
                if (data.error) throw new Error(data.error);

                resultDiv.innerHTML = `
                    <div class="border-2 border-green-500 bg-green-50 rounded-lg p-6">
                        <div class="text-center mb-4">
                            <div class="text-4xl mb-2">&#x2705;</div>
                            <h3 class="text-xl font-semibold text-green-800">Payment Link Created!</h3>
                            <p class="text-sm text-gray-600 mt-1">Order ID: ${data.order_id}</p>
                        </div>
                        <a href="${data.payment_link}" target="_blank" 
                           class="block bg-indigo-600 text-white text-center px-6 py-3 rounded-lg font-semibold hover:bg-indigo-700 transition-colors">
                            Open Payment Page
                        </a>
                        <p class="text-xs text-gray-600 text-center mt-3">
                            The payment page will open in a new tab
                        </p>
                    </div>
                `;

                // Open payment link
                window.open(data.payment_link, '_blank');
                
                // Start watching for status updates
                watchStatus(data.order_id);
                
                // Refresh orders list
                loadOrders();

            } catch (err) {
                resultDiv.innerHTML = `
                    <div class="border-2 border-red-500 bg-red-50 rounded-lg p-4">
                        <p class="text-red-700 font-medium">Error: ${err.message}</p>
                    </div>
                `;
            }
        });

        function watchStatus(orderId) {
            const interval = setInterval(async () => {
                try {
                    const res = await fetch(`/order/${orderId}`);
                    const order = await res.json();
                    
                    if (order.status !== 'pending') {
                        clearInterval(interval);
                        
                        const resultDiv = document.getElementById('result');
                        if (order.status === 'successful') {
                            resultDiv.innerHTML = `
                                <div class="border-2 border-green-500 bg-green-50 rounded-lg p-6 text-center">
                                    <div class="text-5xl mb-3">&#x1F389;</div>
                                    <h3 class="text-2xl font-bold text-green-800 mb-2">Payment Successful!</h3>
                                    <p class="text-gray-700">Amount: <span class="font-semibold">${order.amount} XAF</span></p>
                                    <p class="text-sm text-gray-600 mt-2">Transaction ID: ${order.trans_id}</p>
                                </div>
                            `;
                        } else if (order.status === 'failed') {
                            resultDiv.innerHTML = `
                                <div class="border-2 border-red-500 bg-red-50 rounded-lg p-6 text-center">
                                    <div class="text-4xl mb-2">&#x274C;</div>
                                    <h3 class="text-xl font-bold text-red-800">Payment Failed</h3>
                                    <p class="text-sm text-gray-600 mt-2">Please try again</p>
                                </div>
                            `;
                        }
                        
                        loadOrders();
                    }
                } catch (err) {
                    console.error('Status check error:', err);
                }
            }, 5000);
        }

        async function loadOrders() {
            try {
                const res = await fetch('/orders');
                const orders = await res.json();
                const list = document.getElementById('ordersList');
                
                if (orders.length === 0) {
                    list.innerHTML = '<p class="text-center text-gray-500 py-8">No transactions yet</p>';
                    return;
                }
                
                list.innerHTML = orders.map(o => {
                    const statusColors = {
                        'successful': 'border-green-500 bg-green-50',
                        'failed': 'border-red-500 bg-red-50',
                        'pending': 'border-yellow-500 bg-yellow-50'
                    };
                    
                    const statusText = {
                        'successful': 'SUCCESS',
                        'failed': 'FAILED',
                        'pending': 'PENDING'
                    };
                    
                    return `
                        <div class="border-2 ${statusColors[o.status] || 'border-gray-300'} rounded-lg p-4">
                            <div class="flex justify-between items-start">
                                <div class="flex-1">
                                    <p class="font-semibold text-gray-800">${o.order_id}</p>
                                    <p class="text-sm text-gray-600 mt-1">${o.email}</p>
                                    <p class="text-xs text-gray-500 mt-1">${o.phone || 'No phone'}</p>
                                    <p class="text-xs text-gray-400 mt-1">${new Date(o.created_at).toLocaleString()}</p>
                                </div>
                                <div class="text-right">
                                    <p class="text-xl font-bold text-gray-800">${o.amount} XAF</p>
                                    <p class="text-sm font-semibold uppercase mt-1">
                                        ${statusText[o.status] || o.status}
                                    </p>
                                    ${o.payment_link ? `<a href="${o.payment_link}" target="_blank" class="text-xs text-indigo-600 hover:underline mt-1 inline-block">View Link</a>` : ''}
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');
            } catch (err) {
                console.error('Load orders error:', err);
            }
        }

        loadOrders();
        setInterval(loadOrders, 15000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Render the main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/checkout', methods=['POST'])
def checkout():
    """Create a payment link using Fapshi's /initiate-pay endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        if 'amount' not in data or 'email' not in data:
            return jsonify({"error": "Missing required fields: amount and email"}), 400
        
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        payload = {
            "amount": int(data['amount']),
            "email": data['email'],
            "externalId": order_id
        }

        print(f"\n[REQUEST] Initiating payment for {order_id}")
        print(f"[INFO] Amount: {data['amount']} XAF | Email: {data['email']}")
        print(f"[INFO] Payload: {payload}")

        try:
            response = requests.post(
                f"{FAPSHI_BASE_URL}/initiate-pay",
                json=payload,
                headers={
                    "apikey": FAPSHI_API_KEY,
                    "apiuser": FAPSHI_API_USER,
                    "Content-Type": "application/json"
                },
                timeout=15
            )
        except requests.exceptions.RequestException as req_error:
            error_msg = f"Request to Fapshi failed: {str(req_error)}"
            print(f"[ERROR] {error_msg}")
            return jsonify({"error": error_msg}), 500

        print(f"\n[RESPONSE] Fapshi Status: {response.status_code}")
        print(f"[RESPONSE] Body: {response.text}\n")

        if response.status_code != 200:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = str(error_json)
            except:
                pass
            return jsonify({"error": f"Fapshi API error ({response.status_code}): {error_detail}"}), 500

        try:
            result = response.json()
        except ValueError as json_error:
            print(f"[ERROR] Failed to parse JSON: {json_error}")
            print(f"[ERROR] Response text: {response.text}")
            return jsonify({"error": "Invalid JSON response from Fapshi"}), 500

        payment_link = result.get('link')
        trans_id = result.get('transId')

        if not payment_link or not trans_id:
            print(f"[ERROR] Missing link or transId in response: {result}")
            return jsonify({"error": f"Missing payment link or transaction ID. Response: {result}"}), 500

        try:
            conn = sqlite3.connect('orders.db')
            c = conn.cursor()
            c.execute('''
                INSERT INTO orders (order_id, customer_email, customer_phone, amount, trans_id, payment_link, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
            ''', (order_id, data['email'], data.get('phone', ''), data['amount'], trans_id, payment_link))
            conn.commit()
            conn.close()
        except sqlite3.Error as db_error:
            print(f"[ERROR] Database error: {db_error}")
            return jsonify({"error": f"Database error: {str(db_error)}"}), 500

        print(f"[SUCCESS] Order created: {order_id} | Trans ID: {trans_id}")

        return jsonify({
            "order_id": order_id,
            "payment_link": payment_link,
            "trans_id": trans_id
        })

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": error_msg}), 500

@app.route('/order/<order_id>')
def get_order(order_id):
    """Get order details by order ID"""
    conn = sqlite3.connect('orders.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,))
    order = c.fetchone()
    conn.close()
    
    if order:
        return jsonify(dict(order))
    return jsonify({"error": "Order not found"}), 404

@app.route('/orders')
def get_orders():
    """Get all orders (most recent first)"""
    try:
        conn = sqlite3.connect('orders.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM orders ORDER BY created_at DESC LIMIT 50')
        orders = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify(orders)
    except Exception as e:
        print(f"[ERROR] Failed to get orders: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/webhook/fapshi', methods=['POST'])
def webhook():
    """Handle Fapshi webhook notifications"""
    try:
        payload = request.get_json()
        print(f"\n[WEBHOOK] Received: {payload}\n")
        
        if isinstance(payload, list) and payload:
            payload = payload[0]
        
        status = payload.get('status', '').lower()
        external_id = payload.get('externalId')
        
        if status and external_id:
            conn = sqlite3.connect('orders.db')
            c = conn.cursor()
            c.execute(
                'UPDATE orders SET status = ?, updated_at = ? WHERE order_id = ?',
                (status, datetime.now(), external_id)
            )
            conn.commit()
            conn.close()
            print(f"[WEBHOOK] Updated order {external_id} to status: {status}")
        
        return jsonify({"ok": True})
    
    except Exception as e:
        print(f"[ERROR] Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

def poll_status():
    """Background thread to poll Fapshi for payment status updates"""
    while True:
        time.sleep(30)
        try:
            conn = sqlite3.connect('orders.db')
            c = conn.cursor()
            c.execute("SELECT order_id, trans_id FROM orders WHERE status = 'pending'")
            pending = c.fetchall()
            
            for order_id, trans_id in pending:
                if trans_id:
                    res = requests.get(
                        f"{FAPSHI_BASE_URL}/payment-status/{trans_id}",
                        headers={
                            "apikey": FAPSHI_API_KEY,
                            "apiuser": FAPSHI_API_USER
                        },
                        timeout=10
                    )
                    
                    if res.status_code == 200:
                        data = res.json()
                        item = data[0] if isinstance(data, list) else data
                        new_status = item.get('status', '').lower()
                        
                        if new_status and new_status != 'pending':
                            c.execute(
                                "UPDATE orders SET status = ?, updated_at = ? WHERE order_id = ?",
                                (new_status, datetime.now(), order_id)
                            )
                            print(f"[POLLING] Updated {order_id} to {new_status}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"[ERROR] Poll error: {e}")

def keep_alive():
    """Keep Render service alive by pinging itself"""
    while True:
        try:
            requests.get(RENDER_URL, timeout=5)
        except:
            pass
        time.sleep(300)

if __name__ == '__main__':
    print("\n" + "="*50)
    print("FAPSHI PAYMENT LINK SYSTEM - LIVE MODE")
    print("="*50)
    print(f"API URL: {FAPSHI_BASE_URL}")
    print(f"Server: {RENDER_URL}")
    print("="*50 + "\n")
    
    threading.Thread(target=poll_status, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    
    app.run(host='0.0.0.0', port=5000, debug=True)