import wiegand
import time
import pigpio as gpio
import threading
import IO_init
import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import messagebox, Message
from _tkinter import TclError
import json
from multiprocessing import Process

""" --------------------Global Variables ----------------"""
dem = 0
GPIO_Sensor_ON = False
GPIO_LOCK_ON = False
GPIO_LOCK_status = False
chuoi = None
id = None
wiegandData = 0
w = None
pi = None
timer = 0
serial_chuoi = None
chuoi2 = None
IDcard_code = 0
dem_cuamo = 0
AUTHORIZED_CARD_ID = 15819  # Thẻ được phép mở cửa

# Arduino-like functions
def digitalWrite(pin, value):
    """Giống như digitalWrite trong Arduino"""
    IO_init.SetIOOutput(pin, value)

def digitalRead(pin):
    """Giống như digitalRead trong Arduino"""
    return IO_init.GetIOStatus(pin)

def delay(ms):
    """Giống như delay trong Arduino - đơn vị millisecond"""
    time.sleep(ms / 1000.0)

def delayMicroseconds(us):
    """Giống như delayMicroseconds trong Arduino"""
    time.sleep(us / 1000000.0)

def millis():
    """Giống như millis() trong Arduino - trả về thời gian tính từ khi khởi động"""
    return int(time.time() * 1000)

def setup():
    """Giống như setup() trong Arduino - khởi tạo ban đầu"""
    global pi, w
    print("Khởi tạo hệ thống...")
    IO_init.Init()
    
    # Khởi tạo RFID reader
    pi = gpio.pi()
    w = wiegand.decoder(pi, 20, 21, callback)
    
    # Blink LED để báo khởi động thành công
    for i in range(3):
        digitalWrite(IO_init.GPIO_Led, 1)
        delay(500)
        digitalWrite(IO_init.GPIO_Led, 0)
        delay(500)
    
    print("Hệ thống đã sẵn sàng!")

def loop():
    """Giống như loop() trong Arduino - vòng lặp chính"""
    global dem, GPIO_LOCK_status, chuoi, chuoi2, dem_cuamo
    
    # Kiểm tra nút reset (GPIO 18)
    if digitalRead(18) == 0:
        # Xử lý sensor cửa
        if digitalRead(15) == 0:
            GPIO_Sensor_ON = False
        
        # Xử lý logic mở cửa
        LOCK_event_detect()
        LOCK_event_handle()
        
        # Debug information
        print("----------------DEBUG---------------------")
        print(f"Sensor Status: {digitalRead(IO_init.GPIO_Sensor)}")
        print(f"Lock Status: {digitalRead(IO_init.GPIO_Led)}")
        print(f"Card Status: {chuoi}")
        
        # Reset duplicate card reading
        if chuoi != None and chuoi == chuoi2:
            chuoi2 = None
        
        delay(1000)
        
    elif digitalRead(18) == 1:
        # Chế độ emergency - mở cửa 15 giây
        digitalWrite(IO_init.GPIO_LOCK, 0)
        delay(15000)

def callback(bits, value):
    """Callback function khi đọc được thẻ RFID"""
    global chuoi, IDcard_code, serial_chuoi, chuoi2
    
    try:
        print(f"bits={bits} value={value}")
        IDcard_code = int(bin(value)[-17:-1], 2)
        print(f"Card ID: {IDcard_code}")
        
        # Kiểm tra thẻ có được phép không
        if IDcard_code == AUTHORIZED_CARD_ID:
            chuoi = "OK"
            print("Thẻ hợp lệ - Cho phép mở cửa")
        else:
            chuoi = "NG"
            print("Thẻ không hợp lệ - Từ chối truy cập")
            
        chuoi2 = chuoi
        
    except Exception as e:
        chuoi = None
        print(f"Lỗi đọc thẻ: {e}")

def readWiegand():
    """Khởi tạo đọc RFID"""
    global w, pi
    import pigpio
    import wiegand
    pi = pigpio.pi()
    w = wiegand.decoder(pi, 20, 21, callback)

def LOCK_event_detect():
    """Xác định trạng thái khóa dựa trên kết quả đọc thẻ"""
    global GPIO_LOCK_status, chuoi
    
    if chuoi == None:
        GPIO_LOCK_status = False
    elif chuoi == "NG":
        GPIO_LOCK_status = False
    elif chuoi == "OK":
        GPIO_LOCK_status = True
    else:
        GPIO_LOCK_status = False

def count_cuamo():
    """Đếm ngược thời gian chờ mở cửa"""
    global dem_cuamo, dem, chuoi
    
    dem_cuamo = dem_cuamo - 1
    print(f"Đếm cửa mở: {dem_cuamo}")
    
    if dem_cuamo == 0:
        print("Hết thời gian chờ - Không mở cửa")
        dem = 2
        chuoi = None

def LOCK_event_handle():
    """Xử lý logic điều khiển khóa cửa"""
    global dem_cuamo, dem, chuoi, GPIO_LOCK_status
    
    sensor_status = digitalRead(IO_init.GPIO_Sensor)
    
    # State 1: Cửa đóng và có tín hiệu mở cửa
    if GPIO_LOCK_status == True and sensor_status == 0 and dem == 0:
        digitalWrite(IO_init.GPIO_LOCK, 0)  # Mở khóa
        dem = 1
        dem_cuamo = 50
        print("State 1: Kích hoạt mở cửa")
    
    # State 2: Đang chờ cửa mở
    elif GPIO_LOCK_status == True and sensor_status == 0 and dem == 1:
        count_cuamo()
        print("State 2: Chờ cửa mở")
    
    # State 3: Cửa đã mở
    elif GPIO_LOCK_status == True and sensor_status == 1 and dem == 1:
        dem = 2
        digitalWrite(IO_init.GPIO_LOCK, 1)  # Giữ trạng thái
        print("State 3: Cửa đã mở")
        GPIO_LOCK_status = False
    
    # State 4: Cửa đóng lại
    elif GPIO_LOCK_status == True and dem == 2 and sensor_status == 0:
        dem = 0
        chuoi = None
        GPIO_LOCK_status = False
        digitalWrite(IO_init.GPIO_LOCK, 1)
        print("State 4: Cửa đã đóng - Reset")
    
    # Default: Khóa cửa
    else:
        dem = 0
        chuoi = None
        digitalWrite(IO_init.GPIO_LOCK, 1)

def main():
    """Hàm main - Arduino style"""
    global chuoi2, chuoi, dem_cuamo, dem, GPIO_LOCK_status
    
    # Reset all variables
    dem = 0
    GPIO_Sensor_ON = False
    GPIO_LOCK_ON = False
    GPIO_LOCK_status = False
    chuoi = None
    dem_cuamo = 0
    
    try:
        setup()  # Arduino setup
        
        while True:
            loop()  # Arduino loop
            
    except KeyboardInterrupt:
        print("Chương trình dừng bởi người dùng")
    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        print("Dọn dẹp GPIO...")
        if 'w' in globals() and w:
            w.cancel()
        if 'pi' in globals() and pi:
            pi.stop()
        IO_init.GPIO.cleanup()
        print("Hoàn thành!")

"""
-------------Simplified GUI--------------------
"""
def GUI():
    global e, e1, e2, lastplace, IDcard_code, dem_cuamo, dem
    
    root = Tk()
    root.title("RFID Door Control System")
    root["bg"] = "#b0c4de"
    root.geometry("800x480")

    def update_status():
        """Cập nhật trạng thái GUI"""
        try:
            # Cập nhật trạng thái cửa
            if digitalRead(IO_init.GPIO_Sensor) == 0:
                canvas.itemconfig(arc, fill="red")
                door_status = "Cửa đóng"
            else:
                canvas.itemconfig(arc, fill="green")
                door_status = "Cửa mở"
            
            # Cập nhật thông tin
            e1.delete("1.0", END)
            e1.insert("1.0", f"\nHệ thống RFID Door Control\nThẻ hợp lệ: {AUTHORIZED_CARD_ID}")
            
            e2.delete("1.0", END)
            if IDcard_code == AUTHORIZED_CARD_ID:
                e2.insert("1.0", f"{door_status}\nThẻ hợp lệ - Truy cập được phép!")
            else:
                e2.insert("1.0", f"{door_status}\nChờ quét thẻ hợp lệ...")
                
        except:
            pass
            
        root.after(1000, update_status)

    # Main label
    label_main = Label(root, text="RFID Door Control", 
                      font=("Arial bold", 15), fg="green", bg="#b0c4de")
    label_main.grid(row=0, column=0, columnspan=4)

    # Status frames
    frame_status = LabelFrame(root, text="System Status", 
                             font=("Arial", 9), bg="#b0c4de")
    frame_status.grid(row=1, column=0, sticky=(tk.N, tk.W, tk.S))

    frame_door = LabelFrame(root, text="Door Status", 
                           font=("Arial", 9), bg="#b0c4de")
    frame_door.grid(row=1, column=1, columnspan=2, sticky=(tk.N, tk.W, tk.S))

    frame_indicator = LabelFrame(root, text="Indicator", 
                                font=("Arial", 7), bg="#b0c4de")
    frame_indicator.grid(row=1, column=3, sticky=(tk.N, tk.W, tk.S))

    # Canvas for door status indicator
    canvas = tk.Canvas(frame_indicator, height=60, width=60, bg="#b0c4de")
    canvas.pack()
    arc = canvas.create_arc(1, 1, 60, 60, start=0, extent=359, fill="red")

    # Text widgets
    e1 = Text(frame_status, height=5, width=25, 
              font="Arial 10 bold", fg="#50c78f")
    e1.pack()

    e2 = Text(frame_door, height=5, width=44, 
              font=("Arial", 10))
    e2.pack()

    # Start status update
    update_status()
    
    root.mainloop()

#---------------------------------------------MAIN-------------------------------------------
if __name__ == "__main__":
    print("Khởi động hệ thống RFID Door Control...")
    print(f"Thẻ được phép: {AUTHORIZED_CARD_ID}")
    
    p1 = Process(target=main)
    p1.start()
    p2 = Process(target=GUI)
    p2.start()
    p1.join()
    p2.join()