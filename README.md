### What?
**pytest_yield** is a plugin that allows run tests as coroutines.
This means that a few tests can being executing at same time.

### Why?
This is first question that engineers asking.
General theory said us that each test have to be run separetelly and independently,
meaning without any influence on other tests.
This plugin breaks this rules at all. 

So why do we need it?

Imagine we have integration tests where each test execution takes very long time.
For examle test should wait for some reactions depend on initial actions.
This waiting could take up to e.g. 1 hour. And even after it we need perform next action from scenario and wait more.
Syncronous execution of all tests, one by one, will take huge amout of time.
But what if all test cases are independent, so actions of _test1_ does not influence results of _test2_.
Than make sense some how skip waiting prosess of _test1_ and switch execution context to _test2_.
This actually what **pytest_yield** doing.

### How?
Each concurrent test is suppose to be a generator.
Switching of execution context is performed after each `yield`. Test add itself to the end of a deueue if generator is not exausted yet.
After new one is pulled from left side of dequeue. 
Assume test have `N` yields, tahn it will be `N` times rescheduled.

### Do not use with
Tests that are cross dependent. Most particular example is unittests with mocks, if _test1_ mock some method, this will be implicitly mocked in _test2_ also.