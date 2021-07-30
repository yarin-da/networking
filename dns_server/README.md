# Simple DNS Server implementation

This program simulates a simple DNS server that caches queries with a TTL. Servers search for an existing cache file to repopulate the cache after a crash.

There's a simple client implementation to test the server via the terminal.

```bash
    USAGE: client.py [SERVER_IP] [SERVER_PORT]
    USAGE: [program] [myPort] [parentIP] [parentPort] [ipsFileName]
```