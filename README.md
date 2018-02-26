*Here is output of running tests*
```bash
(venv) vtrotsys@VTROTSYS-M-P58Y ~/P/c/pytest-yield> pytest -vv -s examples/
============================================================ test session starts ============================================================
platform darwin -- Python 2.7.14, pytest-3.4.1, py-1.5.2, pluggy-0.6.0 -- /Users/vtrotsys/Projects/cloudlock/connectors_tests/venv/bin/python2.7
cachedir: .pytest_cache
rootdir: /Users/vtrotsys/Projects/cloudlock/pytest-yield, inifile:
collected 4 items

examples/test_concurent.py::test_1 PASSED
examples/test_concurent.py::TestClass::test_3 PASSED
examples/test_concurent.py::TestClass::test_4 <- pytest_yield.py Hello World3
examples/test_concurent.py::test_2 <- pytest_yield.py Hello World
examples/test_concurent.py::TestClass::test_4 <- pytest_yield.py Hello World4
examples/test_concurent.py::test_2 <- pytest_yield.py Hello Worl2
examples/test_concurent.py::TestClass::test_4 <- pytest_yield.py PASSED
examples/test_concurent.py::test_2 <- pytest_yield.py PASSED

========================================================= 8 passed in 4.03 seconds ==========================================================
```
