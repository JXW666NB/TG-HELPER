// ╔══════════════════════════════════════════╗
// ║   TG Helper Robot - TGOS 架构重构版     ║
// ║   适用于 ESP32S3                        ║
// ║   FreeRTOS 多线程 + 状态机驱动          ║
// ╚══════════════════════════════════════════╝

#include <Arduino.h>
#include <WiFi.h>
#include <WebSocketsServer.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ESP32Servo.h>
#include <Preferences.h>
#include <driver/i2s.h>
#include <WiFiUdp.h>
#include <esp_task_wdt.h>

// ========== 硬件引脚 ==========
#define SERVO_LEFT   17
#define SERVO_RIGHT  18
#define SERVO_HEAD   21

#define OLED_SDA     8
#define OLED_SCL     9

#define I2S_WS       4
#define I2S_SD       5
#define I2S_SCK      6

#define I2S_DOUT     7
#define I2S_BCLK     15
#define I2S_LRC      16

#define SCREEN_WIDTH  128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1
#define OLED_ADDR     0x3C

#define I2S_PORT_MIC  I2S_NUM_0
#define I2S_PORT_SPK  I2S_NUM_1
#define I2S_SAMPLE_RATE 16000
#define I2S_BUF_SIZE  1024

#define UDP_DISCOVERY_PORT 8888
#define MIC_THRESHOLD 2000
#define SILENCE_TIMEOUT 2000
#define WAKE_BUF_MS 3000

// ========== TGOS 屏幕状态枚举 ==========
enum DisplayState {
  DISP_OFF = 0,        // 息屏
  DISP_BOOT,           // 开机动画
  DISP_AP_MODE,        // AP配网模式
  DISP_HOME,           // 主页（表情+状态+待机）
  DISP_LISTENING,      // 正在听
  DISP_THINKING,       // AI思考
  DISP_SPEAKING,       // 正在说
  DISP_SELFTEST,       // 自检
  DISP_INFO            // 信息页（IP/状态）
};
volatile DisplayState displayState = DISP_BOOT;
volatile bool displayDirty = true;

// ========== 全局对象 ==========
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
Servo servo17;
Servo servo18;
Servo servo21;
WebSocketsServer webSocket = WebSocketsServer(81);
WiFiUDP udp;
Preferences prefs;

// ========== 状态变量(volatile 跨线程安全) ==========
volatile bool oledReady = false;
volatile bool wifiConnected = false;
volatile bool isRecording = false;
volatile bool isPlaying = false;
volatile bool robotAwake = false;
volatile int volume = 80;
volatile int leftAngle = 90, rightAngle = 90, headAngle = 90;
String currentExpression = "neutral";
String apName = "";
String apIP = "";

// ========== 语音唤醒变量 ==========
volatile float micEnergy = 0;
volatile bool speechActive = false;
unsigned long speechStartMs = 0;
unsigned long speechEndMs = 0;
int16_t* wakeBuf = nullptr;
volatile int wakeBufPos = 0;
volatile bool wakeBufReady = false;
#define WAKE_MAX_SAMPLES (I2S_SAMPLE_RATE * WAKE_BUF_MS / 1000)

// ========== 待机动画 ==========
unsigned long lastAnimMs = 0;
int animInterval = 4000;
int animIndex = 0;

// ========== FreeRTOS 互斥锁 ==========
SemaphoreHandle_t i2sMutex = nullptr;

// ========== 表情位图 ==========
const uint8_t PROGMEM bmp_neutral[] = {
  0b00000000,0b00000000,0b00000000,0b00000000,
  0b00001100,0b00110000,0b00001100,0b00110000,
  0b00000000,0b00000000,0b00000000,0b00000000,
  0b00010000,0b00001000,0b00001000,0b00010000,
  0b00000111,0b11100000,0b00000000,0b00000000,
  0b00000000,0b00000000,0b00000000,0b00000000,
  0b00000000,0b00000000,0b00000000,0b00000000,
  0b00000000,0b00000000,0b00000000,0b00000000
};
const uint8_t PROGMEM bmp_happy[] = {
  0b00000000,0b00000000,0b00000000,0b00000000,
  0b00001100,0b00110000,0b00001100,0b00110000,
  0b00000000,0b00000000,0b00000000,0b00000000,
  0b00001000,0b00010000,0b00010000,0b00001000,
  0b00100000,0b00000100,0b00111111,0b11111100,
  0b00000000,0b00000000,0b00000000,0b00000000,
  0b00000000,0b00000000,0b00000000,0b00000000,
  0b00000000,0b00000000,0b00000000,0b00000000
};
const uint8_t PROGMEM bmp_sad[] = {
  0b00000000,0b00000000,0b00000000,0b00000000,
  0b00001100,0b00110000,0b00001100,0b00110000,
  0b00000000,0b00000000,0b00000000,0b00000000,
  0b00100000,0b00000100,0b00010000,0b00001000,
  0b00001111,0b11110000,0b00000000,0b00000000,
  0b00000000,0b00000000,0b00000000,0b00000000,
  0b00000000,0b00000000,0b00000000,0b00000000,
  0b00000000,0b00000000,0b00000000,0b00000000
};
const uint8_t PROGMEM bmp_listen[] = {
  0b00000000,0b00000000,0b00000000,0b00000000,
  0b00000110,0b01100000,0b00000110,0b01100000,
  0b00000000,0b00000000,0b00000000,0b00000000,
  0b00000100,0b00100000,0b00000100,0b00100000,
  0b00000100,0b00100000,0b00000011,0b11000000,
  0b00000000,0b00000000,0b00000000,0b00000000,
  0b00000000,0b00000000,0b00000000,0b00000000,
  0b00000000,0b00000000,0b00000000,0b00000000
};

// ========== 舵机控制(ESP32Servo) ==========
void setServo(const char* name, int angle) {
  angle = constrain(angle, 0, 180);
  if (strcmp(name, "left") == 0 || strcmp(name, "left_hand") == 0) {
    leftAngle = angle;
    servo17.write(angle);
  } else if (strcmp(name, "right") == 0 || strcmp(name, "right_hand") == 0) {
    rightAngle = angle;
    servo18.write(angle);
  } else if (strcmp(name, "head") == 0) {
    headAngle = angle;
    servo21.write(angle);
  }
}

// ========== OLED绘制 ==========
void drawBitmap(int x, int y, const uint8_t* bmp) {
  display.drawBitmap(x, y, bmp, 16, 16, SSD1306_WHITE);
}

void drawBootLogo() {
  if (!oledReady) return;
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);

  display.setCursor(24, 0);
  display.println("TG HELPER");
  display.setTextSize(2);
  display.setCursor(38, 20);
  display.println("TGOS");
  display.setTextSize(1);
  display.drawRect(10, 42, 108, 6, SSD1306_WHITE);
  display.setCursor(0, 52);
  display.print("v3.0  ESP32-S3");
  display.display();
}

void drawBootBar(int pct) {
  if (!oledReady) return;
  int w = (108 * pct) / 100;
  display.fillRect(11, 43, w, 4, SSD1306_WHITE);
  display.display();
}

void drawOfflineHome() {
  if (!oledReady) return;
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("TG Helper Robot");
  display.setCursor(0, 12);
  display.println("Status:  Offline");
  display.setCursor(0, 24);
  display.println("No WiFi configured");
  display.setCursor(0, 36);
  display.println("----------------");
  display.setCursor(0, 48);
  display.println("Connect to PC");
  display.println("to configure WiFi");
  display.display();
}

void drawHomeFace() {
  if (!oledReady) return;
  display.clearDisplay();
  const uint8_t* bmp = bmp_neutral;
  if (currentExpression == "happy") bmp = bmp_happy;
  else if (currentExpression == "sad") bmp = bmp_sad;

  drawBitmap(56, 8, bmp);
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.print("TG:");
  display.println(currentExpression);
  display.setCursor(0, 30);
  if (wifiConnected) {
    display.print("IP: ");
    display.println(WiFi.localIP());
  } else {
    display.println("WiFi: Offline");
  }
  display.setCursor(0, 48);
  if (isRecording) display.print("[REC]");
  else if (isPlaying) display.print("[TTS]");
  else display.print("[READY]");
  display.display();
}

void drawListeningFace() {
  if (!oledReady) return;
  display.clearDisplay();
  drawBitmap(56, 8, bmp_listen);
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(">>> Listening <<<");
  display.setCursor(0, 30);
  display.println("I'm listening...");
  display.setCursor(0, 48);
  display.print("[REC]");
  display.display();
}

void drawThinkingFace() {
  if (!oledReady) return;
  static int dots = 0;
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(">>> Thinking <<<");
  display.setCursor(24, 28);
  dots = (dots + 1) % 4;
  display.print("Thinking");
  for (int i = 0; i < dots; i++) display.print(".");
  display.setCursor(0, 48);
  display.print("[AI]");
  display.display();
}

void drawSpeakingFace() {
  if (!oledReady) return;
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(">>> Speaking <<<");
  display.setCursor(0, 16);
  display.println("Replying...");
  display.setCursor(0, 48);
  display.print("[TTS]");
  display.display();
}

void drawAPModeScreen() {
  if (!oledReady) return;
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(">>> AP MODE <<<");
  display.setCursor(0, 12);
  display.print("SSID: ");
  display.println(apName);
  display.setCursor(0, 22);
  display.print("IP:   ");
  display.println(apIP);
  display.setCursor(0, 36);
  display.println("1. Connect this WiFi");
  display.setCursor(0, 48);
  display.println("2. Open TG HELPER");
  display.setCursor(0, 56);
  display.println("3. Config WiFi");
  display.display();
}

void drawSelfTest() {
  if (!oledReady) return;
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(10, 16);
  display.println(">>> SELF TEST <<<");
  display.setCursor(10, 36);
  display.println("Testing motors...");
  display.setCursor(10, 48);
  display.println("Please wait...");
  display.display();
}

// ========== 显示任务 ==========
void taskDisplay(void* param) {
  unsigned long lastThinkTick = 0;
  const unsigned long thinkInterval = 500;

  while (1) {
    DisplayState currentState = displayState;

    switch (currentState) {
      case DISP_BOOT:
        // 由boot流程控制
        break;

      case DISP_AP_MODE:
        drawAPModeScreen();
        vTaskDelay(pdMS_TO_TICKS(2000));
        break;

      case DISP_HOME:
        if (displayDirty) {
          if (!wifiConnected)
            drawOfflineHome();
          else
            drawHomeFace();
          displayDirty = false;
        }
        // 待机动画（独立于主循环）
        break;

      case DISP_LISTENING:
        drawListeningFace();
        vTaskDelay(pdMS_TO_TICKS(200));
        break;

      case DISP_THINKING:
        if (millis() - lastThinkTick > thinkInterval) {
          lastThinkTick = millis();
          drawThinkingFace();
        }
        vTaskDelay(pdMS_TO_TICKS(200));
        break;

      case DISP_SPEAKING:
        drawSpeakingFace();
        vTaskDelay(pdMS_TO_TICKS(200));
        break;

      case DISP_SELFTEST:
        drawSelfTest();
        vTaskDelay(pdMS_TO_TICKS(500));
        break;

      case DISP_INFO:
        drawHomeFace();
        vTaskDelay(pdMS_TO_TICKS(3000));
        displayState = DISP_HOME;
        break;

      case DISP_OFF:
        display.clearDisplay();
        display.display();
        vTaskDelay(pdMS_TO_TICKS(500));
        break;
    }

    vTaskDelay(pdMS_TO_TICKS(100));
  }
}

// ========== 网络任务(UDP + 音频发送) ==========
void taskNetwork(void* param) {
  while (1) {
    int sz = udp.parsePacket();
    if (sz) {
      char buf[256];
      int len = udp.read(buf, 255);
      if (len > 0) {
        buf[len] = 0;
        if (String(buf) == "DISCOVER_TG_ROBOT") {
          StaticJsonDocument<512> doc;
          doc["type"] = "robot_discovered";
          doc["name"] = "TG-Helper";
          doc["ip"] = WiFi.localIP().toString();
          doc["mac"] = WiFi.macAddress();
          doc["version"] = "3.0";
          String resp;
          serializeJson(doc, resp);
          udp.beginPacket(udp.remoteIP(), udp.remotePort());
          udp.write((const uint8_t*)resp.c_str(), resp.length());
          udp.endPacket();
        }
      }
    }

    if (isRecording && robotAwake) {
      static int16_t micBuf[I2S_BUF_SIZE];
      size_t bytesRead = 0;
      if (xSemaphoreTake(i2sMutex, pdMS_TO_TICKS(10)) == pdTRUE) {
        i2s_read(I2S_PORT_MIC, micBuf, sizeof(micBuf), &bytesRead, 10 / portTICK_PERIOD_MS);
        xSemaphoreGive(i2sMutex);
      }
      if (bytesRead > 0) {
        StaticJsonDocument<128> hdr;
        hdr["type"] = "voice_data";
        String hdrStr;
        serializeJson(hdr, hdrStr);
        hdrStr += "\n";
        webSocket.broadcastTXT(hdrStr);
        webSocket.broadcastBIN((uint8_t*)micBuf, bytesRead);
      }
    }

    vTaskDelay(pdMS_TO_TICKS(20));
  }
}

// ========== 语音唤醒任务 ==========
void taskVoice(void* param) {
  unsigned long lastEnergyMs = 0;

  // 分配唤醒缓冲区
  wakeBuf = (int16_t*)malloc(WAKE_MAX_SAMPLES * sizeof(int16_t));

  while (1) {
    if (!oledReady || !wakeBuf) {
      vTaskDelay(pdMS_TO_TICKS(500));
      continue;
    }

    // 能量检测（每100ms）- 仅在PC已连接时工作
    unsigned long now = millis();
    if (now - lastEnergyMs >= 100 && displayState == DISP_HOME && robotAwake) {
      lastEnergyMs = now;
      static int16_t energySamples[512];
      size_t bytesRead = 0;
      if (xSemaphoreTake(i2sMutex, pdMS_TO_TICKS(10)) == pdTRUE) {
        i2s_read(I2S_PORT_MIC, energySamples, sizeof(energySamples), &bytesRead, 1 / portTICK_PERIOD_MS);
        xSemaphoreGive(i2sMutex);
      }
      if (bytesRead > 0) {
        int n = bytesRead / 2;
        float sum = 0;
        for (int i = 0; i < n; i++) sum += abs(energySamples[i]);
        micEnergy = sum / n;

        // 语音检测
        if (!speechActive && micEnergy > MIC_THRESHOLD) {
          speechActive = true;
          speechStartMs = now;
          wakeBufPos = 0;
          memset(wakeBuf, 0, WAKE_MAX_SAMPLES * sizeof(int16_t));
          Serial.printf("[Voice] 语音检测 (energy=%.1f)\n", micEnergy);
        }
        if (speechActive && micEnergy > MIC_THRESHOLD) {
          speechEndMs = now;
        }
      }
    }

    // 填充唤醒缓冲区
    if (speechActive && displayState == DISP_HOME) {
      static int16_t capBuf[I2S_BUF_SIZE];
      size_t bytesRead = 0;
      if (xSemaphoreTake(i2sMutex, pdMS_TO_TICKS(10)) == pdTRUE) {
        i2s_read(I2S_PORT_MIC, capBuf, sizeof(capBuf), &bytesRead, 10 / portTICK_PERIOD_MS);
        xSemaphoreGive(i2sMutex);
      }
      int samples = bytesRead / 2;
      for (int i = 0; i < samples && wakeBufPos < WAKE_MAX_SAMPLES; i++) {
        wakeBuf[wakeBufPos++] = capBuf[i];
      }
    }

    // 静默检测
    if (speechActive && (now - speechEndMs) > SILENCE_TIMEOUT) {
      unsigned long dur = speechEndMs - speechStartMs;
      Serial.printf("[Voice] 语音结束 (dur=%lums, samples=%d)\n", dur, wakeBufPos);
      speechActive = false;

      if (wakeBufPos > WAKE_MAX_SAMPLES / 2) {
        wakeBufReady = true;

        // 发送唤醒数据
        StaticJsonDocument<128> hdr;
        hdr["type"] = "voice_wake";
        hdr["samples"] = wakeBufPos;
        hdr["rate"] = I2S_SAMPLE_RATE;
        String hdrStr;
        serializeJson(hdr, hdrStr);
        hdrStr += "\n";
        webSocket.broadcastTXT(hdrStr);

        int offset = 0;
        while (offset < wakeBufPos) {
          int chunk = min(1024, wakeBufPos - offset);
          webSocket.broadcastBIN((uint8_t*)(wakeBuf + offset), chunk * 2);
          offset += chunk;
          delay(5);
        }

        // 进入聆听状态
        robotAwake = true;
        displayState = DISP_LISTENING;
        displayDirty = true;
        isRecording = true;
        Serial.println("[Voice] 进入聆听模式");
      } else {
        wakeBufPos = 0;
        Serial.println("[Voice] 缓冲区太小，忽略");
      }
    }

    vTaskDelay(pdMS_TO_TICKS(50));
  }
}

// ========== 待机动画 ==========
void performIdleAnimation() {
  if (!oledReady) return;

  const char* exps[] = {"neutral", "happy", "neutral", "happy"};
  currentExpression = exps[animIndex % 4];

  int act = random(0, 4);
  switch (act) {
    case 0: setServo("head", random(70, 110)); delay(200); setServo("head", 90); break;
    case 1: setServo("left", random(75, 105)); delay(200); setServo("left", 90); break;
    case 2: setServo("right", random(75, 105)); delay(200); setServo("right", 90); break;
    case 3: setServo("head", 120); delay(500); setServo("head", 60); delay(500); setServo("head", 90); break;
  }
  animIndex++;
  displayDirty = true;
}

// ========== I2S初始化 ==========
void setupI2S() {
  i2s_config_t mic_cfg = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = I2S_SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = I2S_BUF_SIZE,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };
  i2s_driver_install(I2S_PORT_MIC, &mic_cfg, 0, NULL);
  i2s_pin_config_t mic_pin = { .bck_io_num = I2S_SCK, .ws_io_num = I2S_WS, .data_out_num = I2S_PIN_NO_CHANGE, .data_in_num = I2S_SD };
  i2s_set_pin(I2S_PORT_MIC, &mic_pin);

  i2s_config_t spk_cfg = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = I2S_SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = I2S_BUF_SIZE,
    .use_apll = false,
    .tx_desc_auto_clear = true,
    .fixed_mclk = 0
  };
  i2s_driver_install(I2S_PORT_SPK, &spk_cfg, 0, NULL);
  i2s_pin_config_t spk_pin = { .bck_io_num = I2S_BCLK, .ws_io_num = I2S_LRC, .data_out_num = I2S_DOUT, .data_in_num = I2S_PIN_NO_CHANGE };
  i2s_set_pin(I2S_PORT_SPK, &spk_pin);

  Serial.println("[I2S] OK");
}

// ========== 舵机初始化 ==========
void setupServos() {
  Serial.println("[Servo] 初始化...");

  servo17.setPeriodHertz(50);
  servo17.attach(SERVO_LEFT, 500, 2500);
  servo17.write(90);
  delay(100);

  servo18.setPeriodHertz(50);
  servo18.attach(SERVO_RIGHT, 500, 2500);
  servo18.write(90);
  delay(100);

  servo21.setPeriodHertz(50);
  servo21.attach(SERVO_HEAD, 500, 2500);
  servo21.write(90);

  Serial.println("[Servo] OK");
}

// ========== OLED初始化 ==========
void setupOLED() {
  Wire.begin(OLED_SDA, OLED_SCL);
  for (int i = 0; i < 3; i++) {
    if (display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
      oledReady = true;
      break;
    }
    delay(50);
  }
  if (oledReady) {
    display.clearDisplay();
    display.display();
    display.setTextColor(SSD1306_WHITE);
    Serial.println("[OLED] OK");
  } else {
    Serial.println("[OLED] FAIL");
  }
}

// ========== WiFi连接 ==========
void connectWiFi() {
  WiFi.setSleep(false);

  prefs.begin("wifi", true);
  String ssid = prefs.getString("ssid", "");
  String pass = prefs.getString("password", "");
  unsigned int fails = prefs.getUInt("fail_count", 0);
  prefs.end();

  if (fails >= 3 && ssid.length() > 0) {
    prefs.begin("wifi", false);
    prefs.clear();
    prefs.end();
    ssid = "";
    pass = "";
  }

  if (ssid.length() > 0) {
    Serial.printf("[WiFi] %s ...\n", ssid.c_str());
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid.c_str(), pass.c_str());
    unsigned long t = millis();
    while (WiFi.status() != WL_CONNECTED && (millis() - t) < 15000) {
      delay(500);
      Serial.print(".");
    }
    if (WiFi.status() == WL_CONNECTED) {
      Serial.printf("\n[WiFi] IP: %s\n", WiFi.localIP().toString().c_str());
      prefs.begin("wifi", false);
      prefs.putUInt("fail_count", 0);
      prefs.end();
      wifiConnected = true;
      return;
    }
    fails++;
    Serial.println("\n[WiFi] FAIL");
    prefs.begin("wifi", false);
    prefs.putUInt("fail_count", fails);
    prefs.end();
    WiFi.disconnect(true);
    delay(100);
  }

  WiFi.mode(WIFI_AP);
  uint64_t chip = ESP.getEfuseMac();
  apName = "TG-Robot-" + String((uint32_t)(chip % 10000));
  WiFi.softAP(apName.c_str());
  apIP = WiFi.softAPIP().toString();
  Serial.printf("[WiFi] AP: %s / %s\n", apName.c_str(), apIP.c_str());
  wifiConnected = false;
}

// ========== WebSocket事件 ==========
void onWsEvent(uint8_t num, WStype_t type, uint8_t* payload, size_t len) {
  switch (type) {
    case WStype_DISCONNECTED:
      Serial.printf("[WS] #%u offline\n", num);
      robotAwake = false;
      break;
    case WStype_CONNECTED:
      Serial.printf("[WS] #%u online\n", num);
      robotAwake = true;
      {
        StaticJsonDocument<128> doc;
        doc["type"] = "connected";
        doc["name"] = "TG-Helper";
        doc["version"] = "3.0";
        String r; serializeJson(doc, r);
        webSocket.sendTXT(num, r);
      }
      break;
    case WStype_TEXT: {
      StaticJsonDocument<512> doc;
      if (deserializeJson(doc, payload)) return;
      String cmd = doc["type"];

      if (cmd == "servo_control") {
        setServo(doc["servo"], doc["angle"]);
      } else if (cmd == "set_expression") {
        currentExpression = doc["expression"].as<String>();
        displayDirty = true;
      } else if (cmd == "start_recording") {
        isRecording = true;
        displayState = DISP_LISTENING;
      } else if (cmd == "stop_recording") {
        isRecording = false;
        displayState = DISP_HOME;
        displayDirty = true;
      } else if (cmd == "wake_detected") {
        displayState = DISP_LISTENING;
        isRecording = true;
      } else if (cmd == "start_thinking") {
        displayState = DISP_THINKING;
      } else if (cmd == "start_speaking") {
        displayState = DISP_SPEAKING;
      } else if (cmd == "done_speaking") {
        displayState = DISP_HOME;
        displayDirty = true;
      } else if (cmd == "perform_action") {
        String act = doc["action"];
        if (act == "wave_left") {
          for (int i = 0; i < 3; i++) { setServo("left", 45); delay(300); setServo("left", 135); delay(300); }
          setServo("left", 90);
        } else if (act == "wave_right") {
          for (int i = 0; i < 3; i++) { setServo("right", 45); delay(300); setServo("right", 135); delay(300); }
          setServo("right", 90);
        } else if (act == "nod") {
          for (int i = 0; i < 3; i++) { setServo("head", 60); delay(300); setServo("head", 120); delay(300); }
          setServo("head", 90);
        }
      } else if (cmd == "self_test") {
        displayState = DISP_SELFTEST;
        setServo("left", 45); delay(600); setServo("left", 135); delay(600); setServo("left", 90);
        delay(200);
        setServo("right", 45); delay(600); setServo("right", 135); delay(600); setServo("right", 90);
        delay(200);
        setServo("head", 60); delay(600); setServo("head", 120); delay(600); setServo("head", 90);
        delay(200);
        displayState = DISP_HOME; displayDirty = true;
        StaticJsonDocument<128> r; r["type"] = "self_test_complete"; r["status"] = "ok";
        String rs; serializeJson(r, rs); webSocket.broadcastTXT(rs);
      } else if (cmd == "set_wifi") {
        prefs.begin("wifi", false);
        prefs.putString("ssid", doc["ssid"].as<String>());
        prefs.putString("password", doc["password"].as<String>());
        prefs.putUInt("fail_count", 0);
        prefs.end();
        StaticJsonDocument<128> r; r["type"] = "wifi_saved"; r["message"] = "OK, restarting...";
        String rs; serializeJson(r, rs); webSocket.sendTXT(num, rs);
        delay(500); ESP.restart();
      } else if (cmd == "scan_wifi") {
        int n = WiFi.scanNetworks();
        StaticJsonDocument<1024> r; r["type"] = "wifi_scanned";
        JsonArray arr = r.createNestedArray("networks");
        for (int i = 0; i < n && i < 20; i++) {
          JsonObject o = arr.createNestedObject();
          o["ssid"] = WiFi.SSID(i); o["rssi"] = WiFi.RSSI(i);
          o["enc"] = WiFi.encryptionType(i) == WIFI_AUTH_OPEN ? "open" : "secure";
        }
        WiFi.scanDelete();
        String rs; serializeJson(r, rs); webSocket.sendTXT(num, rs);
      } else if (cmd == "get_status") {
        StaticJsonDocument<256> r; r["type"] = "status";
        r["connected"] = robotAwake; r["recording"] = isRecording;
        r["volume"] = volume; r["wifi"] = wifiConnected;
        String rs; serializeJson(r, rs); webSocket.sendTXT(num, rs);
      } else if (cmd == "set_volume") {
        volume = doc["volume"];
      }
      break;
    }
    case WStype_BIN:
      isPlaying = true;
      displayState = DISP_SPEAKING;
      {
        size_t written = 0;
        if (xSemaphoreTake(i2sMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
          i2s_write(I2S_PORT_SPK, payload, len, &written, portMAX_DELAY);
          xSemaphoreGive(i2sMutex);
        }
      }
      isPlaying = false;
      displayState = DISP_HOME;
      displayDirty = true;
      break;
  }
}

// ========== 串口命令 ==========
void checkSerial() {
  static String cmd;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      cmd.trim(); cmd.toLowerCase();
      if (cmd == "reset_wifi" || cmd == "clear_wifi") {
        prefs.begin("wifi", false); prefs.clear(); prefs.end();
        Serial.println("[Serial] WiFi cleared, rebooting...");
        delay(1000); ESP.restart();
      } else if (cmd == "help") {
        Serial.println("reset_wifi / clear_wifi - Clear WiFi & reboot");
      }
      cmd = "";
    } else { cmd += c; }
  }
}

// ========== 主初始化 ==========
void setup() {
  Serial.begin(9600);
  delay(100);
  Serial.println("\n=== TG Helper Robot - TGOS v3.0 ===");

  // 禁用看门狗
  esp_task_wdt_deinit();

  // 1. OLED 先初始化
  setupOLED();
  if (oledReady) {
    drawBootLogo();
  }

  // 2. WiFi 连接（允许离线启动）
  connectWiFi();
  if (oledReady) {
    for (int i = 25; i <= 100; i += 25) { drawBootBar(i); delay(200); }
  }

  // 3. 外围初始化
  setupServos();
  setupI2S();
  if (oledReady) { drawBootBar(100); delay(500); }

  // 4. 网络服务（等待TCP/IP栈就绪）
  delay(1000);
  Serial.println("[WiFi] 启动WebSocket服务器...");
  webSocket.begin();
  webSocket.onEvent(onWsEvent);
  Serial.printf("[WiFi] WebSocket端口: 81, IP: %s\n", WiFi.localIP().toString().c_str());
  udp.begin(UDP_DISCOVERY_PORT);
  Serial.println("[WiFi] UDP发现端口: 8888");

  // 5. 互斥锁
  i2sMutex = xSemaphoreCreateMutex();

  // 6. 启动 FreeRTOS 任务
  xTaskCreatePinnedToCore(taskDisplay, "Display", 4096, NULL, 2, NULL, 1);
  xTaskCreatePinnedToCore(taskNetwork, "Network", 4096, NULL, 2, NULL, 0);
  xTaskCreatePinnedToCore(taskVoice,   "Voice",   4096, NULL, 3, NULL, 0);

  // 7. 根据WiFi状态设置初始界面
  if (wifiConnected) {
    displayState = DISP_HOME;
  } else if (WiFi.getMode() == WIFI_AP) {
    displayState = DISP_AP_MODE;
  } else {
    displayState = DISP_HOME;  // 离线也能进主页
  }
  displayDirty = true;
  Serial.println("[System] READY");
}

// ========== 主循环 ==========
void loop() {
  webSocket.loop();

  checkSerial();

  if (displayState == DISP_HOME && wifiConnected) {
    unsigned long now = millis();
    if (now - lastAnimMs >= animInterval) {
      lastAnimMs = now;
      performIdleAnimation();
      animInterval = random(3000, 7000);
    }
  }

  delay(5);
}
