import contextlib
import functools
import sys
import threading
import unittest
from test.support import import_fresh_module

OS_ENV_LOCK = threading.Lock()
TZPATH_LOCK = threading.Lock()
TZPATH_TEST_LOCK = threading.Lock()


@functools.lru_cache(1)
def get_modules():
    # The standard import_fresh_module approach seems to be somewhat buggy
    # when it comes to C imports, so in the short term, we will do a little
    # module surgery to test this.
    py_module, c_module = (import_fresh_module("zoneinfo") for _ in range(2))

    from zoneinfo import _zoneinfo as py_zoneinfo
    from zoneinfo import _czoneinfo as c_zoneinfo

    py_module.ZoneInfo = py_zoneinfo.ZoneInfo
    c_module.ZoneInfo = c_zoneinfo.ZoneInfo

    return py_module, c_module


@contextlib.contextmanager
def set_zoneinfo_module(module):
    """Make sure sys.modules["zoneinfo"] refers to `module`.

    This is necessary because `pickle` will refuse to serialize
    an type calling itself `zoneinfo.ZoneInfo` unless `zoneinfo.ZoneInfo`
    refers to the same object.
    """

    NOT_PRESENT = object()
    old_zoneinfo = sys.modules.get("zoneinfo", NOT_PRESENT)
    sys.modules["zoneinfo"] = module
    yield
    if old_zoneinfo is not NOT_PRESENT:
        sys.modules["zoneinfo"] = old_zoneinfo


class ZoneInfoTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.klass = cls.module.ZoneInfo
        super().setUpClass()

    @contextlib.contextmanager
    def tzpath_context(self, tzpath, lock=TZPATH_LOCK):
        with lock:
            old_path = self.module.TZPATH
            try:
                self.module.set_tzpath(tzpath)
                yield
            finally:
                self.module.set_tzpath(old_path)