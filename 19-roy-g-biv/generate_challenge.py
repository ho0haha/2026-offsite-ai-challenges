#!/usr/bin/env python3
"""
Challenge 19: Roy G Biv — Generator

Creates spectrum.rgbiv containing 7 ROYGBIV circles with stippled CAPTCHA numbers.
Different decoder flag combinations make different circles readable/garbled.

Circles 0-3: encoded with DELTA_RUN (overflow-dependent, needs delta_mode=0 clamp)
Circles 4-6: encoded with FILL_PAIR (order-dependent, needs fill_order=0)

Run:  python3 generate_challenge.py
      python3 generate_challenge.py --verify   (also outputs verification PNGs)
"""

import struct
import sys
import math
import random
import zlib
from pathlib import Path

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ─── Constants ────────────────────────────────────────────────────────────────

WIDTH = 400
HEIGHT = 300
FLAG = "CTF{pr1sm_d3c0d3d_r41nb0w_m4st3r}"
SEED = 0x52474249
DATA_ROW_IDX = 250  # must fit in uint8

CIRCLE_NUMBERS = [38, 72, 15, 94, 63, 27, 51]
KEY_STRING = "".join(f"{n:02d}" for n in CIRCLE_NUMBERS)
XOR_KEY = bytes([int(KEY_STRING[i:i+2]) for i in range(0, 14, 2)])

FONT_5x7 = {
    0: [0b01110,0b10001,0b10011,0b10101,0b11001,0b10001,0b01110],
    1: [0b00100,0b01100,0b00100,0b00100,0b00100,0b00100,0b01110],
    2: [0b01110,0b10001,0b00001,0b00010,0b00100,0b01000,0b11111],
    3: [0b01110,0b10001,0b00001,0b00110,0b00001,0b10001,0b01110],
    4: [0b00010,0b00110,0b01010,0b10010,0b11111,0b00010,0b00010],
    5: [0b11111,0b10000,0b11110,0b00001,0b00001,0b10001,0b01110],
    6: [0b00110,0b01000,0b10000,0b11110,0b10001,0b10001,0b01110],
    7: [0b11111,0b00001,0b00010,0b00100,0b01000,0b01000,0b01000],
    8: [0b01110,0b10001,0b10001,0b01110,0b10001,0b10001,0b01110],
    9: [0b01110,0b10001,0b10001,0b01111,0b00001,0b00010,0b01100],
}

ROYGBIV = [
    ("Red",    (220,40,40),   (255,140,140), (140,20,20)),
    ("Orange", (240,150,30),  (255,200,120), (160,90,10)),
    ("Yellow", (240,220,40),  (255,245,150), (170,150,10)),
    ("Green",  (40,180,60),   (140,230,150), (15,110,30)),
    ("Blue",   (40,80,220),   (140,160,255), (15,40,140)),
    ("Indigo", (80,40,180),   (160,130,240), (40,15,110)),
    ("Violet", (160,50,180),  (220,150,240), (100,20,110)),
]

CIRCLE_DEFS = [
    (70,  70,  38),  # 0 Red
    (200, 55,  35),  # 1 Orange
    (330, 75,  40),  # 2 Yellow
    (130, 160, 37),  # 3 Green
    (270, 155, 36),  # 4 Blue
    (85,  245, 35),  # 5 Indigo
    (310, 240, 38),  # 6 Violet
]

# ─── Palette ──────────────────────────────────────────────────────────────────

def build_palette():
    """0=black, 1=white, 2-8=base, 9-15=light, 16-22=dark, 23-30=grays, 31-154=data"""
    pal = [(0,0,0), (255,255,255)]       # 0=black, 1=white
    for _,b,_,_ in ROYGBIV: pal.append(b)  # 2-8 base
    for _,_,l,_ in ROYGBIV: pal.append(l)  # 9-15 light
    for _,_,_,d in ROYGBIV: pal.append(d)  # 16-22 dark
    for i in range(8):                     # 23-30 grays
        v = 30 + i*28; pal.append((v,v,v))
    # 31-154: data encoding (124 entries for lossless byte storage)
    for i in range(124):
        pal.append(((i*73+50)%256, (i*47+100)%256, (i*113+30)%256))
    return pal

# ─── Image Building ──────────────────────────────────────────────────────────

def get_number_bitmap(number, scale=3):
    d1, d2 = number // 10, number % 10
    gap = scale
    rows = []
    for r in range(7):
        row = []
        for col in range(5):
            row.extend([bool((FONT_5x7[d1][r] >> (4-col)) & 1)] * scale)
        row.extend([False] * gap)
        for col in range(5):
            row.extend([bool((FONT_5x7[d2][r] >> (4-col)) & 1)] * scale)
        for _ in range(scale):
            rows.append(row[:])
    return rows


def build_image_and_flat():
    """Build the image and return flat pixel array + circle map.

    Circles 0-3: stipple with every 6th fill pixel set to 0 (black marker).
      In clamp mode these decode as 0 (black, subtle).
      In wrap mode they decode as 255 (magenta, garbled).
    Circles 4-6: normal stipple, encoded with FILL_PAIR.
      fill_order=0 preserves light/dark pattern (correct).
      fill_order=1 swaps them (inverts stipple bias, garbles number).
    """
    rng = random.Random(SEED)
    flat = [0] * (WIDTH * HEIGHT)
    circle_map = [-1] * (WIDTH * HEIGHT)

    for ci, (cx, cy, radius) in enumerate(CIRCLE_DEFS):
        light = 9 + ci
        dark = 16 + ci
        bm = get_number_bitmap(CIRCLE_NUMBERS[ci], scale=3)
        bh, bw = len(bm), len(bm[0])
        bx, by = cx - bw//2, cy - bh//2

        for y in range(max(0, cy-radius), min(HEIGHT, cy+radius+1)):
            for x in range(max(0, cx-radius), min(WIDTH, cx+radius+1)):
                if (x-cx)**2 + (y-cy)**2 <= radius**2:
                    idx = y * WIDTH + x
                    nr, nc = y - by, x - bx
                    in_num = (0 <= nr < bh and 0 <= nc < bw and bm[nr][nc])
                    val = light if rng.random() < (0.62 if in_num else 0.50) else dark
                    flat[idx] = val
                    circle_map[idx] = ci

        # Draw outline (overwrites fill at edges)
        for step in range(360 * 3):
            a = math.radians(step / 3.0)
            ox = int(round(cx + radius * math.cos(a)))
            oy = int(round(cy + radius * math.sin(a)))
            if 0 <= ox < WIDTH and 0 <= oy < HEIGHT:
                i = oy * WIDTH + ox
                flat[i] = 1
                circle_map[i] = -1

    # Insert delta markers for circles 0-3: every 6th fill pixel becomes 0
    for ci in range(4):
        cx, cy, radius = CIRCLE_DEFS[ci]
        for y in range(max(0, cy-radius), min(HEIGHT, cy+radius+1)):
            fill_count = 0
            for x in range(max(0, cx-radius), min(WIDTH, cx+radius+1)):
                idx = y * WIDTH + x
                if circle_map[idx] == ci:
                    if fill_count % 6 == 5:
                        flat[idx] = 0  # black marker (clamp=0, wrap=255)
                    fill_count += 1

    # Background noise
    for y in range(HEIGHT):
        for x in range(WIDTH):
            idx = y * WIDTH + x
            if flat[idx] == 0 and circle_map[idx] == -1:
                if rng.random() < 0.08:
                    flat[idx] = 23 + rng.randint(0, 7)

    # Insert encrypted flag into data row
    encrypted = encrypt_flag(FLAG, XOR_KEY)
    dr = DATA_ROW_IDX * WIDTH
    drng = random.Random(SEED + 999)
    for i in range(len(encrypted)):
        flat[dr + i] = 31 + encrypted[i]  # lossless: encrypted bytes are 0-123
    for i in range(len(encrypted), WIDTH):
        flat[dr + i] = 31 + drng.randint(0, 123)

    return flat, circle_map, encrypted


# ─── CRLE Encoding Primitives ────────────────────────────────────────────────

def _enc_n(opbits, n):
    """Encode opcode byte with length extension."""
    buf = bytearray()
    if n < 31:
        buf.append((opbits << 5) | n)
    else:
        buf.append((opbits << 5) | 31)
        r = n - 31
        while r >= 255:
            buf.append(255)
            r -= 255
        buf.append(r)
    return buf

def enc_literal(data):
    out = bytearray()
    i = 0
    while i < len(data):
        chunk = data[i:i+256]
        out.extend(_enc_n(0b000, len(chunk)-1))
        out.extend(chunk)
        i += len(chunk)
    return bytes(out)

def enc_repeat(val, count):
    buf = _enc_n(0b001, count-1)
    buf.append(val)
    return bytes(buf)

def enc_delta_run(start, delta, count):
    buf = _enc_n(0b011, count-1)
    buf.append(start & 0xFF)
    buf.append(delta & 0xFF)
    return bytes(buf)

def enc_fill_pair(v1, v2, pair_count):
    buf = _enc_n(0b100, pair_count-1)
    buf.append(v1)
    buf.append(v2)
    return bytes(buf)

def enc_row_copy(count, row_width):
    buf = _enc_n(0b110, count-1)
    buf.append((row_width >> 8) & 0xFF)
    buf.append(row_width & 0xFF)
    return bytes(buf)

def enc_end():
    return bytes([0b111 << 5])


# ─── CRLE Compression ────────────────────────────────────────────────────────

def compress(flat, circle_map, enc_flag_len):
    """Compress flat pixel array.

    Circles 0-3 (DELTA_RUN):
      Fill spans encoded as groups of [LITERAL(4), DELTA_RUN(count=2)].
      The DELTA_RUN pairs a real fill pixel with a 0-marker:
        start=fill_val, delta=-(fill_val+1), count=2
        → clamp: [fill_val, 0], wrap: [fill_val, 255]
      ~16% of circle pixels garble in wrong delta_mode.

    Circles 4-6 (FILL_PAIR):
      Alternating light/dark stipple → FILL_PAIR(v1, v2, count).
      fill_order=0: v1,v2 (correct), fill_order=1: v2,v1 (swapped).
      ~37% of circle pixels garble in wrong fill_order.
    """
    compressed = bytearray()

    for row_idx in range(HEIGHT):
        rs = row_idx * WIDTH
        row = flat[rs:rs+WIDTH]
        cm = circle_map[rs:rs+WIDTH]

        # ROW_COPY for duplicate rows
        if row_idx > 0 and row_idx != DATA_ROW_IDX:
            prev = flat[(row_idx-1)*WIDTH:row_idx*WIDTH]
            if row == prev:
                compressed.extend(enc_row_copy(WIDTH, WIDTH))
                continue

        # Segment by circle membership
        x = 0
        while x < WIDTH:
            ci = cm[x]
            sx = x
            while x < WIDTH and cm[x] == ci:
                x += 1
            seg = row[sx:x]

            if ci == -1 or row_idx == DATA_ROW_IDX:
                compressed.extend(_comp_basic(seg))
            elif ci <= 3:
                compressed.extend(_comp_delta(seg, ci))
            else:
                compressed.extend(_comp_fillpair(seg, ci))

    compressed.extend(enc_end())
    return bytes(compressed)


def _comp_basic(data):
    """Encode non-circle data with REPEAT and LITERAL."""
    if not data:
        return b''
    out = bytearray()
    i = 0
    while i < len(data):
        val = data[i]
        run = 1
        while i+run < len(data) and data[i+run] == val and run < 256:
            run += 1
        if run >= 3:
            out.extend(enc_repeat(val, run))
            i += run
        else:
            ls = i
            while i < len(data):
                if i+2 < len(data) and data[i] == data[i+1] == data[i+2]:
                    break
                i += 1
            out.extend(enc_literal(bytes(data[ls:i])))
    return bytes(out)


def _comp_delta(seg, ci):
    """Encode circle 0-3 segment with DELTA_RUN overflow markers.

    Outline pixels (value=1) → REPEAT.
    Fill spans → find 0-markers and encode each as:
      LITERAL(preceding pixels) + DELTA_RUN(count=2 for [prev_val, 0])
      where delta = -(prev_val+1), so start+1*delta = -1.
      Clamp: [prev_val, 0]. Wrap: [prev_val, 255].
    """
    out = bytearray()
    i = 0
    while i < len(seg):
        if seg[i] == 1:
            run = 1
            while i+run < len(seg) and seg[i+run] == 1:
                run += 1
            out.extend(enc_repeat(1, run))
            i += run
            continue

        # Collect fill span (non-outline)
        ss = i
        while i < len(seg) and seg[i] != 1:
            i += 1
        out.extend(_encode_delta_span(seg[ss:i]))
    return bytes(out)


def _encode_delta_span(span):
    """Encode fill span from circles 0-3, pairing markers with DELTA_RUN."""
    out = bytearray()
    i = 0
    while i < len(span):
        # Find next 0-marker
        marker = None
        for j in range(i, len(span)):
            if span[j] == 0:
                marker = j
                break

        if marker is None:
            out.extend(_comp_basic(span[i:]))
            break

        if marker == i:
            # Marker at start, no preceding pixel to pair with
            out.extend(enc_literal(bytes([0])))
            i = marker + 1
            continue

        # Encode pixels before the one paired with the marker
        if marker - 1 > i:
            out.extend(enc_literal(bytes(span[i:marker-1])))

        # Encode [span[marker-1], 0] as DELTA_RUN(count=2)
        prev_val = span[marker - 1]
        if prev_val > 0:
            delta = -(prev_val + 1)  # start + 1*delta = -1 → clamp:0, wrap:255
            out.extend(enc_delta_run(prev_val, delta, 2))
        else:
            out.extend(enc_literal(bytes([0, 0])))

        i = marker + 1
    return bytes(out)


def _comp_fillpair(seg, ci):
    """Encode circle 4-6 segment with FILL_PAIR.

    Alternating light/dark stipple → FILL_PAIR(v1, v2, count).
    fill_order=0: v1,v2 (correct), fill_order=1: v2,v1 (swapped).
    """
    light = 9 + ci
    dark = 16 + ci
    out = bytearray()
    i = 0
    while i < len(seg):
        if seg[i] == 1:
            run = 1
            while i+run < len(seg) and seg[i+run] == 1:
                run += 1
            out.extend(enc_repeat(1, run))
            i += run
            continue

        # Fill span
        ss = i
        while i < len(seg) and seg[i] != 1:
            i += 1
        span = seg[ss:i]

        j = 0
        while j < len(span):
            if j+1 < len(span):
                v1, v2 = span[j], span[j+1]
                if v1 != v2 and v1 in (light,dark) and v2 in (light,dark):
                    pairs = 1
                    k = j+2
                    while k+1 < len(span) and span[k] == v1 and span[k+1] == v2:
                        pairs += 1
                        k += 2
                    out.extend(enc_fill_pair(v1, v2, pairs))
                    j += pairs * 2
                    continue

            val = span[j]
            run = 1
            while j+run < len(span) and span[j+run] == val:
                run += 1
            if run >= 3:
                out.extend(enc_repeat(val, run))
            else:
                out.extend(enc_literal(bytes(span[j:j+run])))
            j += run
    return bytes(out)


# ─── Reference Decoder ────────────────────────────────────────────────────────

def decode_crle(data, width, height, delta_mode=0, fill_order=0):
    output = []
    pos = 0
    target = width * height

    while pos < len(data) and len(output) < target:
        byte = data[pos]; pos += 1
        opcode = (byte >> 5) & 7
        n = byte & 0x1F
        if n == 31:
            while pos < len(data):
                ext = data[pos]; pos += 1
                n += ext
                if ext < 255: break

        if opcode == 0b000:  # LITERAL
            c = n+1; output.extend(data[pos:pos+c]); pos += c
        elif opcode == 0b001:  # REPEAT
            output.extend([data[pos]] * (n+1)); pos += 1
        elif opcode == 0b010:  # COPY_PREV
            off = (data[pos]<<8)|data[pos+1]; pos += 2
            s = len(output) - off
            for k in range(n+1): output.append(output[s+k])
        elif opcode == 0b011:  # DELTA_RUN
            sv = data[pos]; pos += 1
            d = data[pos]; pos += 1
            if d >= 128: d -= 256
            for k in range(n+1):
                v = sv + k*d
                v = max(0,min(255,v)) if delta_mode==0 else v%256
                output.append(v)
        elif opcode == 0b100:  # FILL_PAIR
            v1 = data[pos]; pos += 1
            v2 = data[pos]; pos += 1
            for _ in range(n+1):
                if fill_order==0: output.extend([v1,v2])
                else: output.extend([v2,v1])
        elif opcode == 0b101:  # NESTED_REPEAT
            res = _dec_one(data, pos, delta_mode, fill_order)
            pos = res[1]
            for _ in range(n+1): output.extend(res[0])
        elif opcode == 0b110:  # ROW_COPY
            rw = (data[pos]<<8)|data[pos+1]; pos += 2
            s = len(output) - rw
            for k in range(n+1): output.append(output[s+k])
        elif opcode == 0b111:  # END
            break

    return output[:target]

def _dec_one(data, pos, dm, fo):
    byte = data[pos]; pos += 1
    op = (byte>>5)&7; n = byte&0x1F
    if n == 31:
        while pos < len(data):
            ext = data[pos]; pos += 1; n += ext
            if ext < 255: break
    vals = []
    if op == 0b000:
        c = n+1; vals = list(data[pos:pos+c]); pos += c
    elif op == 0b001:
        vals = [data[pos]]*(n+1); pos += 1
    elif op == 0b011:
        sv = data[pos]; pos += 1; d = data[pos]; pos += 1
        if d >= 128: d -= 256
        for k in range(n+1):
            v = sv+k*d; v = max(0,min(255,v)) if dm==0 else v%256; vals.append(v)
    elif op == 0b100:
        v1 = data[pos]; pos += 1; v2 = data[pos]; pos += 1
        for _ in range(n+1):
            if fo==0: vals.extend([v1,v2])
            else: vals.extend([v2,v1])
    return vals, pos


# ─── Helpers ──────────────────────────────────────────────────────────────────

def encrypt_flag(flag_str, xor_key):
    return bytes(b ^ xor_key[i % len(xor_key)] for i, b in enumerate(flag_str.encode('ascii')))

def write_rgbiv(filename, palette, compressed, encrypted):
    header = bytearray(32)
    header[0:4] = b'RGBI'
    struct.pack_into('>H', header, 0x04, 1)
    struct.pack_into('>H', header, 0x06, WIDTH)
    struct.pack_into('>H', header, 0x08, HEIGHT)
    header[0x0A] = len(palette)
    header[0x0B] = 1
    header[0x0C] = 0x01  # has_data_row=1
    header[0x0D] = DATA_ROW_IDX
    struct.pack_into('>H', header, 0x0E, len(encrypted))
    struct.pack_into('>I', header, 0x10, len(compressed))
    crc = zlib.crc32(header[0x00:0x14]) & 0xFFFFFFFF
    struct.pack_into('>I', header, 0x14, crc)
    with open(filename, 'wb') as f:
        f.write(header)
        for r,g,b in palette:
            f.write(bytes([r,g,b]))
        f.write(compressed)

def decode_to_image(compressed, palette, dm, fo):
    if not HAS_PIL: return None
    indices = decode_crle(compressed, WIDTH, HEIGHT, dm, fo)
    img = Image.new('RGB', (WIDTH, HEIGHT))
    px = img.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            idx = indices[y*WIDTH+x]
            px[x,y] = palette[idx] if 0 <= idx < len(palette) else (255,0,255)
    return img


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    verify = '--verify' in sys.argv
    outdir = Path(__file__).parent

    print("="*60)
    print("Challenge 19: Roy G Biv — Generator")
    print("="*60)

    palette = build_palette()
    print(f"Palette: {len(palette)} entries")

    print("Building image...")
    flat, circle_map, encrypted = build_image_and_flat()

    for i,(cx,cy,r) in enumerate(CIRCLE_DEFS):
        nm = ROYGBIV[i][0]
        enc = "DELTA_RUN" if i<=3 else "FILL_PAIR"
        print(f"  Circle {i} ({nm}): ({cx},{cy}) r={r} num={CIRCLE_NUMBERS[i]} [{enc}]")

    print(f"\nKey: {KEY_STRING}  XOR: {list(XOR_KEY)}")
    print(f"Flag: {FLAG} ({len(encrypted)} encrypted bytes)")

    print("\nCompressing...")
    compressed = compress(flat, circle_map, len(encrypted))
    ratio = len(compressed)*100//(WIDTH*HEIGHT)
    print(f"Compressed: {len(compressed)} bytes ({ratio}%)")

    outfile = outdir / "spectrum.rgbiv"
    write_rgbiv(str(outfile), palette, compressed, encrypted)
    print(f"Written: {outfile} ({outfile.stat().st_size} bytes)")

    # Verify
    print("\n--- Decode Verification ---")
    ref = decode_crle(compressed, WIDTH, HEIGHT, 0, 0)
    ref_match = sum(1 for a,b in zip(ref, flat) if a==b)
    print(f"  Reference (dm=0,fo=0) vs source: {ref_match}/{WIDTH*HEIGHT} "
          f"({ref_match*100//(WIDTH*HEIGHT)}%)")

    for dm in [0,1]:
        for fo in [0,1]:
            dec = decode_crle(compressed, WIDTH, HEIGHT, dm, fo)
            match = sum(1 for a,b in zip(dec, ref) if a==b)
            pct = match*100//(WIDTH*HEIGHT)
            tag = " *" if dm==0 and fo==0 else ""
            print(f"  dm={dm} fo={fo}: {match}/{WIDTH*HEIGHT} match ref ({pct}%){tag}")
            if verify and HAS_PIL:
                img = decode_to_image(compressed, palette, dm, fo)
                fn = outdir / f"verify_dm{dm}_fo{fo}.png"
                img.save(str(fn)); print(f"    -> {fn}")

    # Circle garbling analysis
    print("\n--- Circle Garbling Analysis ---")
    d00 = decode_crle(compressed, WIDTH, HEIGHT, 0, 0)
    d10 = decode_crle(compressed, WIDTH, HEIGHT, 1, 0)
    d01 = decode_crle(compressed, WIDTH, HEIGHT, 0, 1)
    for ci,(cx,cy,radius) in enumerate(CIRCLE_DEFS):
        dm_diff = fo_diff = total = 0
        for y in range(max(0,cy-radius), min(HEIGHT,cy+radius+1)):
            for x in range(max(0,cx-radius), min(WIDTH,cx+radius+1)):
                if (x-cx)**2+(y-cy)**2 <= radius**2:
                    idx = y*WIDTH+x
                    total += 1
                    if d00[idx] != d10[idx]: dm_diff += 1
                    if d00[idx] != d01[idx]: fo_diff += 1
        nm = ROYGBIV[ci][0]
        enc = "DELTA" if ci<=3 else "FILL"
        print(f"  {ci} ({nm:7s}) [{enc:5s}]: "
              f"dm_garble={dm_diff*100//max(1,total):2d}% "
              f"fo_garble={fo_diff*100//max(1,total):2d}%")

    # Flag verification via player path
    print("\n--- Flag Decryption (player path) ---")
    dec_default = decode_crle(compressed, WIDTH, HEIGHT, 0, 0)
    enc_indices = dec_default[DATA_ROW_IDX*WIDTH : DATA_ROW_IDX*WIDTH + len(encrypted)]
    enc_bytes = bytes(idx - 31 for idx in enc_indices)
    decrypted = bytes(b ^ XOR_KEY[i%len(XOR_KEY)] for i,b in enumerate(enc_bytes))
    print(f"  Recovered: {decrypted.decode('ascii')}")
    assert decrypted.decode('ascii') == FLAG, "Flag mismatch!"
    print("  Flag verified OK!")

    print(f"\n{'='*60}")
    print(f"  Flag: {FLAG}")
    print(f"  Key: {KEY_STRING}")
    print(f"  Circles 0-3: need delta_mode=0")
    print(f"  Circles 4-6: need fill_order=0")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
