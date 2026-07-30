# gRPC Authentication Guide

## Two Layers of Security

Your gRPC service uses **two separate authentication mechanisms** that work at different layers:

### 1. **mTLS (Mutual TLS) - Transport Layer** 🔒

**What it is:**

- Uses SSL/TLS certificates (like HTTPS for websites)
- Encrypts the connection between client and server
- Verifies both parties have valid certificates

**Files:**

- `server.crt` + `server.key` - Server's certificate
- `client.crt` + `client.key` - Client's certificate  
- `ca.crt` - Certificate Authority (both trust this)

**Configuration:**

- `GRPC_TLS_ENABLED=true` - Enable TLS encryption (with or without client certificates)

**When to use:**

- Production: Encrypts data in transit

- Prevents man-in-the-middle attacks
- Ensures connection is encrypted

**For Postman:**

- If TLS is enabled, Postman needs the CA certificate
- Or disable TLS for development: `GRPC_TLS_ENABLED=false`

---

### 2. **JWT Bearer Tokens - Application Layer** 🎫

**What it is:**

- JSON Web Tokens sent in HTTP headers
- Contains service identity and permissions
- Verifies WHO is calling and WHAT they can do

**Token contains:**

- Service name (e.g., "ehr_patient")
- Roles (e.g., ["admin", "reader", "writer"])
- Expiration time
- Issuer and audience

**How to generate:**

```bash
make generate-grpc-token
# or
python manage.py generate_grpc_token
```

**For Postman:**

- Add to Metadata tab: Key: `authorization`, Value: `Bearer <your-token>`

**Configuration:**

- `GRPC_AUTH_ENABLED=true` - Enable JWT authentication
- `SERVICE_TOKEN_SECRET` - Secret to sign tokens
- `SERVICE_TOKEN_AUDIENCE` - Expected audience
- `SERVICE_TOKEN_ISSUER` - Expected issuer

---

## How They Work Together

```
┌─────────────────────────────────────────────────┐
│  Client (Postman)                               │
├─────────────────────────────────────────────────┤
│  1. JWT Token in Header                         │
│     Authorization: Bearer <token>               │
│                                                  │
│  2. TLS Certificate (if enabled)                 │
│     - Client presents: client.crt               │
│     - Server verifies with: ca.crt              │
└─────────────────────────────────────────────────┘
         ↓
    [Encrypted Connection (if TLS enabled)]
         ↓
┌─────────────────────────────────────────────────┐
│  Server (Your gRPC Service)                     │
├─────────────────────────────────────────────────┤
│  1. Verify TLS Certificate (if enabled)         │
│     - Check client.crt is valid                 │
│     - Extract CN from certificate               │
│                                                  │
│  2. Verify JWT Token (if auth enabled)          │
│     - Check token signature                     │
│     - Verify expiration                         │
│     - Extract service identity & roles           │
│                                                  │
│  3. Cross-verify (if both enabled)              │
│     - Certificate CN must match JWT service     │
└─────────────────────────────────────────────────┘
```

---

## Configuration Scenarios

### Scenario 1: Development (No Security)

```bash
GRPC_TLS_ENABLED=false
GRPC_AUTH_ENABLED=false
```

- ✅ No certificates needed
- ✅ No tokens needed
- ✅ Easiest for testing
- ❌ Not secure

### Scenario 2: Testing Authentication (JWT Only)

```bash
GRPC_TLS_ENABLED=false
GRPC_AUTH_ENABLED=true
```

- ✅ Test JWT authentication
- ✅ No certificates needed
- ✅ Use tokens in Postman
- ⚠️ Connection not encrypted (dev only)

### Scenario 3: Testing TLS (mTLS Only)

```bash
GRPC_TLS_ENABLED=true
GRPC_AUTH_ENABLED=false
```

- ✅ Test certificate authentication
- ✅ Encrypted connection
- ✅ Postman needs CA certificate
- ⚠️ No JWT verification

### Scenario 4: Production (Both Enabled)

```bash
GRPC_TLS_ENABLED=true
GRPC_AUTH_ENABLED=true
```

- ✅ Maximum security
- ✅ Encrypted connection (mTLS)
- ✅ Application-level auth (JWT)
- ✅ Both must match

**Postman Setup for Scenario 4:**

1. **Configure TLS:**
   - Go to Postman Settings → Certificates
   - Add Client Certificate:
     - Host: `localhost:50054`
     - CRT file: `certs/client.crt`
     - Key file: `certs/client.key`
   - Add CA Certificate:
     - CA Cert: `certs/ca.crt`

2. **Configure JWT Token:**
   - Generate token: `make generate-grpc-token`
   - In Postman gRPC request Metadata tab:
     - Key: `authorization`
     - Value: `Bearer <your-token>`

3. **Important: Certificate CN must match JWT service name**
   - The client certificate's Common Name (CN) must match the service name in the JWT token
   - If they don't match, set `GRPC_REQUIRE_CERT_JWT_MATCH=false` in `.env` for testing
   - Check certificate CN: `openssl x509 -in certs/client.crt -noout -subject`
   - Check JWT service name: Decode the token at jwt.io

4. **Server URL:**
   - Use: `localhost:50054` (no `http://`)
   - Enable TLS/SSL in Postman

---

## Quick Reference

### Environment Variables (You Only Need 2!)

**Only 2 variables control authentication:**

1. **`GRPC_TLS_ENABLED`** - Controls TLS encryption
   - `true` = Enable TLS (encrypted connection)
   - `false` = No TLS (insecure, dev only)

2. **`GRPC_AUTH_ENABLED`** - Controls JWT token authentication
   - `true` = Require JWT bearer token
   - `false` = No JWT required

**That's it!** You don't need `GRPC_REQUIRE_CLIENT_AUTH` - it's not actually used in the code.

### Certificates (mTLS)

- **Purpose**: Encrypt connection, verify identity at transport layer
- **Files**: `server.crt`, `server.key`, `client.crt`, `client.key`, `ca.crt`
- **Config**: `GRPC_TLS_ENABLED=true`
- **Generate**: `./protos/ehr_protos/scripts/generate_tls_certs.sh certs/`
- **Note**: If `GRPC_TLS_CA_FILE` is provided, the server will verify client certificates (mTLS)

### Tokens (JWT)

- **Purpose**: Verify service identity and permissions at application layer
- **Generate**: `make generate-grpc-token`
- **Config**: `GRPC_AUTH_ENABLED=true`
- **Use in Postman**: Metadata tab → `authorization: Bearer <token>`

---

## For Postman Testing

**Recommended for development:**

```bash
# .env
GRPC_TLS_ENABLED=false      # No certificates needed
GRPC_AUTH_ENABLED=true      # Test JWT authentication
```

**Steps:**

1. Generate token: `make generate-grpc-token`
2. Copy the token
3. In Postman gRPC request:
   - Server URL: `localhost:50054`
   - Metadata tab → Add: Key: `authorization`, Value: `Bearer <token>`
4. Import proto files manually (reflection disabled)

---

## Token Management & Refresh

### How Token Refresh Works

**Each service manages its own tokens** - there's no central token server or automatic refresh.

**Token Lifecycle:**

1. **Service generates token** when it needs to call another service
2. **Token expires** after TTL (default: 1 hour, configurable)
3. **Service regenerates token** when expired or before expiration

**Current Implementation:**

- Services generate tokens **on-demand** using `_generate_service_token()`
- Tokens are **short-lived** (recommended: 5 minutes to 1 hour)
- **No automatic refresh** - service must regenerate when needed

**Best Practices:**

1. **Generate tokens just before use** (not store long-term)
2. **Cache tokens briefly** (e.g., 5 minutes) to avoid regenerating for every call
3. **Regenerate before expiration** (e.g., if token expires in 1 hour, regenerate at 50 minutes)
4. **Handle token expiration errors** - catch `UNAUTHENTICATED` errors and regenerate

**Example Token Management Pattern:**

```python
# In your service client code
class ServiceClient:
    def __init__(self):
        self._token = None
        self._token_expires = None
    
    def _get_token(self):
        """Get valid token, regenerating if expired."""
        if self._token and self._token_expires > datetime.now():
            return self._token
        
        # Generate new token (valid for 1 hour)
        self._token = _generate_service_token(ttl_seconds=3600)
        self._token_expires = datetime.now() + timedelta(seconds=3300)  # Regenerate 5 min early
        return self._token
```

**For Postman Testing:**

- Tokens expire after the TTL you set (default: 1 hour)
- When token expires, generate a new one: `make generate-grpc-token`
- Update the token in Postman's Metadata tab
- For Scenario 4: Ensure certificate CN matches JWT service name, or set `GRPC_REQUIRE_CERT_JWT_MATCH=false` for testing

---

## Summary

### Authentication Variables (Simple!)

**You only need 2 environment variables:**

| Variable | Purpose | Values |
|----------|---------|--------|
| `GRPC_TLS_ENABLED` | Enable TLS encryption | `true` / `false` |
| `GRPC_AUTH_ENABLED` | Require JWT bearer token | `true` / `false` |

**That's it!** No need for `GRPC_REQUIRE_CLIENT_AUTH` - it's not used in the code.

### Authentication Layers

- **TLS (Certificates)**: "Is this connection secure and legitimate?" (transport layer)
- **JWT (Tokens)**: "Which service is this and what can they do?" (application layer)
- **Both together**: Maximum security (production)
- **Either one**: Good for testing specific auth mechanisms
- **Neither**: Development only (not secure)

### Token Refresh

- **Each service generates its own tokens** (no central server)
- **No automatic refresh** - services regenerate tokens when needed
- **Short-lived tokens** (5 min to 1 hour recommended)
- **Best practice**: Generate on-demand, cache briefly, regenerate before expiration
