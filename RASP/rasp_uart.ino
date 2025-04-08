#include <Servo.h>  // Thư viện điều khiển servo tiêu chuẩn cho Arduino

Servo myservo;
const int servoPin = 2; // Chân tín hiệu servo (GP2)

// Định nghĩa chân RX, TX cho UART1 (Pico W sử dụng GP0 = TX, GP1 = RX)
#define UART1_RX_PIN 1
#define UART1_TX_PIN 0

// Sử dụng Serial1 thay vì HardwareSerial
#define mySerial Serial1

// Hàm ánh xạ màu sang góc servo (cập nhật lại góc phù hợp)
int mapColorToAngle(String color) {
  if (color == "RED") return 0;
  else if (color == "ORANGE") return 45;
  else if (color == "GREEN") return 90;
  else if (color == "BLUE") return 135;
  else return -1; // Màu không xác định
}

void setup() {
  // Serial monitor debug
  Serial.begin(115200);
  
  // Khởi động UART1 với tốc độ 115200
  mySerial.setRX(UART1_RX_PIN);
  mySerial.setTX(UART1_TX_PIN);
  mySerial.begin(115200);
  
  myservo.attach(servoPin); // Gán chân servo
  Serial.println("Pico W Servo Control Ready");
}

void loop() {
  if (mySerial.available() > 0) {
    // Đọc dữ liệu từ UART (tối đa 20 ký tự)
    char receivedData[20];
    int index = 0;
    
    while (mySerial.available() > 0 && index < 19) {
      char c = mySerial.read();
      if (c == '\n') break; // Kết thúc khi gặp ký tự xuống dòng
      receivedData[index++] = c;
    }
    receivedData[index] = '\0'; // Kết thúc chuỗi

    String color = String(receivedData);
    color.trim();  // Loại bỏ khoảng trắng

    Serial.print("Received color: ");
    Serial.println(color);
    
    int angle = mapColorToAngle(color);
    if (angle >= 0) {
      myservo.write(angle); // Xoay servo
      Serial.print("Moving servo to ");
      Serial.print(angle);
      Serial.println(" degrees.");
    } else {
      Serial.println("Unknown color received.");
    }
  }
  delay(20);  // Delay nhỏ để ổn định
}
