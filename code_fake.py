# Masterkey offline test version - By Raspi

import pigpio
import wiegand
import time
import threading
import tkinter as tk
from tkinter import *
from tkinter import ttk
import IO_init
from multiprocessing import Process

# ---------------------- GLOBAL -----------------------
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

IO_init.Init()

# --------------------- MAIN --------------------------
def main():
    global chuoi2, chuoi, dem, GPIO_LOCK_status, IDcard_code

    def callback(bits, value):
        global chuoi, IDcard_code, chuoi2
        try:
            print("bits={} value={}".format(bits, value))
            IDcard_code = value & 0x1FFFF
            print(f"[CARD SCANNED] ID: {IDcard_code}")
            if IDcard_code == 15819:
                chuoi = "OK"
                chuoi2 = chuoi
                print("[ACCESS GRANTED] Test card 15819")
            else:
                chuoi = "NG"
                chuoi2 = chuoi
                print("[ACCESS DENIED] Card not recognized")
        except Exception as e:
            chuoi = None
            print(f"[ERROR] {e}")

    def readWiegand():
        global w, pi
        pi = pigpio.pi()
        w = wiegand.decoder(pi, 20, 21, callback)

    def LOCK_event_detect():
        global GPIO_LOCK_status
        if chuoi == "OK":
            GPIO_LOCK_status = True
        else:
            GPIO_LOCK_status = False

    def count_cuamo():
        global dem_cuamo, dem
        dem_cuamo -= 1
        print("dem cua mo: ", dem_cuamo)
        if dem_cuamo == 0:
            print("Kich relay nhung cua khong mo")
            dem = 2
            chuoi = None

    def LOCK_event_handle():
        global dem_cuamo, dem, chuoi, GPIO_LOCK_status

        sensor = IO_init.GetIOStatus(IO_init.GPIO_Sensor)

        if GPIO_LOCK_status and sensor == 0 and dem == 0:
            IO_init.SetIOOutput(IO_init.GPIO_LOCK, 0)
            dem = 1
            dem_cuamo = 50
            print("State 1: Relay ON")

        elif GPIO_LOCK_status and sensor == 0 and dem == 1:
            count_cuamo()
            print("State 2: Waiting door open")

        elif GPIO_LOCK_status and sensor == 1 and dem == 1:
            dem = 2
            IO_init.SetIOOutput(IO_init.GPIO_LOCK, 1)
            GPIO_LOCK_status = False
            print("State 3: Door opened, relay OFF")

        elif GPIO_LOCK_status and dem == 2 and sensor == 0:
            dem = 0
            chuoi = None
            GPIO_LOCK_status = False
            IO_init.SetIOOutput(IO_init.GPIO_LOCK, 1)
            print("State 4: Door closed again")

        elif not GPIO_LOCK_status:
            dem = 0
            chuoi = None
            IO_init.SetIOOutput(IO_init.GPIO_LOCK, 1)

    try:
        readWiegand()

        # Flash LED to indicate system boot
        for _ in range(3):
            IO_init.SetIOOutput(IO_init.GPIO_Led, 1)
            time.sleep(0.3)
            IO_init.SetIOOutput(IO_init.GPIO_Led, 0)
            time.sleep(0.3)

        while True:
            if IO_init.GetIOStatus(18) == 0:
                if IO_init.GetIOStatus(15) == 0:
                    GPIO_Sensor_ON = False

                LOCK_event_detect()
                LOCK_event_handle()

                print("DEBUG STATUS:")
                print("Sensor:", IO_init.GetIOStatus(IO_init.GPIO_Sensor))
                print("Relay:", IO_init.GetIOStatus(IO_init.GPIO_Led))
                print("chuoi:", chuoi)

                if chuoi and chuoi == chuoi2:
                    chuoi2 = None

                time.sleep(1)
            else:
                IO_init.SetIOOutput(IO_init.GPIO_LOCK, 0)
                time.sleep(15)

    except Exception as e:
        print("[ERROR] Main loop crashed:", e)

    finally:
        print("Cleaning up GPIO...")
        IDcard_code = 0
        IO_init.GPIO.cleanup()
        w.cancel()
        pi.stop()

# ----------------------- GUI --------------------------
def GUI():
    root = Tk()
    root.title("MasterKey Offline")
    root["bg"] = "#b0c4de"
    root.geometry("800x480")

    def change_color():
        if IO_init.GetIOStatus(IO_init.GPIO_Sensor) == 0:
            canvas.itemconfig(arc, fill="red")
        else:
            canvas.itemconfig(arc, fill="green")
        canvas.after(100, change_color)

    def click_start():
        e1.delete("1.0", END)
        e1.insert("1.0", "WELCOME TO MASTERKEY - OFFLINE MODE")
        if IO_init.GetIOStatus(IO_init.GPIO_Sensor) == 0:
            e2.delete("1.0", END)
            e2.insert("1.0", "Door closed. Please scan card.")
        else:
            e2.delete("1.0", END)
            e2.insert("1.0", "Door open. Take key and close.")
        e2.after(1000, click_start)

    # Layout
    Label(root, text="MasterKey", font=("Arial bold", 15), fg="green", bg="#b0c4de").grid(row=0, column=0, columnspan=4)
    Label(root, text="Canon VietNam", font="Courier 8 bold italic", fg="red", bg="#b0c4de").grid(row=3, column=0, sticky=(N, W, S))
    Label(root, text="DEV by TIM Advanced Group!", font=("Arial", 8), fg="blue", bg="#b0c4de").grid(row=3, column=1, columnspan=3, sticky=(N, E, S))

    frame_GUI_status = LabelFrame(root, text="GUI Status", font=("Arial", 9), bg="#b0c4de")
    frame_GUI_status.grid(row=1, column=0, sticky=(N, W, S))

    frame_door_waiting = LabelFrame(root, text="Door Status", font=("Arial", 9), bg="#b0c4de")
    frame_door_waiting.grid(row=1, column=1, columnspan=2, sticky=(N, W, S))

    frame_door_status = LabelFrame(root, text=" ", font=("Arial", 7), bg="#b0c4de")
    frame_door_status.grid(row=1, column=3, sticky=(N, W, S))

    # Door Status Indicator
    canvas = tk.Canvas(frame_door_status, height=60, width=60, bg="#b0c4de")
    canvas.pack()
    arc = canvas.create_arc(1, 1, 60, 60, start=0, extent=359, fill="red")
    change_color()

    # GUI Status
    e1 = Text(frame_GUI_status, height=3, width=25, font="Arial 13 bold", fg="#50c78f")
    e1.pack()

    # Door Status Message
    e2 = Text(frame_door_waiting, height=3, width=44, font=("Arial Italic", 12))
    e2.pack()

    # Start GUI loop
    click_start()
    root.mainloop()

# --------------------- ENTRY POINT --------------------
if __name__ == "__main__":
    p1 = Process(target=main)
    p1.start()
    p2 = Process(target=GUI)
    p2.start()
    p1.join()
    p2.join()
