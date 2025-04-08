import cv2
import numpy as np
import serial
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import pandas as pd
from datetime import datetime

# Các khoảng giá trị HSV cho từng màu (loại bỏ màu VÀNG)
color_ranges = {
    "RED": (np.array([0, 100, 100]), np.array([9, 255, 255])),
    "ORANGE": (np.array([9, 100, 100]), np.array([25, 255, 255])),
    "GREEN": (np.array([45, 100, 100]), np.array([95, 255, 255])),
    "BLUE": (np.array([95, 100, 100]), np.array([120, 255, 255]))
}

# Dictionary lưu số lần phát hiện màu
color_counts = {color: 0 for color in color_ranges.keys()}

# Màu nền cho giao diện đếm màu
display_colors = {
    "RED": "#FFCCCC",
    "ORANGE": "#FFE5CC",
    "GREEN": "#CCFFCC",
    "BLUE": "#CCCCFF"
}

# Kết nối Serial với Raspberry Pi (điều chỉnh cổng nếu cần)
try:
    # Ví dụ: sử dụng cổng COM14 trên Windows, điều chỉnh nếu cần
    rasp_serial = serial.Serial('COM13', 115200, timeout=1)
    rasp_serial.readline()  # Xóa dữ liệu thừa
except Exception as e:
    print("Không thể kết nối Serial:", e)
    rasp_serial = None

# Khởi tạo camera
cap = cv2.VideoCapture(0)

# Biến lưu màu được phát hiện ở frame trước để chỉ đếm khi thay đổi
last_detected_color = None

# Tạo cửa sổ giao diện Tkinter
root = tk.Tk()
root.title("Camera & Color Counter")
root.geometry("800x650")
root.configure(bg="#F0F0F0")

# Khung hiển thị video
video_frame = tk.Frame(root, bg="#000000")
video_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)

lmain = tk.Label(video_frame)
lmain.pack(fill="both", expand=True)

# Khung hiển thị số lượng màu
counter_frame = tk.Frame(root, bg="#F0F0F0")
counter_frame.pack(side="top", fill="x", padx=10, pady=10)

header = tk.Label(counter_frame, text="Color Counter", font=("Helvetica", 16, "bold"), bg="#F0F0F0")
header.pack(pady=5)

color_labels = {}
for color in color_ranges.keys():
    frm = tk.Frame(counter_frame, bg=display_colors[color], padx=10, pady=5)
    frm.pack(side="left", expand=True, fill="both", padx=5, pady=5)
    lbl = tk.Label(frm, text=f"{color}: 0", font=("Helvetica", 14), bg=display_colors[color])
    lbl.pack()
    color_labels[color] = lbl

# Khung chứa các nút điều khiển
button_frame = tk.Frame(root, bg="#F0F0F0")
button_frame.pack(side="bottom", fill="x", padx=10, pady=10)


def reset_counters():
    global color_counts, last_detected_color
    color_counts = {color: 0 for color in color_ranges.keys()}
    last_detected_color = None
    for color, lbl in color_labels.items():
        lbl.config(text=f"{color}: 0")
    print("Reset counters!")


reset_button = tk.Button(button_frame, text="Reset", font=("Helvetica", 14),
                         command=reset_counters, bg="#CCCCCC")
reset_button.pack(side="left", padx=20, pady=5)


def export_to_excel():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"color_counts_{now}.xlsx"

    # Tạo DataFrame dạng 1 dòng với mỗi màu là 1 cột
    df = pd.DataFrame([color_counts])
    try:
        df.to_excel(filename, index=False)
        print(f"Đã lưu file Excel: {filename}")
    except Exception as e:
        print("Lỗi khi ghi Excel:", e)


export_button = tk.Button(button_frame, text="Export to Excel", font=("Helvetica", 14),
                          command=export_to_excel, bg="#99CCFF")
export_button.pack(side="left", padx=20, pady=5)

quit_button = tk.Button(button_frame, text="Quit", font=("Helvetica", 14),
                        command=lambda: on_closing(), bg="#FF9999")
quit_button.pack(side="right", padx=20, pady=5)


def update_frame():
    global last_detected_color
    ret, frame = cap.read()
    if not ret:
        root.after(10, update_frame)
        return

    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    max_area = 0
    max_color = "UNKNOWN"
    max_circle = None

    # Duyệt qua từng màu để tìm vùng có diện tích lớn nhất
    for color, (lower, upper) in color_ranges.items():
        mask = cv2.inRange(hsv_frame, lower, upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            c = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(c)
            if area > max_area:
                max_area = area
                max_color = color
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                max_circle = (int(x), int(y), int(radius))

    # Nếu phát hiện vùng có diện tích đáng kể
    if max_area > 100 and max_circle is not None:
        (x, y, radius) = max_circle
        cv2.circle(frame, (x, y), radius, (0, 255, 0), 2)
        cv2.putText(frame, f"{max_color} ({int(max_area)})", (x - radius, y - radius - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        # Cập nhật số đếm và gửi tín hiệu qua Serial chỉ khi màu thay đổi
        if max_color != last_detected_color:
            color_counts[max_color] += 1
            last_detected_color = max_color
            if rasp_serial:
                # Gửi tín hiệu kèm ký tự xuống dòng (nếu cần) để dễ xử lý trên phía nhận
                signal = f"{max_color}\n"
                rasp_serial.write(signal.encode())
                print("Gửi tín hiệu:", signal.strip())
    else:
        cv2.putText(frame, "No significant color detected", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        last_detected_color = None

    # Cập nhật giao diện số lượng màu
    for color, lbl in color_labels.items():
        lbl.config(text=f"{color}: {color_counts[color]}")

    # Chuyển đổi frame từ BGR sang RGB và hiển thị lên Tkinter
    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(cv2image)
    imgtk = ImageTk.PhotoImage(image=img)
    lmain.imgtk = imgtk
    lmain.configure(image=imgtk)

    # Lặp lại sau 10 ms
    root.after(10, update_frame)


def on_closing():
    cap.release()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)
update_frame()
root.mainloop()
