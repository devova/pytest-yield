import sys

import itertools
import pytest

from _pytest.runner import (
    call_and_report, call_runtest_hook,
    check_interactive_exception, show_test_item
)
from _pytest.python import Generator

from collections import deque
from mark import Report


if pytest.__version__ > '3.4':
    def pytest_configure(config):
        import newhooks
        config.pluginmanager.add_hookspecs(newhooks)
else:
    def pytest_addhooks(pluginmanager):
        import newhooks
        pluginmanager.add_hookspecs(newhooks)


def pytest_sessionstart(session):
    session.concurrent_markers = list(
        itertools.chain(*session.config.hook.pytest_collect_concurrent_markers()))


@pytest.hookimpl(hookwrapper=True)
def pytest_pycollect_makeitem(collector, name, obj):
    outcome = yield
    item = outcome.get_result()
    if isinstance(item, Generator) and (
            getattr(obj, 'is_concurrent', False) or (
                hasattr(obj, 'func_doc') and
                any(marker in obj.func_doc for marker in item.session.concurrent_markers))):
        obj.is_concurrent = True
        items = list(collector._genfunctions(name, obj))
        for item in items:
            item.was_already_run = False
            item.was_finished = False
        outcome.force_result(items)


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items):
    for item in items:
        item.is_concurrent = getattr(item.obj, 'is_concurrent', False)
        if item.is_concurrent and hasattr(item.obj, 'upstream'):
            upstream_name = getattr(item.obj, 'upstream')
            for upstream_item in items:
                if upstream_item.name == upstream_name:
                    upstream_item.downstream = item
                    item.upstream = upstream_item
                    break
            if not hasattr(item, 'upstream'):
                # someone did a mistake in name
                # lets figure out is there any parametrized tests
                msg = 'Could not find upstream test with name `%s`.' % upstream_name
                for potential_upstream_item in items:
                    if potential_upstream_item.name.startswith(upstream_name):
                        msg += ' Maybe you want to specify `%s`?' % potential_upstream_item.name
                        break
                raise Exception(msg)
        if item.is_concurrent and hasattr(item.obj, 'downstream'):
            downstream_name = getattr(item.obj, 'downstream')
            for downstream_item in items:
                if downstream_item.name == downstream_name:
                    downstream_item.upstream = item
                    item.downstream = downstream_item
                    break
            if not hasattr(item, 'downstream'):
                # someone did a mistake in name
                # lets figure out is there any parametrized tests
                msg = 'Could not find downstream test with name `%s`.' % downstream_name
                for potential_downstream_item in items:
                    if potential_downstream_item.name.startswith(downstream_name):
                        msg += ' Maybe you want to specify `%s`?' % potential_downstream_item.name
                        break
                raise Exception(msg)


def pytest_runtestloop(session):
    if (session.testsfailed and
            not session.config.option.continue_on_collection_errors):
        raise session.Interrupted(
            "%d errors during collection" % session.testsfailed)

    if session.config.option.collectonly:
        return True
    has_items = len(session.items) > 0
    items = deque(session.items)
    if has_items:
        items[-1].last_in_round = True
    while has_items:
        try:
            item = items.popleft()
            upstream_item = getattr(item, 'upstream', None)
            if upstream_item:
                if upstream_item.is_concurrent and not upstream_item.was_finished:
                    items.append(item)
                    continue
            nextitem = items[0] if len(items) > 0 else None
            item.config.hook.pytest_runtest_protocol(item=item, nextitem=nextitem)
            if session.shouldstop:
                raise session.Interrupted(session.shouldstop)
            if item.is_concurrent and not item.was_finished:
                items.append(item)
            if getattr(item, 'last_in_round', False):
                item.config.hook.pytest_round_finished()
                delattr(item, 'last_in_round')
                if len(items) > 0:
                    items[-1].last_in_round = True
        except IndexError:
            has_items = False
    return True


def pytest_runtest_protocol(item, nextitem):
    if item.is_concurrent:
        if not item.was_already_run:
            item.ihook.pytest_runtest_logstart(
                nodeid=item.nodeid, location=item.location,
            )
        result = yieldtestprotocol(item, nextitem=nextitem)
        try:
            if item.was_finished:
                item.ihook.pytest_runtest_logfinish(
                    nodeid=item.nodeid, location=item.location,
                )
        except AttributeError:  # compatibilyty with pytest==3.0
            pass
        return result


def yieldtestprotocol(item, log=True, nextitem=None):
    hasrequest = hasattr(item, "_request")
    result = True
    if hasrequest and not item._request:
        item._initrequest()
    if not item.was_already_run:
        rep = call_and_report(item, "setup", log)
        if not rep.passed:
            item.was_finished = True
        if rep.passed and item.config.option.setupshow:
            show_test_item(item)
    if item.was_already_run or rep.passed:
        if not item.config.option.setuponly:
            result = yield_and_report(item, "call", log)
    if item.was_finished:
        call_and_report(item, "teardown", log, nextitem=nextitem)
        if hasrequest:
            item._request = False
            item.funcargs = None
    return result


def yield_and_report(item, when, log=True, **kwds):
    call = call_runtest_hook(item, when, **kwds)
    call.when = 'yield'
    hook = item.ihook
    report = hook.pytest_runtest_makereport(item=item, call=call)
    report.result = getattr(call, 'result', [])
    if not item.was_finished and all(not isinstance(res, Report) for res in report.result):
        log = False
    if log:
        hook.pytest_runtest_logreport(report=report)
    if check_interactive_exception(call, report):
        hook.pytest_exception_interact(node=item, call=call, report=report)
    return report


def pytest_report_teststatus(report):
    if report.when == "yield" and report.passed and len(report.result) > 0:
        letter = 'y'
        word = report.result[0] if isinstance(report.result[0], Report) else ''
        return report.outcome, letter, word


def pytest_runtest_call(item):
    try:
        if item.is_concurrent:
            if not item.was_already_run:
                item.concurrent_test = item.ihook.pytest_pyfunc_call(pyfuncitem=item)
            try:
                res = item.concurrent_test.next()
                item.was_already_run = True
            except StopIteration:
                item.was_finished = True
                res = None
        else:
            item.runtest()
            res = None
        return res
    except Exception:
        item.was_finished = True
        # Store trace info to allow postmortem debugging
        type, value, tb = sys.exc_info()
        tb = tb.tb_next  # Skip *this* frame
        sys.last_type = type
        sys.last_value = value
        sys.last_traceback = tb
        del tb  # Get rid of it in this namespace
        raise


def pytest_pyfunc_call(pyfuncitem):
    testfunction = pyfuncitem.obj
    if pyfuncitem._isyieldedfunction():
        res = testfunction(*pyfuncitem._args)
    else:
        funcargs = pyfuncitem.funcargs
        testargs = {}
        for arg in pyfuncitem._fixtureinfo.argnames:
            testargs[arg] = funcargs[arg]
        res = testfunction(**testargs)
    return res


def pytest_round_finished():
    pass


def pytest_collect_concurrent_markers():
    return 'concurrent',