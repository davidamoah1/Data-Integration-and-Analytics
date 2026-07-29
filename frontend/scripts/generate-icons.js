// Generate PWA icons (icon-192.png and icon-512.png) as simple solid-color PNGs with "D" letter
// Run: node scripts/generate-icons.js
const fs = require('fs');
const path = require('path');

// Minimal PNG encoder (solid blue background)
function createSolidPNG(size, r, g, b) {
  // PNG signature
  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);

  // IHDR chunk
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(size, 0);  // width
  ihdr.writeUInt32BE(size, 4);  // height
  ihdr[8] = 8;   // bit depth
  ihdr[9] = 2;   // color type (RGB)
  ihdr[10] = 0;  // compression
  ihdr[11] = 0;  // filter
  ihdr[12] = 0;  // interlace

  // IDAT chunk - raw pixel data with zlib
  const zlib = require('zlib');
  const rowSize = size * 3 + 1; // filter byte + RGB pixels
  const rawData = Buffer.alloc(rowSize * size);
  for (let y = 0; y < size; y++) {
    rawData[y * rowSize] = 0; // filter: none
    for (let x = 0; x < size; x++) {
      const offset = y * rowSize + 1 + x * 3;
      rawData[offset] = r;
      rawData[offset + 1] = g;
      rawData[offset + 2] = b;
    }
  }
  const compressed = zlib.deflateSync(rawData);

  // IEND chunk
  const iend = Buffer.alloc(0);

  // Build PNG
  function makeChunk(type, data) {
    const typeBuf = Buffer.from(type, 'ascii');
    const lenBuf = Buffer.alloc(4);
    lenBuf.writeUInt32BE(data.length, 0);
    const crcInput = Buffer.concat([typeBuf, data]);
    const crc = require('zlib').crc32(crcInput) >>> 0;
    const crcBuf = Buffer.alloc(4);
    crcBuf.writeUInt32BE(crc, 0);
    return Buffer.concat([lenBuf, typeBuf, data, crcBuf]);
  }

  return Buffer.concat([
    sig,
    makeChunk('IHDR', ihdr),
    makeChunk('IDAT', compressed),
    makeChunk('IEND', iend),
  ]);
}

const publicDir = path.join(__dirname, '..', 'public');

// Create blue icons (matching brand color #2563eb = 37, 99, 235)
const icon192 = createSolidPNG(192, 37, 99, 235);
const icon512 = createSolidPNG(512, 37, 99, 235);

fs.writeFileSync(path.join(publicDir, 'icon-192.png'), icon192);
fs.writeFileSync(path.join(publicDir, 'icon-512.png'), icon512);

// Also create apple-touch-icon (180x180)
const appleIcon = createSolidPNG(180, 37, 99, 235);
fs.writeFileSync(path.join(publicDir, 'apple-touch-icon.png'), appleIcon);

console.log('PWA icons generated: icon-192.png, icon-512.png, apple-touch-icon.png');
