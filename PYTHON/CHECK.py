import cv2
import numpy as np

def nothing(x):
    pass

# Sử dụng webcam (đầu vào mặc định là 0)
cap = cv2.VideoCapture(0)

# Tạo các cửa sổ hiển thị
cv2.namedWindow("live transmission", cv2.WINDOW_AUTOSIZE)
cv2.namedWindow("Tracking")

# Tạo trackbar để điều chỉnh giá trị HSV cho vùng cần theo dõi
cv2.createTrackbar("LH", "Tracking", 0, 255, nothing)
cv2.createTrackbar("LS", "Tracking", 0, 255, nothing)
cv2.createTrackbar("LV", "Tracking", 0, 255, nothing)
cv2.createTrackbar("UH", "Tracking", 255, 255, nothing)
cv2.createTrackbar("US", "Tracking", 255, 255, nothing)
cv2.createTrackbar("UV", "Tracking", 255, 255, nothing)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Chuyển đổi không gian màu sang HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Lấy giá trị trackbar để xác định khoảng giá trị HSV dưới và trên
    l_h = cv2.getTrackbarPos("LH", "Tracking")
    l_s = cv2.getTrackbarPos("LS", "Tracking")
    l_v = cv2.getTrackbarPos("LV", "Tracking")
    u_h = cv2.getTrackbarPos("UH", "Tracking")
    u_s = cv2.getTrackbarPos("US", "Tracking")
    u_v = cv2.getTrackbarPos("UV", "Tracking")

    lower_bound = np.array([l_h, l_s, l_v])
    upper_bound = np.array([u_h, u_s, u_v])

    # Tạo mặt nạ theo khoảng HSV đã chọn
    mask = cv2.inRange(hsv, lower_bound, upper_bound)
    res = cv2.bitwise_and(frame, frame, mask=mask)

    # Hiển thị kết quả
    cv2.imshow("live transmission", frame)
    cv2.imshow("mask", mask)
    cv2.imshow("res", res)

    # Nhấn phím 'q' để thoát vòng lặp
    key = cv2.waitKey(5) & 0xFF
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
