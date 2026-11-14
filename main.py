# food-picture-01 v5 — "Golden Broth" entrypoint.
#
# The artwork is a JPEG stored as entry.png next to this file. Running
# this program copies it, byte for byte, into the output directory and
# then proves the copy is identical. Nothing is generated, nothing is
# fetched: the picture already exists, this script just delivers it.
#
# Stdlib only (hashlib, os, sys). Plain open() + os.path throughout —
# no pathlib, no shutil, no network, no randomness. Run it twice and
# both runs land on the exact same bytes.
import hashlib
import os
import sys

ARTWORK = "entry.png"
LIMIT_BYTES = 1 << 20
BLOCK = 32768


def digest_of(path):
    # SHA-256 of a whole file, streamed in BLOCK-sized sips.
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            sip = handle.read(BLOCK)
            if not sip:
                break
            hasher.update(sip)
    return hasher.hexdigest()


def jpeg_bounds_ok(path):
    # A whole JPEG starts FFD8 and ends FFD9. Anything else is not the
    # artwork we think it is, and we refuse to ship it.
    with open(path, "rb") as handle:
        head = handle.read(2)
        handle.seek(-2, os.SEEK_END)
        tail = handle.read(2)
    return head == b"\xff\xd8" and tail == b"\xff\xd9"


def pour(src, dst):
    # Chunked copy, returns how many bytes flowed through.
    moved = 0
    with open(src, "rb") as reader, open(dst, "wb") as writer:
        while True:
            sip = reader.read(BLOCK)
            if not sip:
                break
            writer.write(sip)
            moved += len(sip)
    return moved


def pick_outdir(argv):
    # First argument wins; then MAKEFUN_OUTPUT_DIR; then the cwd.
    if len(argv) > 1:
        return argv[1]
    return os.environ.get("MAKEFUN_OUTPUT_DIR") or os.getcwd()


def run(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, ARTWORK)
    outdir = pick_outdir(argv)
    if not os.path.isdir(outdir):
        raise SystemExit("main.py: no such output directory: " + outdir)
    dst = os.path.join(outdir, ARTWORK)
    if os.path.abspath(dst) == os.path.abspath(src):
        raise SystemExit("main.py: output path is the artwork itself: " + dst)
    if not os.path.isfile(src):
        raise SystemExit("main.py: artwork missing: " + src)
    if os.path.getsize(src) > LIMIT_BYTES:
        raise SystemExit("main.py: artwork over 1 MiB: " + src)
    if not jpeg_bounds_ok(src):
        raise SystemExit("main.py: artwork is not a whole JPEG: " + src)
    wanted = digest_of(src)
    moved = pour(src, dst)
    if moved > LIMIT_BYTES:
        raise SystemExit("main.py: output over 1 MiB: " + dst)
    if not jpeg_bounds_ok(dst):
        raise SystemExit("main.py: output is not a whole JPEG: " + dst)
    got = digest_of(dst)
    if got != wanted:
        raise SystemExit("main.py: copy mismatch, output differs from artwork")
    print("entry.png written (" + str(moved) + " bytes), sha256 " + got)


if __name__ == "__main__":
    run(sys.argv)
