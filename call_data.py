from flask import Flask, Response
from prometheus_client import generate_latest, CollectorRegistry, Gauge
import json
import time
import json
import socket
import select
import requests

app = Flask(__name__)
REGISTRY = CollectorRegistry(auto_describe=False)

# Fetch data via web (Deprecated)
def fetch_data():
    url = 'http://10.0.0.216/user/userpanel'

    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Cookie': 'ctime=1; language=cn',
        'DNT': '1',
        'Origin': 'http://10.0.0.216',
        'Pragma': 'no-cache',
        'Referer': 'http://10.0.0.216/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }

    data = {
        'post': '4',
    }

    response = requests.post(url, headers=headers, data=data, verify=False)  # Set verify=False to ignore SSL certificate validation

    # Print response content
    return response.text

def send_message(buf, buf_size, read_buff, read_buff_size):
    try:
        # Create a socket
        sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Define server address (IP address, port number)
        server_addr = ("10.0.0.216", 4111)
        # Connect to the server
        sockfd.connect(server_addr)
        print(f"Socket [{sockfd.fileno()}] sending {buf_size} bytes of data to the server: {buf}\n")
        # Send data
        sockfd.send(buf.encode())  # Encode to bytes before sending
        # Set up select for handling timeouts
        readfds = [sockfd]
        timeout = 10
        # Wait for data or timeout
        rlist, _, _ = select.select(readfds, [], [], timeout)

        if not rlist:
            print("Data retrieval timed out.\n")
            sockfd.close()
            return "Read Timeout!"

        # Read data from the socket
        rv = sockfd.recv(read_buff_size)
        if not rv:
            print(f"Socket [{sockfd.fileno()}] disconnected\n")
        else:
            print(f"Socket [{sockfd.fileno()}] read {len(rv)} bytes of data from the server: {rv.decode()}\n")  # Decode to string

        sockfd.close()
        return rv.decode()
    except Exception as e:
        print(f"An exception occurred: {str(e)}")
        return "An exception occurred!"

# Get monitoring data via socket
def get_monitor_data():
    readdata = bytearray(81920)
    ret = dict()
    datalist = ["info", "getnet", "boardpow", "state", "fan", "getpool", "board"]
    for i in datalist:
        senddata = {"id": i}
        senddata = json.dumps(senddata) + "\n"
        result = send_message(senddata, len(senddata), readdata, len(readdata))
        ret.update(json.loads(result).get('ret', {}))

    return {"data": ret}

# Convert human-readable uptime to seconds
def uptime_format(humantime):
    runtime_str = humantime
    runtime_parts = runtime_str.split(':')
    if len(runtime_parts) == 4:
        days, hours, minutes, seconds = map(int, runtime_parts)
        total_seconds = (days * 24 * 3600) + (hours * 3600) + (minutes * 60) + seconds
    else:
        hours, minutes, seconds = map(int, runtime_parts)
        total_seconds = (hours * 3600) + (minutes * 60) + seconds

    return total_seconds

# Create Prometheus metrics
g_online = Gauge('device_online', 'Device online status', registry=REGISTRY)
g_rtpow = Gauge('device_rtpow', 'Real-time power consumption', ['unit'], registry=REGISTRY)
g_avgpow = Gauge('device_avgpow', 'Average power consumption', ['unit'], registry=REGISTRY)
g_reject = Gauge('device_reject', 'Device reject rate', registry=REGISTRY)
g_runtime = Gauge('device_runtime', 'Device runtime', registry=REGISTRY)
g_powstate = Gauge('device_powstate', 'Power state of the device', registry=REGISTRY)
g_netstate = Gauge('device_netstate', 'Network state of the device', registry=REGISTRY)
g_fanstate = Gauge('device_fanstate', 'Fan state of the device', registry=REGISTRY)
g_tempstate = Gauge('device_tempstate', 'Temperature state of the device', registry=REGISTRY)
# Add temperature metrics to Prometheus
g_intmp = Gauge('device_intemperature', 'Device internal temperature in Celsius', registry=REGISTRY)
g_outtmp = Gauge('device_outtemperature', 'Device external temperature in Celsius', registry=REGISTRY)
g_fans = Gauge('device_fan_speed', 'Fan speed in RPM', ['fan'], registry=REGISTRY)

@app.route('/metrics')
def metrics():
    # Fetch data via web API (Deprecated)
    #data = fetch_data()  # Get data
    #parsed_data = json.loads(data)
    # Get monitoring data via socket
    parsed_data = get_monitor_data()

    # Update Prometheus metrics
    g_online.set(int(parsed_data['data']['online']))
    g_rtpow.labels(unit=parsed_data['data']['unit']).set(float(parsed_data['data']['rtpow'].replace('G', '')))
    g_avgpow.labels(unit=parsed_data['data']['unit']).set(float(parsed_data['data']['avgpow'].replace('G', '')))
    g_reject.set(parsed_data['data']['reject'])
    g_runtime.set(uptime_format(parsed_data['data']['runtime']))

    # Get states via socket
    powstate = 0 if parsed_data['data']['pow'] else 1
    netstate = 0 if parsed_data['data']['net'] else 1
    fanstate = 0 if parsed_data['data']['fan'] else 1
    tempstate = 0 if parsed_data['data']['temp'] else 1
    g_powstate.set(powstate)
    g_netstate.set(netstate)
    g_fanstate.set(fanstate)
    g_tempstate.set(tempstate)

    # Get temperature values (assuming they are in Celsius)
    intmp = float(parsed_data['data']['boards'][0]['intmp'])
    outtmp = float(parsed_data['data']['boards'][0]['outtmp'])
    g_intmp.set(intmp)
    g_outtmp.set(outtmp)

    # Add fan speed metrics to Prometheus
    for i in range(1, len(parsed_data['data']['fans']) + 1):
        fan_labels = 'fan_{}'.format(i)
        index = i - 1
        fan_speeds = parsed_data['data']['fans'][index]
        g_fans.labels(fan=fan_labels).set(float(fan_speeds))

    # Generate Prometheus-formatted metric data
    data = generate_latest(REGISTRY)

    return Response(data, content_type='text/plain; version=0.0.4')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=33123, debug=False)

