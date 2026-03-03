# Challenge 19: Roy G Biv

**Tier 5 — Expert (1000 pts)**

You've intercepted a mysterious file encoded in the `.rgbiv` image format. Your mission: decode it, understand what you see, and extract the hidden flag.

## The File

`spectrum.rgbiv` — a binary image file using a custom format with CRLE compression.

## .rgbiv Format Specification

### Header (32 bytes)

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0x00 | 4 | magic | `"RGBI"` (0x52474249) |
| 0x04 | 2 | version | 0x0001 (uint16 BE) |
| 0x06 | 2 | width | Image width in pixels (uint16 BE) |
| 0x08 | 2 | height | Image height in pixels (uint16 BE) |
| 0x0A | 1 | palette_size | Number of palette entries (0 = 256) |
| 0x0B | 1 | compression | 1 = CRLE |
| 0x0C | 1 | flags | Bit flags (see below) |
| 0x0D | 1 | data_row_index | Row containing encoded data (if has_data_row=1) |
| 0x0E | 2 | data_row_length | Byte count of encoded data in that row (uint16 BE) |
| 0x10 | 4 | compressed_size | Size of compressed pixel data (uint32 BE) |
| 0x14 | 4 | checksum | CRC-32 of bytes 0x00–0x13 |
| 0x18 | 8 | reserved | Zeros |

### Flags (byte at 0x0C)

| Bit | Name | Description |
|-----|------|-------------|
| 0 | has_data_row | 1 = a row contains encoded data |
| 1 | delta_mode | 0 = clamp to [0,255]; 1 = wrap (mod 256) |
| 2 | fill_order | 0 = emit v1,v2; 1 = emit v2,v1 |
| 3–7 | reserved | Must be 0 |

**Important:** The flags in the file header indicate the *default* configuration. Other combinations may produce different results.

### Palette

Immediately follows the header. Each entry is 3 bytes (R, G, B). The number of entries is given by `palette_size` (0 means 256).

Pixels are 8-bit palette indices. Index 0 is typically black, index 1 is white.

### CRLE Compression

Byte-oriented compression. Each instruction starts with one byte where the top 3 bits encode the opcode and the bottom 5 bits encode a base count N.

**Length extension:** If N = 31, read additional bytes. Add each byte to N. Stop when a byte less than 255 is read.

| Bits 7–5 | Opcode | Parameters | Output | Description |
|----------|--------|------------|--------|-------------|
| 000 | LITERAL | N+1 raw bytes | Copy bytes to output | Raw pixel data |
| 001 | REPEAT | 1 byte: val | val repeated N+1 times | Run-length encoding |
| 010 | COPY_PREV | 2 bytes: offset (BE) | N+1 bytes from output[pos−offset] | Back-reference |
| 011 | DELTA_RUN | 1 byte: start, 1 byte: delta (signed int8) | N+1 values: start + i×delta | Arithmetic sequence. **Overflow behavior depends on `delta_mode` flag.** |
| 100 | FILL_PAIR | 1 byte: v1, 1 byte: v2 | 2×(N+1) alternating bytes | Alternating pair fill. **Pair order depends on `fill_order` flag.** |
| 101 | NESTED_REPEAT | Next instruction (decoded once) | Inner output repeated N+1 times | Nested repetition |
| 110 | ROW_COPY | 2 bytes: row_width (BE) | N+1 bytes from output[pos−row_width] | Copy from previous row |
| 111 | END | None | — | Stop decoding |

#### DELTA_RUN Details

Produces the sequence: `start`, `start + delta`, `start + 2×delta`, ..., `start + N×delta`

Where `delta` is a **signed** 8-bit integer (values 128–255 represent −128 to −1).

- **delta_mode = 0 (clamp):** Each value is clamped to [0, 255]
- **delta_mode = 1 (wrap):** Each value is taken modulo 256

#### FILL_PAIR Details

Produces 2×(N+1) bytes of alternating values:

- **fill_order = 0:** v1, v2, v1, v2, v1, v2, ...
- **fill_order = 1:** v2, v1, v2, v1, v2, v1, ...

### Data Row

If `has_data_row` is set, one row of the image contains encoded data mixed with the visual content. The row index and data byte count are specified in the header. The data bytes are stored as palette indices starting from the beginning of that row.

## Hints

1. The header contains more than just dimensions.
2. Try different flag combinations. Not all configurations produce the same image.
3. Look carefully at what you see. Some things are easier to read than others.
4. The image contains seven visual elements. Each holds a two-digit number.
5. The numbers form a key. The key unlocks the data.

## Submission

Submit the flag in the format `CTF{...}`.

## Requirements

```
pip install Pillow>=9.0
```

Pillow is only needed if you want to output PNG images from your decoder. The core decoding requires only Python standard library.
