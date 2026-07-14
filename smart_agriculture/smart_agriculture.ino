#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

#include <DHT.h>

#define DHTPIN 5       // GPIO pin connected to DHT data pin
#define DHTTYPE DHT11   // Change to DHT22 if using that

DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "vivo Y100A";
const char* password = "Aditya";

String serverName = "http://10.201.242.194:5000/";


void setup() {
  Serial.begin(9600);


  pinMode(27,INPUT);  //// MQ135 sensor
  pinMode(13,OUTPUT); // FAN relay
  digitalWrite(13,HIGH);


  pinMode(33,INPUT); /// LDR value
  pinMode(12,OUTPUT);
  digitalWrite(12,HIGH); //// LIGHT bulb relay


  pinMode(4,INPUT);  //// Soil mositure sensor value
  pinMode(2, OUTPUT);
  digitalWrite(2, HIGH); // Relay PUMP (Active LOW type)
  Serial.println("Relay Test Starting...");

  dht.begin(); /// DHT sensor

  // --- Connect to WiFi ---
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ Connected to WiFi!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
   // Read temperature and humidity
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature(); // Celsius

  // Check if reading failed
    Serial.print("Temperature: ");
    Serial.print(temperature);
    Serial.print(" °C  |  Humidity: ");
    Serial.print(humidity);
    Serial.println(" %");
  


  int light=digitalRead(33);
  light=!light;
  Serial.print("Light status-");
  Serial.println(light);
  if(light==0){
    digitalWrite(12,LOW); // Turn relay ON  
  }
  else {
    digitalWrite(12,HIGH);
  }



  int moist= analogRead(4);
  moist=map(moist,2900,400,0,100);
  Serial.print("Soil Moisture-");
  Serial.println(moist);
  if(moist<40){digitalWrite(2,LOW);}
  else{digitalWrite(2,HIGH);}



  int co2 = analogRead(27);
  co2=map(co2,100,960,0,100);
  Serial.print("Co2-");
  Serial.println(co2);
  if(co2>31 || temperature>28){digitalWrite(13,LOW);}
  else{digitalWrite(13,HIGH);}

  // --- Send to Flask Server ---
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");

    // Create JSON payload
    StaticJsonDocument<200> doc;
    doc["temperature"] = temperature;
    doc["humidity"] = humidity;
    doc["soil_moisture"] = moist;
    doc["light"] = light;
    doc["co2"] = co2;

    String jsonData;
    serializeJson(doc, jsonData);

    int httpResponseCode = http.POST(jsonData);

    if (httpResponseCode > 0) {
      Serial.println("✅ Data sent to Flask: " + jsonData);
    } else {
      Serial.print("❌ Error sending data: ");
      Serial.println(httpResponseCode);
    }
    http.end();
  }



  delay(3000);                   // Wait 2 seconds
}