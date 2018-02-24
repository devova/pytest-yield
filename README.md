*Here is output of running tests*
```bash
(venv)devova@VolodymyrsMBP2 ~/P/p/pytest_coroutines> pytest -vv -s test_concurent.py
=============================================================== test session starts ===============================================================
platform darwin -- Python 2.7.14, pytest-3.4.1, py-1.5.2, pluggy-0.6.0 -- /Users/devova/Projects/py/pytest_coroutines/venv/bin/python2.7
cachedir: .pytest_cache
rootdir: /Users/devova/Projects/py/pytest_coroutines, inifile:
collected 4 items

test_concurent.py::test_2 <- conftest.py Hello World
test_concurent.py::test_1 PASSED
test_concurent.py::TestClass::test_4 <- conftest.py Hello World3
test_concurent.py::TestClass::test_3 PASSED
test_concurent.py::test_2 <- conftest.py Hello Worl2
test_concurent.py::TestClass::test_4 <- conftest.py Hello World4
test_concurent.py::test_2 <- conftest.py FAILED
test_concurent.py::TestClass::test_4 <- conftest.py FAILED

==================================================================== FAILURES =====================================================================
_____________________________________________________________________ test_2 ______________________________________________________________________

item = <Function 'test_2'>

    @hookspec(firstresult=True)
    def pytest_runtest_call(item):
        try:
            if item.is_concurent:
                if not item.was_already_run:
                    item.concurrent_test = item.ihook.pytest_pyfunc_call(pyfuncitem=item)
                try:
>                   res = item.concurrent_test.next()

conftest.py:167:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

    @concurrent
    def test_2():
        yield "Hello World"
        yield "Hello Worl2"
        yield
>       assert 1 == 2
E       assert 1 == 2

test_concurent.py:11: AssertionError
________________________________________________________________ TestClass.test_4 _________________________________________________________________

item = <Function 'test_4'>

    @hookspec(firstresult=True)
    def pytest_runtest_call(item):
        try:
            if item.is_concurent:
                if not item.was_already_run:
                    item.concurrent_test = item.ihook.pytest_pyfunc_call(pyfuncitem=item)
                try:
>                   res = item.concurrent_test.next()

conftest.py:167:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <test_concurent.TestClass object at 0x1111ee6d0>

    @concurrent
    def test_4(self):
        yield self.text % "World3"
        yield self.text % "World4"
        yield
>       assert 2 == 3
E       assert 2 == 3

test_concurent.py:23: AssertionError
======================================================= 2 failed, 6 passed in 0.09 seconds ========================================================
```
