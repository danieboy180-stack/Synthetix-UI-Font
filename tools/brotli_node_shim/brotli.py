"""Minimal `brotli` module backed by Node's built-in zlib brotli (Google's brotli library).

Why: the build sandbox has no `pip install brotli` and no network. fontTools' WOFF2 writer needs only
compress(data, mode=MODE_FONT) and decompress(data). If the real `brotli` wheel is installed, DO NOT put this
directory on PYTHONPATH. WOFF2 bytes depend on the compressor build, so the WOFF2 hashes in SHA256SUMS record
the node version used (see build/config.json -> toolchain in reports/build-environment.json).
"""
import subprocess
MODE_GENERIC, MODE_TEXT, MODE_FONT = 0, 1, 2
_C = ("const z=require('zlib');const c=z.constants;const d=require('fs').readFileSync(0);"
      "const q=+process.argv[1],m=+process.argv[2],w=+process.argv[3];"
      "process.stdout.write(z.brotliCompressSync(d,{params:{[c.BROTLI_PARAM_MODE]:m,[c.BROTLI_PARAM_QUALITY]:q,"
      "[c.BROTLI_PARAM_LGWIN]:w,[c.BROTLI_PARAM_SIZE_HINT]:d.length}}));")
_D = "process.stdout.write(require('zlib').brotliDecompressSync(require('fs').readFileSync(0)));"


def compress(data, mode=MODE_GENERIC, quality=11, lgwin=22, lgblock=0):
    return subprocess.run(['node', '-e', _C, str(quality), str(mode), str(lgwin)], input=bytes(data), capture_output=True, check=True).stdout


def decompress(data):
    return subprocess.run(['node', '-e', _D], input=bytes(data), capture_output=True, check=True).stdout
