# Minimal HTTP/1.1 Server (Python Sockets)

This project is a fully functional **HTTP/1.1 server built from scratch** using only Python’s standard library (`socket`, `threading`, etc.).  
No web frameworks and no high-level HTTP libraries were used, as required by the assignment.

---

## 🚀 Features Implemented

### ✅ Core Requirements
- Manual HTTP parsing (request line, headers, body)
- Supports HTTP methods: **GET**, **POST**, **DELETE**
- Required routes:
  - `GET /` — Returns welcome message
  - `GET /echo?message=<text>` — Echoes query parameter
  - `POST /data` — Accepts JSON and stores it in memory
  - `GET /data` — Returns all stored items
  - `GET /data/<id>` — Returns one item by ID
- Correct HTTP/1.1 responses:
  - Status line  
  - Content-Type  
  - Content-Length  
  - Date header  

### ⭐ Bonus Features
- Multi-threaded client handling  
- Static file server (`/static/<filename>`)  
- CORS support  
- Graceful keep-alive timeout  
- Request logging with timestamp + thread info  
- Request body size limit (5MB)  

---

## 📁 Project Structure

.
├── server.py # Main server implementation
├── README.md # Documentation
└── static/ # Static file directory (optional)---

## 🏃‍♂️ Running the Server

python3 server.py
The server starts on:

arduino
Copy code
http://localhost:8080/
Keep this terminal running while you test.

🧪 How to Test the Server
1️⃣ GET /
bash
Copy code
curl -i http://localhost:8080/
2️⃣ GET /echo
bash
Copy code
curl -i "http://localhost:8080/echo?message=hello"
Expected:

json
Copy code
{"message":"hello"}
3️⃣ POST /data
bash
Copy code
curl -i -X POST http://localhost:8080/data \
  -H "Content-Type: application/json" \
  -d '{"name":"test","value":1}'
4️⃣ GET /data
bash
Copy code
curl -i http://localhost:8080/data
5️⃣ GET /data/<id>
bash
Copy code
curl -i http://localhost:8080/data/1
6️⃣ DELETE /data/<id>
bash
Copy code
curl -i -X DELETE http://localhost:8080/data/1
Expected:

json
Copy code
{"status":"deleted"}
7️⃣ Static File Test
Create:

arduino
Copy code
static/hello.txt
Test:

bash
Copy code
curl -i http://localhost:8080/static/hello.txt
8️⃣ 404 Test
bash
Copy code
curl -i http://localhost:8080/notfound
🧠 Architecture & Design Decisions
Manual HTTP Parsing
All parsing is done manually:

Read raw TCP bytes

Detect \r\n\r\n to end headers

Extract:

Method

Path

HTTP version

Headers dictionary

Body using Content-Length

Routing
A simple dispatcher matches:

/

/echo

/data

/data/<id>

/static/<file>

In-Memory Database
Data is stored in a Python list:

python
Copy code
data_store = []
Each POST creates a new object with auto-increment ID.

Thread-Per-Connection
Each new TCP connection runs in a separate thread:

Simple to implement

Enough for this assignment

Gracefully closes idle connections

🛠 Error Handling
The server returns:

Error	Status Code	Meaning
400	Bad Request	malformed request line / invalid JSON
404	Not Found	route does not exist
405	Method Not Allowed	unsupported method for route
500	Internal Server Error	unexpected server crash

📌 Limitations
No HTTPS / TLS

No persistent storage (in-memory only)

Thread-per-connection is not ideal for 100k concurrency

No chunked transfer encoding

✔ Assignment Requirements Coverage
Requirement	Status
Manual HTTP parsing	✅
GET /	✅
GET /echo	✅
POST /data	✅
GET /data	✅
GET /data/<id>	✅
JSON body handling	✅
Custom status codes	✅
Error handling	✅
Threading (bonus)	⭐
Static files (bonus)	⭐
CORS (bonus)	⭐
DELETE route (bonus)	⭐

📜 License
Free to use for learning and academic purposes.
