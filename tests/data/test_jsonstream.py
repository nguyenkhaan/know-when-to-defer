import io
from itertools import pairwise

import ijson
import pytest

from kwd.data.jsonstream import NanToNullReader

DOC = b'{"a": NaN, "b": [NaN, 1.5, NaN], "c": {"d": NaN}, "Na": "N"}'
PARSED = {"a": None, "b": [None, 1.5, None], "c": {"d": None}, "Na": "N"}


class SplitRaw:
    """Raw stream that returns short reads, cutting the data at fixed offsets."""

    def __init__(self, data: bytes, *cuts: int):
        bounds = [0, *cuts, len(data)]
        self._parts = [data[a:b] for a, b in pairwise(bounds)]

    def read(self, size: int = -1) -> bytes:
        while self._parts:
            part = self._parts.pop(0)
            if part:
                self._parts.insert(0, part[size:])
                return part[:size]
        return b""


def drain(reader: NanToNullReader, size: int) -> list[bytes]:
    chunks = []
    while chunk := reader.read(size):
        chunks.append(chunk)
    return chunks


@pytest.mark.parametrize("size", [1, 2, 3, 4, 1 << 20])
def test_nan_rewritten_for_any_read_size(size):
    chunks = drain(NanToNullReader(io.BytesIO(DOC)), size)
    assert b"".join(chunks) == DOC.replace(b"NaN", b"null")


@pytest.mark.parametrize("cut", range(len(DOC) + 1))
def test_nan_rewritten_at_every_chunk_boundary(cut):
    reader = NanToNullReader(SplitRaw(DOC, cut))
    assert b"".join(drain(reader, 1 << 20)) == DOC.replace(b"NaN", b"null")


@pytest.mark.parametrize("buf_size", [1, 2, 3, 4, 1 << 16])
def test_ijson_parses_rewritten_stream(buf_size):
    reader = NanToNullReader(io.BytesIO(DOC))
    assert dict(ijson.kvitems(reader, "", use_float=True, buf_size=buf_size)) == PARSED


def test_read_zero_returns_empty_and_consumes_nothing():
    reader = NanToNullReader(io.BytesIO(DOC))
    assert reader.read(0) == b""
    assert b"".join(drain(reader, 7)) == DOC.replace(b"NaN", b"null")


@pytest.mark.parametrize("size", [1, 2, 3, 4, 5, 64])
def test_read_never_exceeds_size_when_rewrite_expands(size):
    chunks = drain(NanToNullReader(io.BytesIO(b"NaN" * 50)), size)
    assert all(len(chunk) <= size for chunk in chunks)
    assert b"".join(chunks) == b"null" * 50


@pytest.mark.parametrize("data", [b"N", b"Na", b"[1]N", b"[1]Na", b"NaNN", b"NaNNa"])
@pytest.mark.parametrize("size", [1, 2, 3, 1 << 20])
def test_trailing_partial_token_is_kept(data, size):
    chunks = drain(NanToNullReader(io.BytesIO(data)), size)
    assert b"".join(chunks) == data.replace(b"NaN", b"null")


@pytest.mark.parametrize("data", [b"NaNa", b"NNaNa", b"NaNaN", b"NaNaNa", b"NNaNN", b"NaNNaN"])
def test_adjacent_partial_tokens_match_whole_stream_rewrite(data):
    expected = data.replace(b"NaN", b"null")
    for cut in range(len(data) + 1):
        assert b"".join(drain(NanToNullReader(SplitRaw(data, cut)), 1 << 20)) == expected
    for size in (1, 2, 3, 4):
        assert b"".join(drain(NanToNullReader(io.BytesIO(data)), size)) == expected


def test_read_without_size_returns_at_most_one_chunk():
    reader = NanToNullReader(io.BytesIO(b"x" * 10), chunk_size=4)
    assert reader.read() == b"xxxx"
    assert reader.read(-1) == b"xxxx"
    assert reader.read(None) == b"xx"
    assert reader.read() == b""
