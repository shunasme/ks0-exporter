# ks0-exporter 

## Start commands 
```
python3 call_data.py
```

## Result data 

```
curl  http://127.0.0.1:33123/metrics
# HELP device_online Device online status
# TYPE device_online gauge
device_online 1.0
# HELP device_rtpow Real-time power consumption
# TYPE device_rtpow gauge
device_rtpow{unit="G"} 156.0
# HELP device_avgpow Average power consumption
# TYPE device_avgpow gauge
device_avgpow{unit="G"} 155.0
# HELP device_reject Device reject rate
# TYPE device_reject gauge
device_reject 4.296875
# HELP device_runtime Device runtime
# TYPE device_runtime gauge
device_runtime 4192.0
# HELP device_powstate Power state of the device
# TYPE device_powstate gauge
device_powstate 0.0
# HELP device_netstate Network state of the device
# TYPE device_netstate gauge
device_netstate 0.0
# HELP device_fanstate Fan state of the device
# TYPE device_fanstate gauge
device_fanstate 0.0
# HELP device_tempstate Temperature state of the device
# TYPE device_tempstate gauge
device_tempstate 0.0
# HELP device_intemperature Device internal temperature in Celsius
# TYPE device_intemperature gauge
device_intemperature 37.0
# HELP device_outtemperature Device external temperature in Celsius
# TYPE device_outtemperature gauge
device_outtemperature 49.0
# HELP device_fan_speed Fan speed in RPM
# TYPE device_fan_speed gauge
device_fan_speed{fan="fan_1"} 6079.0
device_fan_speed{fan="fan_2"} 6213.0
device_fan_speed{fan="fan_3"} 0.0
device_fan_speed{fan="fan_4"} 0.0
```
