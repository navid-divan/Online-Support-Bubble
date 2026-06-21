from osb.adapters.storage import InMemoryStorage


def test_append_read_scan():
    s = InMemoryStorage()
    h0, h1 = s.append("a"), s.append("b")
    assert (h0, h1) == (0, 1)
    assert s.read(0) == "a"
    assert s.scan() == [(0, "a"), (1, "b")]


def test_read_out_of_range_is_none():
    s = InMemoryStorage()
    assert s.read(0) is None
    assert s.read(-1) is None


def test_overwrite():
    s = InMemoryStorage()
    h = s.append("a")
    assert s.overwrite(h, "z")
    assert s.read(h) == "z"
    assert not s.overwrite(99, "x")


def test_namespaced_kv():
    s = InMemoryStorage()
    s.put("ns", b"k", 7)
    assert s.get("ns", b"k") == 7
    assert s.contains("ns", b"k")
    assert not s.contains("ns", b"missing")
    assert s.get("other", b"k") is None
    assert s.items("ns") == [(b"k", 7)]
