"""Cliente minimo do OBS WebSocket (protocolo v5), so com a biblioteca padrao do Python.

Uso:
  obs = OBS("127.0.0.1", 4455, "senha")
  obs.call("StartRecord")
"""
import base64
import hashlib
import json
import os
import socket
import struct
import uuid
from pathlib import Path


class OBSError(RuntimeError):
    pass


class OBS:
    def __init__(self, host, port, password=""):
        self.sock = socket.create_connection((host, port), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (f"GET / HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
               f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
               f"Sec-WebSocket-Protocol: obswebsocket.json\r\n\r\n")
        self.sock.sendall(req.encode())
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise OBSError("OBS fechou a conexao no handshake")
            head += chunk
        head, self.buf = head.split(b"\r\n\r\n", 1)
        if b" 101 " not in head.split(b"\r\n")[0]:
            raise OBSError("handshake recusado: " + head.split(b"\r\n")[0].decode())
        hello = self._recv()
        if hello.get("op") != 0:
            raise OBSError(f"esperava Hello, veio {hello}")
        ident = {"rpcVersion": 1, "eventSubscriptions": 0}
        auth = hello["d"].get("authentication")
        if auth:
            secret = base64.b64encode(hashlib.sha256((password + auth["salt"]).encode()).digest()).decode()
            ident["authentication"] = base64.b64encode(
                hashlib.sha256((secret + auth["challenge"]).encode()).digest()).decode()
        self._send({"op": 1, "d": ident})
        ok = self._recv()
        if ok.get("op") != 2:
            raise OBSError(f"autenticacao falhou: {ok}")

    @classmethod
    def from_config(cls, path="obs_config.json"):
        cfg = json.loads(Path(path).read_text(encoding="utf-8"))
        hosts = [cfg.get("host", "127.0.0.1")]
        if "127.0.0.1" not in hosts:
            hosts.append("127.0.0.1")
        last = None
        for h in hosts:
            try:
                return cls(h, int(cfg.get("port", 4455)), cfg.get("password", ""))
            except OSError as e:
                last = e
        raise OBSError(f"nao conectou no OBS: {last}")

    def call(self, request, data=None):
        rid = str(uuid.uuid4())
        d = {"requestType": request, "requestId": rid}
        if data:
            d["requestData"] = data
        self._send({"op": 6, "d": d})
        while True:
            msg = self._recv()
            if msg.get("op") == 7 and msg["d"].get("requestId") == rid:
                st = msg["d"]["requestStatus"]
                if not st.get("result"):
                    raise OBSError(f"{request}: {st.get('code')} {st.get('comment', '')}")
                return msg["d"].get("responseData", {})

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass

    # --- quadros WebSocket ---
    def _send(self, obj):
        payload = json.dumps(obj).encode()
        n = len(payload)
        hdr = bytearray([0x81])
        if n < 126:
            hdr.append(0x80 | n)
        elif n < 65536:
            hdr.append(0x80 | 126); hdr += struct.pack(">H", n)
        else:
            hdr.append(0x80 | 127); hdr += struct.pack(">Q", n)
        mask = os.urandom(4)
        self.sock.sendall(bytes(hdr) + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def _read(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise OBSError("OBS fechou a conexao")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def _recv(self):
        while True:
            b0, b1 = self._read(2)
            op, n = b0 & 0x0F, b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            data = self._read(n)
            if op == 0x8:
                raise OBSError("OBS fechou a conexao")
            if op == 0x9:  # ping -> pong
                self.sock.sendall(bytes([0x8A, 0x80 | len(data)]) + b"\0\0\0\0" + data)
                continue
            if op in (0x1, 0x0):
                return json.loads(data)
