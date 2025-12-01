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

### 404 Test
    curl -i http://localhost:8080/notfound

## ✨ Bonus Features

### DELETE /data/<id>
    curl -i -X DELETE http://localhost:8080/data/1

Expected:
    {"status":"deleted"}

### Static File Test
Create:

    static/hello.txt

Test:

    curl -i http://localhost:8080/static/hello.txt

Expected Result:

    HTTP/1.1 200 OK
    <headers...>

    hello world

### CORS (Cross-Origin Resource Sharing) 
This server sets permissive CORS headers on responses:

  ```
  Access-Control-Allow-Origin: *
  Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
  Access-Control-Allow-Headers: Content-Type, Authorization
  ```

**Quick preflight test (curl OPTIONS) - Simulate a browser preflight:**
```
curl -i -X OPTIONS http://localhost:8080/data \
  -H "Origin: http://example.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"
```

## Threading / Concurrency Tests
This server uses a thread-per-connection model (`threading.Thread`).
These tests verify concurrency and the safety of the in-memory data store.

> **Note:** Run server in one terminal and tests in another.

**Quick Smoke Test — 50 Parallel GET Requests**
```
seq 1 50 | xargs -n1 -P20 -I{} \
curl -s -o /dev/null -w "%{http_code} " "http://localhost:8080/"
echo
```

Expected: 
A sequence of `200` codes — one per request.


**200 Parallel GET Requests**
```
seq 1 200 | xargs -n1 -P50 -I{} \
curl -s -o /dev/null -w "%{http_code} " "http://localhost:8080/"
echo
```

**Concurrent POST Requests (Thread-Safe Data Store)**
```
seq 1 50 | xargs -n1 -P20 -I{} \
curl -s -X POST http://localhost:8080/data \
  -H "Content-Type: application/json" \
  -d "{\"index\":{}}"
```

Then verify the count:

```
curl -s http://localhost:8080/data | jq 'length'
```

Expected:
```
50
```

Expected:
- HTTP/1.1 204 No Content
- Access-Control-Allow-origin: *
- Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
- Access-Control-Allow-Headers: Content-Ty Authorization

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
