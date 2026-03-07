# Challenge 19: Roy G Biv

**Tier 5 — Expert (1000 pts)**

You've intercepted a mysterious file encoded in the `.rgbiv` image format. Your mission: decode it, understand what you see, and extract the hidden flag.

## The File

`spectrum.rgbiv` — a binary image file using a custom format with Haar wavelet transform and CRLE compression.

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
| 1 | haar_transform | 1 = pixel data is Haar wavelet transformed |
| 2-7 | reserved | Must be 0 |

### Palette

Immediately follows the header. Each entry is 3 bytes (R, G, B). The number of entries is given by `palette_size` (0 means 256).

Pixels are 8-bit palette indices. Index 0 is typically black, index 1 is white.

### Haar Wavelet Transform

If `haar_transform` is set, the pixel data has been pre-processed with a 1-level row-wise integer Haar wavelet transform using the lifting scheme. The data row (specified by `data_row_index`) is **not** transformed and is stored as raw palette indices.

#### Decoding (Inverse Transform)

After CRLE decompression, each row (except the data row) contains wavelet coefficients that must be inverse-transformed to recover the original palette indices.

Each transformed row of width W is laid out as:

```
[s[0], s[1], ..., s[W/2-1], d_stored[0], d_stored[1], ..., d_stored[W/2-1]]
```

Where:
- `s[i]` are the **smooth** (approximation) coefficients
- `d_stored[i]` are the **detail** (difference) coefficients, stored with an offset of +128

To recover the original pixel values:

```
For i = 0 to W/2 - 1:
    d[i] = d_stored[i] - 128          # remove offset to get signed detail
    even[i] = s[i] - (d[i] >> 1)      # arithmetic right shift (toward -inf)
    odd[i]  = d[i] + even[i]
    pixel[2*i]     = even[i]
    pixel[2*i + 1] = odd[i]
```

**Important:** The `>> 1` operation is an **arithmetic right shift** (sign-preserving), equivalent to `floor(d / 2)` for all integers. In Python, this is the standard `>>` operator. In C, use `d >> 1` for signed integers (implementation-defined but works on virtually all platforms), or compute `(d >= 0) ? d/2 : (d-1)/2`.

#### Forward Transform Reference

For completeness, the forward transform (used during encoding) is:

```
For i = 0 to W/2 - 1:
    d[i] = pixel[2*i + 1] - pixel[2*i]     # odd minus even
    s[i] = pixel[2*i] + (d[i] >> 1)        # even plus floor(d/2)
    d_stored[i] = d[i] + 128               # offset for unsigned storage
```

This transform is perfectly reversible with integer arithmetic.

### CRLE Compression

Byte-oriented compression applied to the (possibly wavelet-transformed) data stream. Each instruction starts with one byte where the top 3 bits encode the opcode and the bottom 5 bits encode a base count N.

**Length extension:** If N = 31, read additional bytes. Add each byte to N. Stop when a byte less than 255 is read.

| Bits 7-5 | Opcode | Parameters | Output | Description |
|----------|--------|------------|--------|-------------|
| 000 | LITERAL | N+1 raw bytes | Copy bytes to output | Raw data |
| 001 | REPEAT | 1 byte: val | val repeated N+1 times | Run-length encoding |
| 010 | COPY_PREV | 2 bytes: offset (BE) | N+1 bytes from output[pos-offset] | Back-reference |
| 011 | DELTA_RUN | 1 byte: start, 1 byte: delta (signed int8) | N+1 values: start + i*delta, clamped to [0,255] | Arithmetic sequence |
| 100 | FILL_PAIR | 1 byte: v1, 1 byte: v2 | 2*(N+1) alternating bytes: v1,v2,v1,v2,... | Alternating pair fill |
| 101 | NESTED_REPEAT | Next instruction (decoded once) | Inner output repeated N+1 times | Nested repetition |
| 110 | ROW_COPY | 2 bytes: row_width (BE) | N+1 bytes from output[pos-row_width] | Copy from previous row |
| 111 | END | None | - | Stop decoding |

#### DELTA_RUN Details

Produces the sequence: `start`, `start + delta`, `start + 2*delta`, ..., `start + N*delta`

Where `delta` is a **signed** 8-bit integer (values 128-255 represent -128 to -1). Each value is clamped to [0, 255].

#### FILL_PAIR Details

Produces 2*(N+1) bytes of alternating values: v1, v2, v1, v2, v1, v2, ...

### Data Row

If `has_data_row` is set, one row of the image contains encoded data. The row index and data byte count are specified in the header. The data bytes are stored as palette indices starting from the beginning of that row. **This row is never wavelet-transformed** — its values are raw palette indices even when `haar_transform` is set.

## Hints

1. The specification above is everything you need to decode the binary file.
2. The image holds seven two-digit values.
3. Those values, in order, are the key to the data row.

## Submission

Submit the flag in the format `CTF{...}`.

## Requirements

```
pip install Pillow>=9.0
```

Pillow is only needed if you want to output PNG images from your decoder. The core decoding requires only Python standard library.
