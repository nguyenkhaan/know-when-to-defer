"""Streaming helpers for the LMRC JSON files, which are too large to load whole."""

from typing import BinaryIO


class NanToNullReader:
    """File wrapper that rewrites the bare token `NaN` to `null`, chunk by chunk.

    Holds back a trailing "N"/"Na" so a `NaN` split across chunks is still caught, and never
    returns more than `size` bytes (ijson's C backend drops anything beyond the requested
    size, and the rewrite makes the text longer). Safe here because LMRC never contains the
    text `NaN` inside a JSON string.

    `read()` without a size returns at most one chunk, not the whole stream: ijson always
    passes a size and reads until it gets `b""`.
    """

    def __init__(self, raw: BinaryIO, chunk_size: int = 1 << 20):
        self._raw = raw
        self._chunk = chunk_size
        self._tail = b""  # unconverted bytes that may start a split NaN
        self._out = b""  # converted bytes not yet handed to the caller
        self._eof = False

    def _fill(self, want: int) -> None:
        while not self._out and not self._eof:
            data = self._raw.read(want)
            # Rewrite before looking at the end of the buffer: otherwise the "Na" of `NaNa`
            # would be held back and cut a complete `NaN` in two.
            buf = (self._tail + data).replace(b"NaN", b"null")
            if not data:
                self._eof, keep = True, 0
            elif buf.endswith(b"Na"):
                keep = 2
            elif buf.endswith(b"N"):
                keep = 1
            else:
                keep = 0
            self._tail = buf[len(buf) - keep :]
            self._out += buf[: len(buf) - keep]

    def read(self, size: int | None = -1) -> bytes:
        if size == 0:  # ijson probes with read(0) to detect bytes vs str: consume nothing
            return b""
        want = self._chunk if size is None or size < 0 else size
        self._fill(want)
        out, self._out = self._out[:want], self._out[want:]
        return out
