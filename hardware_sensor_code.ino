#include <WiFi.h>
#include <HTTPClient.h>

// -----------------------------------------
// 1. WiFi Credentials
// -----------------------------------------
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";

// -----------------------------------------
// 2. Your Cloud Run API Endpoint
// -----------------------------------------
const char* serverName = "https://aquasense-ai-149325089156.europe-west1.run.app/api/predict";

// -----------------------------------------
// 3. Sensor Output Pins (ESP32)
// -----------------------------------------
const int pH_Pin = 34;
const int turbidity_pin = 35; 
const int temp_pin = 32;

void setup() {
  Serial.begin(115200);

  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi...");
  while(WiFi.status() != WL_CONNECTED) { 
    delay(500); 
    Serial.print("."); 
  }
  Serial.println("");
  Serial.print("Connected to WiFi network with IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if(WiFi.status() == WL_CONNECTED){
    WiFiClient client;
    HTTPClient http;
    
    // 1. Read Raw Analog Values from your sensors
    int ph_raw = analogRead(pH_Pin);
    int turb_raw = analogRead(turbidity_pin);
    int temp_raw = analogRead(temp_pin);
    
    // 2. Convert Raw Values to Standard Units 
    float ph_level = 7.0 + ((ph_raw - 1800) / 100.0); 
    float turbidity_ntu = turb_raw / 10.0;             
    float temperature_c = (temp_raw / 4095.0) * 330.0;
    
    // Default dissolved oxygen (if you don't have this expensive sensor yet)
    float do_level = 6.5; 
    
    // 3. Create the JSON payload String
    // We only send these 4 physical properties. The AI does the heavy lifting!
    String jsonPayload = "{";
    jsonPayload += "\"ph\": " + String(ph_level) + ", ";
    jsonPayload += "\"do\": " + String(do_level) + ", ";
    jsonPayload += "\"turbidity\": " + String(turbidity_ntu) + ", ";
    jsonPayload += "\"temperature\": " + String(temperature_c);
    jsonPayload += "}";

    // 4. Send the POST Request to the Flask API
    http.begin(client, serverName);
    http.addHeader("Content-Type", "application/json");
    // SECURITY: Replace this key with your actual
    // API key from .env before field deployment.
    // Never commit real keys to version control.
    http.addHeader(
        "X-API-Key",
        "varuna-prod-key-change-this-immediately"
    );

    Serial.println("Sending physical stats to AI Detective...");
    int httpResponseCode = http.POST(jsonPayload);

    if (httpResponseCode > 0) {
      String payload = http.getString();
      Serial.println("The AI has diagnosed the hidden impurity:");
      Serial.println(payload);
    }
    else {
      Serial.print("Error code: ");
      Serial.println(httpResponseCode);
    }
    http.end();
  }
  else {
    Serial.println("WiFi Disconnected");
  }

  // Wait 10 seconds before reading again
  delay(10000); 
}
