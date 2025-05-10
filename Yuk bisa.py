import RPi.GPIO as GPIO
import time
import random
import requests
from threading import Thread, Event
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# Konfigurasi Hardware
STEPPER_PINS = [17, 18, 27, 22]
STEP_SEQUENCE = [
    [1, 0, 0, 0],
    [0, 0, 1, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1]
]

# Global Variables
stop_event = Event()  # Event untuk mengendalikan motor: set=berhenti, clear=jalan
data_lock = Event()   # Lock untuk menghindari pengiriman data ketika reset

# URL untuk komunikasi dengan server Django
SERVER_IP = "192.168.91.78:8000"  # Ganti dengan IP dan port server Django Anda
SENSOR_URL = f"http://{SERVER_IP}/api/sensordata/"
POWER_URL = f"http://{SERVER_IP}/api/powersystem/"

# Counter untuk produk
good_product_count = 0
bad_product_count = 0

def setup():
    """Setup GPIO pins"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in STEPPER_PINS:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, 0)
    print("GPIO pins initialized")

def cleanup():
    """Cleanup GPIO pins"""
    for pin in STEPPER_PINS:
        GPIO.output(pin, 0)
    GPIO.cleanup()
    print("GPIO pins cleaned up")

def generate_sensor_data():
    """Generate sensor data based on motor status"""
    global good_product_count, bad_product_count
    
    # Jika motor berhenti, semua nilai sensor 0 kecuali counter
    if stop_event.is_set():
        return {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "vibration_level": 0,
            "motor_voltage": 0,
            "motor_current": 0,
            "power_consumption": 0,
            "bottle_mass": 0,
            "bottle_brightness": 0,
            "good_product": good_product_count,
            "bad_product": bad_product_count,
            "power_system": 1  # Sesuaikan dengan ID power_system di database Anda
        }
    
    # Jika motor berjalan, menghasilkan nilai-nilai sensor realistis
    # Tingkatkan counter berdasarkan peluang acak
    if random.random() > 0.8:  # 20% peluang ada produk baru
        if random.random() > 0.7:  # 30% peluang produk buruk
            bad_product_count += 1
        else:
            good_product_count += 1
    
    return {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "vibration_level": random.randint(45, 55),
        "motor_voltage": random.randint(15, 19),
        "motor_current": random.randint(50, 60),
        "power_consumption": round(60 + random.random()*10, 1),
        "bottle_mass": random.randint(50, 58),
        "bottle_brightness": random.randint(70, 80),
        "good_product": good_product_count,
        "bad_product": bad_product_count,
        "power_system": 1  # Sesuaikan dengan ID power_system di database Anda
    }

def send_sensor_data():
    """Thread untuk mengirim data sensor secara berkala"""
    print("Starting sensor data thread")
    while True:
        if not data_lock.is_set():  # Hanya kirim data jika tidak sedang lock
            try:
                payload = generate_sensor_data()
                response = requests.post(
                    SENSOR_URL,
                    json=payload,
                    timeout=3
                )
                print(f"Data sent: G:{payload['good_product']}, B:{payload['bad_product']} | Status: {response.status_code}")
            except Exception as e:
                print(f"Failed to send data: {str(e)}")
        
        time.sleep(1)  # Kirim data setiap 1 detik

def move_stepper():
    """Thread untuk menggerakkan motor stepper"""
    print("Starting stepper motor thread")
    step_index = 0
    while True:
        if not stop_event.is_set():  # Hanya jalankan motor jika event tidak di-set
            # Rotasi motor dengan sequence
            step = STEP_SEQUENCE[step_index % 4]
            for pin in range(4):
                GPIO.output(STEPPER_PINS[pin], step[pin])
            step_index += 1
            time.sleep(0.005)  # Kecepatan motor
        else:
            # Motor berhenti, tidur sebentar
            time.sleep(0.1)

def poll_power_status():
    """Thread untuk polling status daya dari server"""
    print("Starting power status polling thread")
    last_id = 0
    
    while True:
        try:
            response = requests.get(POWER_URL, timeout=3)
            if response.status_code == 200:
                power_data = response.json()
                
                if power_data and len(power_data) > 0:
                    latest_power = power_data[-1]  # Ambil data terbaru
                    
                    # Cek apakah ini status baru (ID lebih besar)
                    if latest_power["id"] > last_id:
                        last_id = latest_power["id"]
                        
                        # Set status motor berdasarkan nilai dari server
                        new_status = latest_power["status"]
                        if new_status:  # True = ON
                            if stop_event.is_set():  # Jika motor sebelumnya berhenti
                                stop_event.clear()  # Jalankan motor
                                print("Motor started from server poll (ID: {})".format(latest_power["id"]))
                        else:  # False = OFF
                            if not stop_event.is_set():  # Jika motor sebelumnya jalan
                                stop_event.set()  # Hentikan motor
                                print("Motor stopped from server poll (ID: {})".format(latest_power["id"]))
        except Exception as e:
            print(f"Error polling power status: {str(e)}")
        
        time.sleep(1)  # Poll setiap 1 detik

@app.route("/control-power", methods=["POST"])
def control_power():
    """API endpoint untuk ON/OFF motor"""
    data = request.get_json()
    
    if not data or "status" not in data:
        return jsonify({"error": "Missing 'status' parameter"}), 400
    
    status = data["status"]
    if status not in [0, 1]:
        return jsonify({"error": "Status must be 0 or 1"}), 400
    
    # Set stop_event berdasarkan status
    if status == 0:
        stop_event.set()  # Hentikan motor
        print("Motor stopped via API")
    else:
        stop_event.clear()  # Jalankan motor
        print("Motor started via API")
    
    return jsonify({
        "message": "Motor " + ("started" if status == 1 else "stopped"),
        "motor_running": status
    })

@app.route("/reset-counter", methods=["POST"])
def reset_counter():
    """API endpoint untuk reset counter"""
    global good_product_count, bad_product_count
    
    data = request.get_json()
    
    if not data or "reset" not in data:
        return jsonify({"error": "Missing 'reset' parameter"}), 400
    
    if data["reset"]:
        data_lock.set()  # Lock pengiriman data selama reset
        
        # Reset counter
        print("Resetting counters via API")
        good_product_count = 0
        bad_product_count = 0
        
        data_lock.clear()  # Unlock pengiriman data
        
        return jsonify({
            "message": "Counters reset successfully",
            "success": True
        })
    
    return jsonify({"error": "Invalid reset value"}), 400

@app.route("/status", methods=["GET"])
def get_status():
    """API endpoint untuk cek status Raspberry Pi"""
    return jsonify({
        "status": "running",
        "motor_running": not stop_event.is_set(),
        "good_product": good_product_count,
        "bad_product": bad_product_count
    })

if __name__ == "__main__":
    try:
        # Inisialisasi GPIO
        setup()
        
        # Mulai semua thread
        Thread(target=move_stepper, daemon=True).start()
        Thread(target=send_sensor_data, daemon=True).start()
        Thread(target=poll_power_status, daemon=True).start()
        
        # Jalankan server Flask
        print("Starting Flask server on port 5000")
        app.run(host="0.0.0.0", port=5000)
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
    except Exception as e:
        print(f"\nError: {str(e)}")
    finally:
        cleanup()
