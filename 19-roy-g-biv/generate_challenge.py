#!/usr/bin/env python3
"""
Challenge 19: Roy G Biv — Generator (SIRDS + Haar DWT)

Encoding pipeline:
  1. Build image: grid of colored circles, each a SIRDS stereogram hiding a number
  2. Row-wise Haar wavelet transform (1 level) on all rows except the data row
  3. CRLE compress the coefficient stream

Each circle is a Single Image Random Dot Stereogram (SIRDS) encoding a two-digit
number as depth information. Humans can read the numbers by cross-eyed or
wall-eyed viewing. AI vision models cannot perceive the depth.

Run:  python3 generate_challenge.py
      python3 generate_challenge.py --verify
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

GRID_COLS = 4
GRID_ROWS = 7
CIRCLE_RADIUS = 75
CIRCLE_SPACING_X = 170
CIRCLE_SPACING_Y = 170
GRID_MARGIN_X = 45
GRID_MARGIN_Y = 45

SIRDS_SEP = 16        # horizontal repeat period (tile width)
SIRDS_SHIFT = 3       # depth disparity in pixels for number region
FONT_SCALE = 5        # scale factor for 5x7 bitmap font

WIDTH = GRID_MARGIN_X * 2 + GRID_COLS * CIRCLE_SPACING_X
HEIGHT = GRID_MARGIN_Y * 2 + GRID_ROWS * CIRCLE_SPACING_Y

FLAG = "CTF{pr1sm_d3c0d3d_r41nb0w_m4st3r}"
SEED = 0x52474249
DATA_ROW_IDX = min(HEIGHT - 1, 250)
DATA_PALETTE_OFFSET = 31
BG_NOISE_PROB = 0.06

CIRCLE_NUMBERS = [38, 72, 15, 94, 63, 27, 51]
XOR_KEY = bytes(CIRCLE_NUMBERS)

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

# ─── Palette ──────────────────────────────────────────────────────────────────

def build_palette():
    pal = [(0, 0, 0), (255, 255, 255)]
    for _, b, _, _ in ROYGBIV:
        pal.append(b)
    for _, _, l, _ in ROYGBIV:
        pal.append(l)
    for _, _, _, d in ROYGBIV:
        pal.append(d)
    for i in range(8):
        v = 30 + i * 28
        pal.append((v, v, v))
    for i in range(124):
        pal.append(((i * 73 + 50) % 256, (i * 47 + 100) % 256, (i * 113 + 30) % 256))
    return pal

# ─── Number Bitmap ────────────────────────────────────────────────────────────

def get_number_mask(number, scale=FONT_SCALE):
    d1, d2 = number // 10, number % 10
    gap = scale
    positions = set()
    for r in range(7):
        for col in range(5):
            if (FONT_5x7[d1][r] >> (4 - col)) & 1:
                for sy in range(scale):
                    for sx in range(scale):
                        positions.add((r * scale + sy, col * scale + sx))
        for col in range(5):
            if (FONT_5x7[d2][r] >> (4 - col)) & 1:
                for sy in range(scale):
                    for sx in range(scale):
                        positions.add((r * scale + sy, 5 * scale + gap + col * scale + sx))
    bw = 5 * scale + gap + 5 * scale
    bh = 7 * scale
    return positions, bw, bh


# Pre-compute masks for all numbers
NUMBER_MASKS = {n: get_number_mask(n) for n in CIRCLE_NUMBERS}

# ─── Circle Drawing Helper ───────────────────────────────────────────────────

def draw_circle_outline(flat, img_width, img_height, cx, cy, radius, value=1):
    """Draw a circle outline using midpoint algorithm."""
    x, y = radius, 0
    err = 1 - radius
    while x >= y:
        for px, py in [(cx+x, cy+y), (cx-x, cy+y), (cx+x, cy-y), (cx-x, cy-y),
                       (cx+y, cy+x), (cx-y, cy+x), (cx+y, cy-x), (cx-y, cy-x)]:
            if 0 <= px < img_width and 0 <= py < img_height:
                flat[py * img_width + px] = value
        y += 1
        if err < 0:
            err += 2 * y + 1
        else:
            x -= 1
            err += 2 * (y - x) + 1

# ─── SIRDS Rendering ────────────────────────────────────────────────────────

def circle_center(color_idx, col_idx):
    cx = GRID_MARGIN_X + col_idx * CIRCLE_SPACING_X + CIRCLE_SPACING_X // 2
    cy = GRID_MARGIN_Y + color_idx * CIRCLE_SPACING_Y + CIRCLE_SPACING_Y // 2
    return cx, cy


def render_sirds_circle(flat, img_width, cx, cy, ci, col_idx):
    """Render one SIRDS circle into the flat pixel array."""
    light = 9 + ci
    dark = 16 + ci
    positions, bw, bh = NUMBER_MASKS[CIRCLE_NUMBERS[ci]]
    num_x0 = cx - bw // 2
    num_y0 = cy - bh // 2
    diameter = CIRCLE_RADIUS * 2
    r_sq = CIRCLE_RADIUS * CIRCLE_RADIUS

    for local_y in range(diameter):
        y = cy - CIRCLE_RADIUS + local_y
        if y < 0 or y >= HEIGHT:
            continue

        # Per-row RNG for the seed strip
        row_rng = random.Random(SEED + ci * 10000 + col_idx * 1000 + local_y)

        # Generate SIRDS row across the full diameter
        row_pixels = [0] * diameter
        for lx in range(min(SIRDS_SEP, diameter)):
            row_pixels[lx] = light if row_rng.random() < 0.5 else dark

        for lx in range(SIRDS_SEP, diameter):
            x = cx - CIRCLE_RADIUS + lx
            bm_y = y - num_y0
            bm_x = x - num_x0
            has_depth = (bm_y, bm_x) in positions
            offset = SIRDS_SEP - (SIRDS_SHIFT if has_depth else 0)
            src = lx - offset
            if src >= 0:
                row_pixels[lx] = row_pixels[src]
            else:
                row_pixels[lx] = light if row_rng.random() < 0.5 else dark

        # Write only pixels inside the circle
        rel_y = local_y - CIRCLE_RADIUS
        for lx in range(diameter):
            rel_x = lx - CIRCLE_RADIUS
            if rel_y * rel_y + rel_x * rel_x <= r_sq:
                x = cx - CIRCLE_RADIUS + lx
                if 0 <= x < img_width:
                    flat[y * img_width + x] = row_pixels[lx]


# ─── Haar Wavelet (1-level, row-wise, integer lifting) ──────────────────────

def haar_forward_row(row):
    n = len(row)
    half = n // 2
    out = [0] * n
    for i in range(half):
        even, odd = row[2 * i], row[2 * i + 1]
        diff = odd - even
        out[i] = max(0, min(255, even + (diff >> 1)))
        out[half + i] = max(0, min(255, diff + 128))
    return out


def haar_inverse_row(row):
    n = len(row)
    half = n // 2
    out = [0] * n
    for i in range(half):
        d_val = row[half + i] - 128
        even = row[i] - (d_val >> 1)
        out[2 * i] = max(0, min(255, even))
        out[2 * i + 1] = max(0, min(255, d_val + even))
    return out


def haar_forward_image(flat, width, height, skip_row):
    result = list(flat)
    for y in range(height):
        if y == skip_row:
            continue
        row = flat[y * width:(y + 1) * width]
        result[y * width:(y + 1) * width] = haar_forward_row(row)
    return result


def haar_inverse_image(coeffs, width, height, skip_row):
    result = list(coeffs)
    for y in range(height):
        if y == skip_row:
            continue
        row = coeffs[y * width:(y + 1) * width]
        result[y * width:(y + 1) * width] = haar_inverse_row(row)
    return result


# ─── Image Building ──────────────────────────────────────────────────────────

def build_image():
    flat = [0] * (WIDTH * HEIGHT)

    for ci in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cx, cy = circle_center(ci, col)
            render_sirds_circle(flat, WIDTH, cx, cy, ci, col)
            draw_circle_outline(flat, WIDTH, HEIGHT, cx, cy, CIRCLE_RADIUS)

    # Sparse background noise
    bg_rng = random.Random(SEED + 7777)
    for i in range(WIDTH * HEIGHT):
        if flat[i] == 0 and bg_rng.random() < BG_NOISE_PROB:
            flat[i] = 23 + bg_rng.randint(0, 7)

    # Encrypted flag in data row
    encrypted = encrypt_flag(FLAG, XOR_KEY)
    dr = DATA_ROW_IDX * WIDTH
    drng = random.Random(SEED + 999)
    for i in range(len(encrypted)):
        flat[dr + i] = DATA_PALETTE_OFFSET + encrypted[i]
    for i in range(len(encrypted), WIDTH):
        flat[dr + i] = DATA_PALETTE_OFFSET + drng.randint(0, 123)

    return flat, encrypted


# ─── CRLE Encoding ───────────────────────────────────────────────────────────

def _enc_n(opbits, n):
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
        chunk = data[i:i + 256]
        out.extend(_enc_n(0b000, len(chunk) - 1))
        out.extend(chunk)
        i += len(chunk)
    return bytes(out)


def enc_repeat(val, count):
    buf = _enc_n(0b001, count - 1)
    buf.append(val)
    return bytes(buf)


def enc_row_copy(count, row_width):
    buf = _enc_n(0b110, count - 1)
    buf.append((row_width >> 8) & 0xFF)
    buf.append(row_width & 0xFF)
    return bytes(buf)


def enc_end():
    return bytes([0b111 << 5])


def compress(data_flat):
    compressed = bytearray()
    for row_idx in range(HEIGHT):
        rs = row_idx * WIDTH
        row = data_flat[rs:rs + WIDTH]
        if row_idx > 0:
            prev = data_flat[(row_idx - 1) * WIDTH:row_idx * WIDTH]
            if row == prev:
                compressed.extend(enc_row_copy(WIDTH, WIDTH))
                continue
        compressed.extend(_comp_basic(row))
    compressed.extend(enc_end())
    return bytes(compressed)


def _comp_basic(data):
    if not data:
        return b''
    out = bytearray()
    i = 0
    while i < len(data):
        val = data[i]
        run = 1
        while i + run < len(data) and data[i + run] == val and run < 256:
            run += 1
        if run >= 3:
            out.extend(enc_repeat(val, run))
            i += run
        else:
            ls = i
            while i < len(data):
                if i + 2 < len(data) and data[i] == data[i + 1] == data[i + 2]:
                    break
                i += 1
            out.extend(enc_literal(bytes(data[ls:i])))
    return bytes(out)


# ─── Reference Decoder ───────────────────────────────────────────────────────

def decode_crle(data, width, height):
    output = []
    pos = 0
    target = width * height
    while pos < len(data) and len(output) < target:
        byte = data[pos]; pos += 1
        opcode = (byte >> 5) & 7
        n = byte & 0x1F
        if n == 31:
            while pos < len(data):
                ext = data[pos]; pos += 1; n += ext
                if ext < 255:
                    break
        if opcode == 0b000:
            c = n + 1; output.extend(data[pos:pos + c]); pos += c
        elif opcode == 0b001:
            output.extend([data[pos]] * (n + 1)); pos += 1
        elif opcode == 0b010:
            off = (data[pos] << 8) | data[pos + 1]; pos += 2
            s = len(output) - off
            for k in range(n + 1):
                output.append(output[s + k])
        elif opcode == 0b011:
            sv = data[pos]; pos += 1; d = data[pos]; pos += 1
            if d >= 128:
                d -= 256
            for k in range(n + 1):
                v = sv + k * d; output.append(max(0, min(255, v)))
        elif opcode == 0b100:
            v1 = data[pos]; pos += 1; v2 = data[pos]; pos += 1
            for _ in range(n + 1):
                output.extend([v1, v2])
        elif opcode == 0b101:
            inner, pos = _dec_one(data, pos)
            for _ in range(n + 1):
                output.extend(inner)
        elif opcode == 0b110:
            rw = (data[pos] << 8) | data[pos + 1]; pos += 2
            s = len(output) - rw
            for k in range(n + 1):
                output.append(output[s + k])
        elif opcode == 0b111:
            break
    return output[:target]


def _dec_one(data, pos):
    byte = data[pos]; pos += 1
    op = (byte >> 5) & 7; n = byte & 0x1F
    if n == 31:
        while pos < len(data):
            ext = data[pos]; pos += 1; n += ext
            if ext < 255:
                break
    vals = []
    if op == 0b000:
        c = n + 1; vals = list(data[pos:pos + c]); pos += c
    elif op == 0b001:
        vals = [data[pos]] * (n + 1); pos += 1
    elif op == 0b011:
        sv = data[pos]; pos += 1; d = data[pos]; pos += 1
        if d >= 128:
            d -= 256
        for k in range(n + 1):
            vals.append(max(0, min(255, sv + k * d)))
    elif op == 0b100:
        v1 = data[pos]; pos += 1; v2 = data[pos]; pos += 1
        for _ in range(n + 1):
            vals.extend([v1, v2])
    return vals, pos


# ─── Helpers ─────────────────────────────────────────────────────────────────

def encrypt_flag(flag_str, xor_key):
    return bytes(b ^ xor_key[i % len(xor_key)] for i, b in enumerate(flag_str.encode('ascii')))


def write_rgbiv(filename, palette, compressed, encrypted):
    header = bytearray(32)
    header[0:4] = b'RGBI'
    struct.pack_into('>H', header, 0x04, 1)
    struct.pack_into('>H', header, 0x06, WIDTH)
    struct.pack_into('>H', header, 0x08, HEIGHT)
    header[0x0A] = len(palette) % 256
    header[0x0B] = 1  # CRLE
    header[0x0C] = 0x03  # has_data_row=1, haar_transform=1
    header[0x0D] = DATA_ROW_IDX
    struct.pack_into('>H', header, 0x0E, len(encrypted))
    struct.pack_into('>I', header, 0x10, len(compressed))
    crc = zlib.crc32(header[0x00:0x14]) & 0xFFFFFFFF
    struct.pack_into('>I', header, 0x14, crc)
    with open(filename, 'wb') as f:
        f.write(header)
        for r, g, b in palette:
            f.write(bytes([r, g, b]))
        f.write(compressed)


def decode_to_image(compressed, palette):
    if not HAS_PIL:
        return None
    coeffs = decode_crle(compressed, WIDTH, HEIGHT)
    indices = haar_inverse_image(coeffs, WIDTH, HEIGHT, DATA_ROW_IDX)
    img = Image.new('RGB', (WIDTH, HEIGHT))
    px = img.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            idx = indices[y * WIDTH + x]
            px[x, y] = palette[idx] if 0 <= idx < len(palette) else (255, 0, 255)
    return img


# ─── Verification Images ─────────────────────────────────────────────────────

def build_cheat_reference(palette):
    """Answer key: numbers shown in clear text on colored circles."""
    if not HAS_PIL:
        return None
    img = Image.new('RGB', (WIDTH, HEIGHT), (0, 0, 0))
    px = img.load()
    r_sq = CIRCLE_RADIUS * CIRCLE_RADIUS
    for ci in range(GRID_ROWS):
        base_rgb = ROYGBIV[ci][1]
        positions, bw, bh = NUMBER_MASKS[CIRCLE_NUMBERS[ci]]
        for col in range(GRID_COLS):
            cx, cy = circle_center(ci, col)
            bx_off = cx - bw // 2
            by_off = cy - bh // 2
            for y in range(cy - CIRCLE_RADIUS, cy + CIRCLE_RADIUS + 1):
                if y < 0 or y >= HEIGHT:
                    continue
                for x in range(cx - CIRCLE_RADIUS, cx + CIRCLE_RADIUS + 1):
                    if x < 0 or x >= WIDTH:
                        continue
                    if (x - cx) ** 2 + (y - cy) ** 2 <= r_sq:
                        if (y - by_off, x - bx_off) in positions:
                            px[x, y] = (0, 0, 0)
                        else:
                            px[x, y] = base_rgb
    # Outlines
    outline_flat = [0] * (WIDTH * HEIGHT)
    for ci in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cx, cy = circle_center(ci, col)
            draw_circle_outline(outline_flat, WIDTH, HEIGHT, cx, cy, CIRCLE_RADIUS)
    for i in range(WIDTH * HEIGHT):
        if outline_flat[i]:
            px[i % WIDTH, i // WIDTH] = (255, 255, 255)
    return img


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    verify = '--verify' in sys.argv
    outdir = Path(__file__).parent

    print("=" * 60)
    print("Challenge 19: Roy G Biv — Generator")
    print("=" * 60)

    palette = build_palette()
    print(f"Palette: {len(palette)} entries")
    print(f"Image: {WIDTH}x{HEIGHT}, Grid: {GRID_COLS}x{GRID_ROWS} = {GRID_COLS * GRID_ROWS} circles")
    print(f"SIRDS: sep={SIRDS_SEP}px, shift={SIRDS_SHIFT}px, font scale={FONT_SCALE}")

    print("\nBuilding image...")
    flat, encrypted = build_image()

    for ci in range(GRID_ROWS):
        print(f"  {ROYGBIV[ci][0]:7s}: {CIRCLE_NUMBERS[ci]:02d}")

    print("\nApplying Haar DWT (skip data row)...")
    coeffs = haar_forward_image(flat, WIDTH, HEIGHT, DATA_ROW_IDX)

    restored = haar_inverse_image(coeffs, WIDTH, HEIGHT, DATA_ROW_IDX)
    haar_match = sum(1 for a, b in zip(flat, restored) if a == b)
    total = WIDTH * HEIGHT
    print(f"  Haar roundtrip: {haar_match}/{total} "
          f"({'OK' if haar_match == total else 'LOSSY: ' + str(total - haar_match) + ' diffs'})")

    print("\nCompressing...")
    compressed = compress(coeffs)
    ratio = len(compressed) * 100 // total
    print(f"Compressed: {len(compressed)} bytes ({ratio}%)")

    outfile = outdir / "spectrum.rgbiv"
    write_rgbiv(str(outfile), palette, compressed, encrypted)
    print(f"Written: {outfile} ({outfile.stat().st_size} bytes)")

    # Full decode verification
    print("\n--- Full Decode Verification ---")
    dec_coeffs = decode_crle(compressed, WIDTH, HEIGHT)
    dec_pixels = haar_inverse_image(dec_coeffs, WIDTH, HEIGHT, DATA_ROW_IDX)
    full_match = sum(1 for a, b in zip(flat, dec_pixels) if a == b)
    print(f"  Full roundtrip: {full_match}/{total} "
          f"({'OK' if full_match == total else 'ERRORS: ' + str(total - full_match)})")

    # Flag verification
    print("\n--- Flag Decryption ---")
    enc_indices = dec_pixels[DATA_ROW_IDX * WIDTH: DATA_ROW_IDX * WIDTH + len(encrypted)]
    enc_bytes = bytes(idx - DATA_PALETTE_OFFSET for idx in enc_indices)
    decrypted = bytes(b ^ XOR_KEY[i % len(XOR_KEY)] for i, b in enumerate(enc_bytes))
    print(f"  Recovered: {decrypted.decode('ascii')}")
    assert decrypted.decode('ascii') == FLAG, "Flag mismatch!"
    print("  Flag verified OK!")

    if verify and HAS_PIL:
        print("\n--- Verification Images ---")

        img = decode_to_image(compressed, palette)
        fn = outdir / "verify_decoded.png"
        img.save(str(fn))
        print(f"  {fn}")

        cheat = build_cheat_reference(palette)
        fn = outdir / "verify_cheat.png"
        cheat.save(str(fn))
        print(f"  {fn}")

    print(f"\n{'=' * 60}")
    print(f"  Flag: {FLAG}")
    print(f"  Numbers: {CIRCLE_NUMBERS}")
    print(f"  XOR key: {list(XOR_KEY)}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
