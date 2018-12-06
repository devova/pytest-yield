========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - tests
      - | |drone|
    * - package
      - | |version| |supported-versions| |supported-implementations|

.. |drone| image:: https://cloud.drone.io/api/badges/devova/pytest-yield/status.svg
    :alt: Drone-CI Build Status
    :target: https://cloud.drone.io/devova/pytest-yield


.. |version| image:: https://img.shields.io/pypi/v/pytest-yield.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/pytest-yield

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/pytest-yield.svg
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/pytest-yield

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/pytest-yield.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/pytest-cov

.. end-badges

What?
~~~~~

**pytest\_yield** is a plugin that allows run tests as coroutines. This
means that a few tests can being executing at same time.

Why?
~~~~

This is first question that engineers asking. General theory said us
that each test have to be run separetelly and independently, meaning
without any influence on other tests. This plugin breaks this rules at
all.

So why do we need it?

Imagine we have integration tests where each test execution takes very
long time. For examle test should wait for some reactions depend on
initial actions. This waiting could take up to e.g. 1 hour. And even
after it we need perform next action from scenario and wait more.
Syncronous execution of all tests, one by one, will take huge amout of
time. But what if all test cases are independent, so actions of *test1*
does not influence results of *test2*. Than make sense some how skip
waiting prosess of *test1* and switch execution context to *test2*. This
actually what **pytest\_yield** doing.

How?
~~~~

Each concurrent test is suppose to be a generator. Switching of
execution context is performed after each ``yield``. Test add itself to
the end of a deueue if generator is not exausted yet. After new one is
pulled from left side of dequeue. Assume test have ``N`` yields, tahn it
will be ``N`` times rescheduled.

|image2|

Do not use with
~~~~~~~~~~~~~~~

Tests that are cross dependent. Most
particular example is unittests with mocks, if *test1* mock some method,
this will be implicitly mocked in *test2* also.

.. |image2| image:: https://raw.githubusercontent.com/devova/pytest-yield/b0c7aa058df5f50cb9a05272fce01fc62a78bbee/how-it-works-pytest-yield.svg?sanitize=true
