import os
import subprocess
import requests
import json
import time
from tivars.types import TIString
from tivars.models import TI_84PCE

MEDIA_DEVICE_COPIER = os.path.join(".", "publish", "MediaDeviceCopier.exe")
SERVER_URL = "http://left-integrating.gl.at.ply.gg:60412"

def log(message, level="INFO"):
    timestamp = time.strftime("%H:%M:%S")
    prefix = {
        "INFO": "✓",
        "ERROR": "❌", 
        "WARN": "⚠️"
    }.get(level, "•")
    print(f"[{timestamp}] {prefix} {message}")

def clear_calculator_variable(var_name):
    send_dir = os.path.join(".", "send")
    
    if not os.path.exists(send_dir):
        os.makedirs(send_dir)
    
    ti_string = TIString(name=var_name)
    ti_string.load_string("")
    
    filename = os.path.join(send_dir, f"CLEAR_{var_name}.8xs")
    ti_string.save(filename, model=TI_84PCE)
    
    try:
        subprocess.run([
            MEDIA_DEVICE_COPIER, "upload-files",
            "-n", "TI-84 Plus CE",
            "-s", send_dir,
            "-t", "RAM",
            "-se"
        ], check=False, capture_output=True)
        
        log(f"Cleared {var_name} on calculator")
        
    except Exception as e:
        log(f"Error clearing {var_name}: {e}", "ERROR")
    
    if os.path.exists(filename):
        os.remove(filename)

def send_session_id(session_id):
    send_dir = os.path.join(".", "send")
    
    if not os.path.exists(send_dir):
        os.makedirs(send_dir)
    
    ti_string = TIString(name="Str7")
    ti_string.load_string(session_id)
    
    filename = os.path.join(send_dir, "SESSION.8xs")
    ti_string.save(filename, model=TI_84PCE)
    
    try:
        subprocess.run([
            MEDIA_DEVICE_COPIER, "upload-files",
            "-n", "TI-84 Plus CE",
            "-s", send_dir,
            "-t", "RAM",
            "-se"
        ], check=False, capture_output=True)
        
        log("Session ID transferred to calculator")
        
    except Exception as e:
        log(f"Session transfer error: {e}", "ERROR")
    
    if os.path.exists(filename):
        os.remove(filename)

def send_received_message(message):
    send_dir = os.path.join(".", "send")
    
    if not os.path.exists(send_dir):
        os.makedirs(send_dir)
    
    ti_string = TIString(name="Str3")
    ti_string.load_string(message)
    
    filename = os.path.join(send_dir, "RECEIVED.8xs")
    ti_string.save(filename, model=TI_84PCE)
    
    try:
        subprocess.run([
            MEDIA_DEVICE_COPIER, "upload-files",
            "-n", "TI-84 Plus CE",
            "-s", send_dir,
            "-t", "RAM",
            "-se"
        ], check=False, capture_output=True)
        
        log("Received message transferred to calculator")
        
    except Exception as e:
        log(f"Message transfer error: {e}", "ERROR")
    
    if os.path.exists(filename):
        os.remove(filename)

def get_calculator_string(var_name):
    receive_dir = os.path.join(".", "receive")
    
    if not os.path.exists(receive_dir):
        os.makedirs(receive_dir)
    
    try:
        result = subprocess.run([
            MEDIA_DEVICE_COPIER, "download-files",
            "-n", "TI-84 Plus CE",
            "-s", "RAM",
            "-t", receive_dir
        ], check=False, capture_output=True, text=True)
        
        downloaded_files = os.listdir(receive_dir)
        
        for filename in downloaded_files:
            if filename.upper().startswith(var_name.upper()) and filename.endswith('.8xs'):
                filepath = os.path.join(receive_dir, filename)
                try:
                    ti_string = TIString.open(filepath)
                    content = ti_string.string()
                    
                    for f in downloaded_files:
                        file_path = os.path.join(receive_dir, f)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    
                    return content
                    
                except Exception as e:
                    log(f"Error reading {filename}: {e}", "ERROR")
        
        for f in downloaded_files:
            file_path = os.path.join(receive_dir, f)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        return None
        
    except Exception as e:
        log(f"Error downloading files: {e}", "ERROR")
        return None

def check_calculator_connection():
    try:
        result = subprocess.run([
            MEDIA_DEVICE_COPIER, "list-devices"
        ], capture_output=True, text=True, check=False)
        
        return "TI-84 Plus CE" in result.stdout
            
    except Exception as e:
        log(f"Error checking devices: {e}", "ERROR")
        return False

def handle_authentication():
    log("Processing authentication request")
    
    raw_auth_data = get_calculator_string("STR0")
    if not raw_auth_data:
        log("No authentication data found", "ERROR")
        return False
    
    clean_auth_data = raw_auth_data.strip().strip('"')
    log(f"Auth data received: {clean_auth_data}")
    
    try:
        auth_parts = clean_auth_data.split(":", 2)
        if len(auth_parts) != 3:
            log("Invalid authentication data format", "ERROR")
            clear_calculator_variable("Str0")
            send_session_id("")
            return False
            
        request_type = auth_parts[0].strip().strip('"').upper()
        user_name = auth_parts[1].strip().strip('"')
        user_password = auth_parts[2].strip().strip('"')
        
        log(f"Auth type: '{request_type}', Username: '{user_name}'")
        
        if request_type == "LOGIN":
            api_endpoint = "/login"
        elif request_type == "SIGNUP":
            api_endpoint = "/signup"
        else:
            log(f"Unknown auth type: {request_type}", "ERROR")
            clear_calculator_variable("Str0")
            send_session_id("")
            return False
        
        log(f"Using endpoint: {api_endpoint}")
        
        try:
            server_response = requests.post(f"{SERVER_URL}{api_endpoint}", json={
                "username": user_name,
                "password": user_password
            })
            
            clear_calculator_variable("Str0")
            
            if server_response.status_code == 200:
                response_data = server_response.json()
                new_session_id = response_data.get("session_id", "")
                
                log(f"{request_type} successful for user: {user_name}")
                log(f"Session ID: {new_session_id}")
                
                send_session_id(new_session_id)
                return True
                
            else:
                try:
                    error_response = server_response.json()
                    error_message = error_response.get("error", "Unknown error")
                except:
                    error_message = f"HTTP {server_response.status_code}"
                log(f"{request_type} failed: {error_message}", "ERROR")
                send_session_id("")
                return False
                
        except requests.RequestException as network_error:
            log(f"Server connection error: {network_error}", "ERROR")
            send_session_id("")
            return False
        except Exception as request_error:
            log(f"Request processing error: {request_error}", "ERROR")
            send_session_id("")
            return False
            
    except Exception as parsing_error:
        log(f"Error parsing authentication data: {parsing_error}", "ERROR")
        clear_calculator_variable("Str0")
        send_session_id("")
        return False

def handle_send_message():
    log("Processing send message request")
    
    message_data = get_calculator_string("STR1")
    session_id = get_calculator_string("STR7")
    
    if not message_data:
        log("No message data found", "ERROR")
        return False
    
    if not session_id:
        log("No session ID found - please authenticate first", "ERROR")
        return False
    
    try:
        message_data = message_data.strip().strip('"')
        session_id = session_id.strip().strip('"')
        
        parts = message_data.split(":", 2)
        if len(parts) != 3:
            log("Invalid message data format", "ERROR")
            clear_calculator_variable("Str1")
            return False
            
        sender, recipient, message = parts
        sender = sender.strip().strip('"')
        recipient = recipient.strip().strip('"')
        message = message.strip().strip('"')
        
        response = requests.post(f"{SERVER_URL}/send_message", json={
            "session_id": session_id,
            "sender": sender,
            "recipient": recipient,
            "message": message
        })
        
        clear_calculator_variable("Str1")
        
        if response.status_code == 200:
            log(f"Message sent from {sender} to {recipient}")
            log(f"Message: {message}")
            return True
        else:
            try:
                error_msg = response.json().get("error", "Unknown error")
            except:
                error_msg = f"HTTP {response.status_code}"
            log(f"Message send failed: {error_msg}", "ERROR")
            return False
            
    except ValueError as e:
        log(f"Error parsing message data: {e}", "ERROR")
        clear_calculator_variable("Str1")
        return False
    except requests.RequestException as e:
        log(f"Server connection error: {e}", "ERROR")
        clear_calculator_variable("Str1")
        return False
    except Exception as e:
        log(f"Send message error: {e}", "ERROR")
        clear_calculator_variable("Str1")
        return False

def handle_receive_messages():
    log("Processing receive messages request")
    
    session_id = get_calculator_string("STR7")
    
    if not session_id:
        log("No session ID found - please authenticate first", "ERROR")
        send_received_message("")
        return False
    
    try:
        session_id = session_id.strip().strip('"')
        
        response = requests.get(f"{SERVER_URL}/get_messages", params={
            "session_id": session_id
        })
        
        if response.status_code == 200:
            data = response.json()
            messages = data.get("messages", [])
            
            if messages:
                latest_message = messages[-1]
                formatted_msg = f"FROM: {latest_message['sender']}\nMSG: {latest_message['message']}"
                
                log(f"New message from {latest_message['sender']}")
                log(f"Message: {latest_message['message']}")
                
                send_received_message(formatted_msg)
                return True
                
            else:
                log("No new messages")
                send_received_message("")
                return True
                
        else:
            try:
                error_msg = response.json().get("error", "Unknown error")
            except:
                error_msg = f"HTTP {response.status_code}"
            log(f"Message receive failed: {error_msg}", "ERROR")
            send_received_message("")
            return False
            
    except requests.RequestException as e:
        log(f"Server connection error: {e}", "ERROR")
        send_received_message("")
        return False
    except Exception as e:
        log(f"Receive messages error: {e}", "ERROR")
        send_received_message("")
        return False

def auto_detect_and_process():
    try:
        auth_data = get_calculator_string("STR0")
        message_data = get_calculator_string("STR1")
        session_id = get_calculator_string("STR7")
        
        if auth_data and auth_data.strip().strip('"') and ("LOGIN:" in auth_data.upper() or "SIGNUP:" in auth_data.upper()):
            log("Detected authentication request")
            return handle_authentication()
        
        elif message_data and message_data.strip().strip('"') and session_id and session_id.strip().strip('"'):
            log("Detected send message request")
            return handle_send_message()
        
        elif session_id and session_id.strip().strip('"') and not (message_data and message_data.strip().strip('"')):
            log("Detected receive messages request")
            return handle_receive_messages()
        
        else:
            return True
            
    except Exception as e:
        log(f"Error in auto-detection: {e}", "ERROR")
        return False

def main():
    print("=== TI-84 Plus CE Automated Server Messenger ===")
    print("Waiting for calculator connection...")
    print("Press Ctrl+C to quit")
    print("="*50)
    
    if not os.path.exists(MEDIA_DEVICE_COPIER):
        log(f"MediaDeviceCopier not found at: {MEDIA_DEVICE_COPIER}", "ERROR")
        return
    
    calculator_connected = False
    
    try:
        while True:
            try:
                current_connection = check_calculator_connection()
                
                if current_connection and not calculator_connected:
                    log("TI-84 Plus CE connected - monitoring for requests")
                    calculator_connected = True
                    
                elif not current_connection and calculator_connected:
                    log("TI-84 Plus CE disconnected - waiting for reconnection", "WARN")
                    calculator_connected = False
                
                if calculator_connected:
                    auto_detect_and_process()
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                log("Shutdown requested by user")
                break
            except Exception as e:
                log(f"Unexpected error: {e}", "ERROR")
                time.sleep(1)
                
    except KeyboardInterrupt:
        log("Goodbye!")

if __name__ == "__main__":
    main()