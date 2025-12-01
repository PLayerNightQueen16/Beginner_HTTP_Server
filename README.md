# Minimal HTTP/1.1 Server (Python Sockets)
This project is a fully functional **HTTP/1.1 server built from scratch** using only Python’s standard library (`socket`, `threading`, etc.). No web frameworks and no high-level HTTP libraries were used.

## 🚀 Features Implemented
### Core Requirements
- Manual HTTP parsing (request line, headers, body)
- Supports HTTP methods: **GET**, **POST**, **DELETE**
- Routes:
  - `GET /` — Welcome message
  - `GET /echo?message=<text>` — Echo message
  - `POST /data` — Store JSON
  - `GET /data` — Return all items
  - `GET /data/<id>` — Return item by ID
- Proper HTTP/1.1 responses (status line, headers, body)

### Bonus Features
- Multi-threaded client handling
- Static file server (`/static/<filename>`)
- CORS support
- Keep-alive timeout handling
- Request logging
- Request body size limit (5MB)

## 📁 Project Structure
    .
    ├── server.py
    ├── README.md
    └── static/

## 🏃‍♂️ Running the Server
    python3 server.py

Server runs at:
    http://localhost:8080/

## 🧪 Testing the Server

### GET /
    curl -i http://localhost:8080/

### GET /echo
    curl -i "http://localhost:8080/echo?message=hello"

Expected:
    {"message":"hello"}

### POST /data
    curl -i -X POST http://localhost:8080/data \
      -H "Content-Type: application/json" \
      -d '{"name":"test","value":1}'

### GET /data
    curl -i http://localhost:8080/data

### GET /data/<id>
    curl -i http://localhost:8080/data/1

### DELETE /data/<id>
    curl -i -X DELETE http://localhost:8080/data/1

Expected:
    {"status":"deleted"}

### Static File Test
Create:
    static/hello.txt

Test:
    curl -i http://localhost:8080/static/hello.txt

### 404 Test
    curl -i http://localhost:8080/notfound


## 🧠 Architecture & Design
### Manual HTTP Parsing
- Reads raw TCP bytes
- Detects header termination (`\r\n\r\n`)
- Parses method, path, version, headers
- Reads body using `Content-Length`

### Routing
Routes handled:
- `/`
- `/echo`
- `/data`
- `/data/<id>`
- `/static/<file>`

### In-Memory Data Store
Each POST creates an auto-incremented item.

### Thread-per-Connection
- Each client connection handled on a new thread
- Simple, meets assignment needs

## 🛠 Error Handling
| Code | Meaning |
|------|---------|
| 400 | Bad Request |
| 404 | Route not found |
| 405 | Method not allowed |
| 500 | Internal server error |

## 📌 Limitations
- No HTTPS/TLS
- No database (in-memory only)
- Threading not ideal for massive concurrency
- No chunked encoding

## ✔ Assignment Coverage
| Requirement | Status |
|------------|--------|
| Manual HTTP parsing | ✅ |
| GET / | ✅ |
| GET /echo | ✅ |
| POST /data | ✅ |
| GET /data | ✅ |
| GET /data/<id> | ✅ |
| JSON handling | ✅ |
| Status codes | ✅ |
| Error handling | ✅ |
| Threading | ⭐ |
| Static files | ⭐ |
| CORS | ⭐ |
| DELETE | ⭐ |

## 📜 License
Free to use for learning and academic purposes.
