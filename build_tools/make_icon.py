"""Gera assets/icon.ico (sem dependencias): quadrado escuro arredondado com um ponto de gravacao dourado e '2x'."""
import struct, zlib, math, sys
from pathlib import Path

def render(n):
    ss = 4; N = n * ss
    px = [[(0, 0, 0, 0)] * n for _ in range(n)]
    acc = [[[0, 0, 0, 0] for _ in range(n)] for _ in range(n)]
    r = N * 0.2
    cx, cy, cr = N * 0.5, N * 0.5, N * 0.30
    for Y in range(N):
        for X in range(N):
            # retangulo arredondado
            dx = max(r - X, 0, X - (N - 1 - r)); dy = max(r - Y, 0, Y - (N - 1 - r))
            if dx * dx + dy * dy > r * r:
                continue
            col = (24, 27, 31)
            d = math.hypot(X - cx, Y - cy)
            if d <= cr:
                col = (214, 164, 99)
                if d <= cr * 0.55:
                    col = (200, 60, 45)
            elif d <= cr * 1.12:
                col = (24, 27, 31)
            elif d <= cr * 1.24:
                col = (154, 106, 51)
            a = acc[Y // ss][X // ss]
            a[0] += col[0]; a[1] += col[1]; a[2] += col[2]; a[3] += 255
    k = ss * ss
    rows = []
    for y in range(n):
        row = b"\x00"
        for x in range(n):
            a = acc[y][x]
            if a[3]:
                cnt = a[3] / 255
                row += bytes((int(a[0] / cnt), int(a[1] / cnt), int(a[2] / cnt), int(a[3] / k)))
            else:
                row += b"\x00\x00\x00\x00"
        rows.append(row)
    raw = b"".join(rows)
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))

sizes = [16, 24, 32, 48, 64, 128, 256]
pngs = [render(s) for s in sizes]
out = Path(sys.argv[1])
head = struct.pack("<HHH", 0, 1, len(sizes))
off = 6 + 16 * len(sizes)
dirs = b""
for s, p in zip(sizes, pngs):
    dirs += struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, 1, 32, len(p), off)
    off += len(p)
out.write_bytes(head + dirs + b"".join(pngs))
Path(out.with_suffix(".png")).write_bytes(pngs[-1])
print("ok", out)
