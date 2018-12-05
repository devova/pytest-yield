import sys
import six
import py
import pytest
from _pytest.compat import get_real_func

from _pytest.runner import (
    call_and_report, call_runtest_hook,
    check_interactive_exception, show_test_item,
    TestReport)
from _pytest.python import Generator

from collections import deque
from .mark import Report
from pytest_yield.fixtures import YieldFixtureRequest, YieldFixtureDef
from pytest_yield.runner import YieldSetupState


if pytest.__version__ > '3.4':
    @pytest.mark.trylast
    def pytest_configure(config):
        from . import newhooks
        config.pluginmanager.add_hookspecs(newhooks)
        fixture_def = config.pluginmanager.get_plugin('fixtures').FixtureDef
        fixture_def.finish = YieldFixtureDef.finish
        fixture_def.addfinalizer = YieldFixtureDef.addfinalizer
        fixture_def.execute = YieldFixtureDef.execute
else:
    @pytest.mark.trylast
    def pytest_addhooks(pluginmanager):
        from . import newhooks
        pluginmanager.add_hookspecs(newhooks)
        pluginmanager.get_plugin('fixtures').FixtureDef.finish = YieldFixtureDef.finish
        pluginmanager.get_plugin('fixtures').FixtureDef.addfinalizer = YieldFixtureDef.addfinalizer
        pluginmanager.get_plugin('fixtures').FixtureDef.execute = YieldFixtureDef.execute


@pytest.mark.trylast
def pytest_sessionstart(session):
    session._setupstate = YieldSetupState()


@pytest.hookimpl(hookwrapper=True)
def pytest_pycollect_makeitem(collector, name, obj):
    outcome = yield
    item = outcome.get_result()

    concurrent_mark = getattr(obj, 'concurrent', None)
    if not concurrent_mark:
        concurrent_mark = getattr(obj, 'async', None)

    if concurrent_mark:
        if isinstance(item, Generator):
            obj = get_real_func(obj)
            items = list(collector._genfunctions(name, obj))
            outcome.force_result(items)
        else:
            raise Exception(
                'Attempt to set `concurrent` mark for non generator %s' % name)


@pytest.mark.trylast
def pytest_collection_modifyitems(items):
    items_dict = {item.name: item for item in items}
    for item in items:
        item._request = YieldFixtureRequest(item)
        item_chain = item.listchain()
        session = item_chain[0]
        session._setupstate.collection_stack.add_nested(item_chain)

        if pytest.__version__ >= '3.6':
            concurrent_mark = item.get_closest_marker('concurrent')
        else:
            concurrent_mark = getattr(item.obj, 'concurrent', None)
        if not concurrent_mark:
            if pytest.__version__ >= '3.6':
                concurrent_mark = item.get_closest_marker('async')
            else:
                concurrent_mark = getattr(item.obj, 'async', None)

        item.is_concurrent = concurrent_mark or False
        item.was_already_run = False
        item.was_finished = False
        if item.is_concurrent and 'upstream' in concurrent_mark.kwargs:
            upstream_name = concurrent_mark.kwargs['upstream']
            if upstream_name in items_dict:
                item.upstream = items_dict[upstream_name]
            else:
                # someone did a mistake in name
                # lets figure out is there any parametrized tests
                msg = '\nCould not find upstream test with name `%s`.\n' % \
                      upstream_name
                for potential_upstream_name in items_dict.keys():
                    if potential_upstream_name.startswith(upstream_name):
                        msg += 'Maybe you want to specify `%s`?\n' % \
                               potential_upstream_name
                        break
                hook = item.ihook
                report = TestReport(
                    item.nodeid, item.location,
                    {}, 'failed', msg, 'configure',
                    [], 0)
                hook.pytest_runtest_logreport(report=report)
                item.session.shouldstop = True

        if item.is_concurrent and 'downstream' in concurrent_mark.kwargs:
            downstream_name = concurrent_mark.kwargs['downstream']
            if downstream_name in items_dict:
                items_dict[downstream_name].upstream = item
            else:
                # someone did a mistake in name
                # lets figure out is there any parametrized tests
                msg = '\nCould not find downstream test with name `%s`.\n' % \
                      downstream_name
                for potential_downstream_name in items_dict.keys():
                    if potential_downstream_name.startswith(downstream_name):
                        msg += 'Maybe you want to specify `%s`?\n' % \
                               potential_downstream_name
                        break
                hook = item.ihook
                report = TestReport(
                    item.nodeid, item.location,
                    {}, 'failed', msg, 'configure',
                    [], 0)
                hook.pytest_runtest_logreport(report=report)
                item.session.shouldstop = True


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
            if upstream_item and not upstream_item.was_finished:
                items.append(item)
                maybe_last_in_round(item, items)
                continue
            nextitem = items[0] if len(items) > 0 else None
            item.config.hook.pytest_runtest_protocol(item=item, nextitem=nextitem)
            if session.shouldstop:
                raise session.Interrupted(session.shouldstop)
            if item.is_concurrent and not item.was_finished:
                items.append(item)
            maybe_last_in_round(item, items)
        except IndexError:
            has_items = False
    return True


def maybe_last_in_round(item, items):
    if getattr(item, 'last_in_round', False):
        item.config.hook.pytest_round_finished()
        delattr(item, 'last_in_round')
        if len(items) > 0:
            items[-1].last_in_round = True


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
    report.call_result = getattr(item, 'call_result', None)
    if not item.was_finished and report.passed and not isinstance(report.call_result, Report):
        log = False
    if log:
        hook.pytest_runtest_logreport(report=report)
    if check_interactive_exception(call, report):
        hook.pytest_exception_interact(node=item, call=call, report=report)
    return report


def pytest_report_teststatus(report):
    if report.when == "yield" and report.passed and \
            isinstance(report.call_result, Report):
        letter = 'y'
        word = report.call_result
        return report.outcome, letter, word


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    yield
    if not item.is_concurrent:
        item.was_finished = True


def init_generator(pyfuncitem):
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


def pytest_pyfunc_call(pyfuncitem):
    if pyfuncitem.is_concurrent:
        if not pyfuncitem.was_already_run:
            pyfuncitem._concurrent_stack = [init_generator(pyfuncitem)]
            pyfuncitem.was_already_run = True
            try:
                pyfuncitem._concurrent_res = six.next(pyfuncitem._concurrent_stack[-1])
            except Exception:
                pyfuncitem.was_finished = True
                if hasattr(pyfuncitem, '_concurrent_res'):
                    del pyfuncitem._concurrent_res
                raise
            return
        try:
            if hasattr(pyfuncitem._concurrent_res, 'next') or hasattr(
                    pyfuncitem._concurrent_res, '__next__'):
                pyfuncitem._concurrent_stack.append(pyfuncitem._concurrent_res)
                pyfuncitem._concurrent_res = six.next(pyfuncitem._concurrent_stack[-1])
            else:
                pyfuncitem._concurrent_res = pyfuncitem._concurrent_stack[-1].send(
                    pyfuncitem._concurrent_res)
        except StopIteration:
            pyfuncitem._concurrent_stack.pop()
            if len(pyfuncitem._concurrent_stack) == 0:
                pyfuncitem.was_finished = True
                del pyfuncitem._concurrent_res
        except Exception:
            pyfuncitem.was_finished = True
            del pyfuncitem._concurrent_res
            raise
        pyfuncitem.call_result = getattr(pyfuncitem, '_concurrent_res', None)
        return pyfuncitem.call_result


def pytest_fixture_post_finalizer(fixturedef, request):
    exceptions = []
    try:
        while getattr(request, '_fixturedef_finalizers', None):
            try:
                func = request._fixturedef_finalizers.pop()
                func()
            except:  # noqa
                exceptions.append(sys.exc_info())
        if exceptions:
            e = exceptions[0]
            del exceptions  # ensure we don't keep all frames alive because of the traceback
            py.builtin._reraise(*e)

    finally:
        pass


def pytest_round_finished():
    pass
