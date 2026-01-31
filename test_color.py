from pydualsense import pydualsense , TriggerModes
import vgamepad as vg
import time
import socket
import struct
import psutil, os, gc

# Désactive le ramasse-miettes pendant la boucle critique pour éviter les micro-saccades
gc.disable() 

# Force la priorité maximale (Realtime)
p = psutil.Process(os.getpid())
p.nice(psutil.REALTIME_PRIORITY_CLASS)

ds = pydualsense()
ds.init()
g= vg.VX360Gamepad()
IP = "127.0.0.1"
PORT = 4444
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((IP, PORT))
FMT = "<I4sHBB7f2I3f16s16si"
EXPECTED = struct.calcsize(FMT)  # = 96
FMT2 = "<4s18f"
EXPECTED2 = struct.calcsize(FMT2)

last_gear = None

def clamp8(v):
    return max(0, min(255, int(v)))

def rpm_light(rpm):
    rpm_norm = min(max(rpm / 6000.0, 0.0), 1.0)

    # Vert → Jaune → Rouge
    if rpm_norm < 0.25:
        # Vert → Jaune
        r = clamp8(rpm_norm * 2 * 255)
        g = 255
        b = 0
    else:
        # Jaune → Rouge
        r = 255
        g = clamp8((1.0 - rpm_norm) * 2 * 255)
        b = 0

    ds.light.setColorI(r, g, b)

def convert_stick(v):
    return int(max(-128, min(127, v)) * 256)  # -128..127 → -32768..32767

def button_update():
    global ds
    #joystick part
    lx = ds.state.LX
    ly = ds.state.LY
    rx= ds.state.RX
    ry= ds.state.RY
    g.left_joystick(
        x_value=convert_stick(lx),
        y_value=convert_stick(-ly)
    )
    g.right_joystick(
        x_value=convert_stick(rx),
        y_value=convert_stick(-ry)
    )

    #d-pad part
    pad_up = ds.state.DpadUp
    pad_down = ds.state.DpadDown
    pad_left = ds.state.DpadLeft
    pad_right = ds.state.DpadRight
    if pad_up:
        g.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
    if pad_down:
        g.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
    if pad_left:
        g.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
    if pad_right:
        g.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)


    #button part
    a_button = ds.state.cross
    b_button = ds.state.circle
    x_button = ds.state.triangle
    y_button = ds.state.square
    if a_button:
        g.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
    if b_button:
        g.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    if x_button:
        g.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
    if y_button:
        g.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
    

    #trigger part
    r2 = ds.state.R2
    l2 = ds.state.L2
    vg_r2 = int(max(0.0, min(1.0, r2)) * 255)
    vg_l2 = int(max(0.0, min(1.0, l2)) * 255)
    g.right_trigger(value=vg_r2)
    g.left_trigger(value=vg_l2)

    #select part
    select_button = ds.state.share
    start_button = ds.state.options
    if select_button:
        g.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_SELECT)
    if start_button:
        g.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_START)

    #special part
    special_button = ds.state.ps
    if special_button:
        g.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_SPECIAL)

    g.update()

def gear_label(g):
    if g == 0: return "R"
    if g == 1: return "N"
    return str(g - 1)  

while True:
    button_update()  
    #-----------------------
    data, addr = sock.recvfrom(1024)

    
    og = struct.unpack(FMT, data)
    gear = og[3]
    speed_ms  = og[5]
    rpm       = og[6]
    throttle  = og[14]   # 0..1
    brake     = og[15] 
   

    is_gear_change = (gear != last_gear)
    if is_gear_change:
        last_gear = gear
        force_gear = 2
    else:
        force_gear = 1

    x = force_gear
    
    # Calculate force based on RPM
    r2_force = 0
    trigger_mode = TriggerModes.Rigid

    if 2000 <= rpm < 3000:
        r2_force = 0 if is_gear_change else 65
    elif 3000 <= rpm < 4000:
        r2_force = 0 if is_gear_change else 130
    elif 4000 <= rpm < 5000:
        r2_force = 255 if is_gear_change else 165
    elif 5000 <= rpm < 6000:
        r2_force = 255
    else:
        trigger_mode = TriggerModes.Off
    
    ds.triggerR.setMode(trigger_mode)
    if trigger_mode == TriggerModes.Rigid:
        ds.triggerR.setForce(x, r2_force)
    
    # lEft trigger effect
    if brake > 0:
        brake_force= r2_force
        ds.triggerL.setMode(TriggerModes.Pulse)
        ds.triggerL.setForce(0, brake_force)
        ds.light.setColorI(255, 0, 0)

    else:
        rpm_light(rpm)
        ds.triggerL.setMode(TriggerModes.Off)

    #Vibration base on velocity
    
    speed_kph = speed_ms * 3.6
    #print(f"gear:{gear_label(gear)} rpm:{rpm:.0f} brake:{brake:.2f} kph:{speed_kph:.1f} thr:{throttle:.2f} speed_kph:{speed_kph:.2f}", end="\r")
   #time.sleep(0.00001)
