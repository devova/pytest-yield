import inspect
import functools
import py
import sys

from _pytest.compat import NOTSET, getlocation, exc_clear
from _pytest.fixtures import FixtureDef, FixtureRequest, scopes, SubRequest
from pytest import fail


class YieldFixtureDef(FixtureDef):

    @staticmethod
    def finish(self, request):
        exceptions = []
        try:
            _finalizers = getattr(self, '_finalizers_per_item', {}).get(
                request.node, self._finalizers)
            while _finalizers:
                try:
                    func = _finalizers.pop()
                    func()
                except:  # noqa
                    exceptions.append(sys.exc_info())
            if exceptions:
                e = exceptions[0]
                del exceptions  # ensure we don't keep all frames alive because of the traceback
                py.builtin._reraise(*e)

        finally:
            hook = self._fixturemanager.session.gethookproxy(request.node.fspath)
            hook.pytest_fixture_post_finalizer(fixturedef=self, request=request)
            # even if finalization fails, we invalidate
            # the cached fixture value and remove
            # all finalizers because they may be bound methods which will
            # keep instances alive
            if hasattr(self, "cached_result"):
                del self.cached_result
            del _finalizers[:]

    @staticmethod
    def addfinalizer(self, finalizer, colitem=None):
        if colitem:
            if not hasattr(self, '_finalizers_per_item'):
                self._finalizers_per_item = {}
            self._finalizers_per_item.setdefault(colitem, []).append(finalizer)
        else:
            self._finalizers.append(finalizer)

    @staticmethod
    def execute(self, request):
        # get required arguments and register our own finish()
        # with their finalization
        for argname in self.argnames:
            fixturedef = request._get_active_fixturedef(argname)
            if argname != "request":
                fixturedef.addfinalizer(
                    functools.partial(self.finish, request=request), colitem=request.node)

        my_cache_key = request.param_index
        cached_result = getattr(self, "cached_result", None)
        if cached_result is not None:
            result, cache_key, err = cached_result
            if my_cache_key == cache_key:
                if err is not None:
                    py.builtin._reraise(*err)
                else:
                    return result
            # we have a previous but differently parametrized fixture instance
            # so we need to tear it down before creating a new one
            self.finish(request)
            assert not hasattr(self, "cached_result")

        hook = self._fixturemanager.session.gethookproxy(request.node.fspath)
        return hook.pytest_fixture_setup(fixturedef=self, request=request)


class CachedResultStore(object):
    def cached_store_for_function(self):
        return self

    def cached_store_for_class(self):
        return self.node.cls

    def cached_store_for_module(self):
        return self.node.module

    def cached_store_for_session(self):
        return self.node.session

    def _compute_fixture_value(self, fixturedef):
        """
        Creates a SubRequest based on "self" and calls the execute method of the given
        fixturedef object. This will force the FixtureDef object to throw away any previous results
        and compute a new fixture value, which will be stored into the FixtureDef object itself.

        :param FixtureDef fixturedef:
        """
        # prepare a subrequest object before calling fixture function
        # (latter managed by fixturedef)
        argname = fixturedef.argname
        funcitem = self._pyfuncitem
        scope = fixturedef.scope
        try:
            param = funcitem.callspec.getparam(argname)
        except (AttributeError, ValueError):
            param = NOTSET
            param_index = 0
            if fixturedef.params is not None:
                frame = inspect.stack()[3]
                frameinfo = inspect.getframeinfo(frame[0])
                source_path = frameinfo.filename
                source_lineno = frameinfo.lineno
                source_path = py.path.local(source_path)
                if source_path.relto(funcitem.config.rootdir):
                    source_path = source_path.relto(funcitem.config.rootdir)
                msg = (
                    "The requested fixture has no parameter defined for the "
                    "current test.\n\nRequested fixture '{0}' defined in:\n{1}"
                    "\n\nRequested here:\n{2}:{3}".format(
                        fixturedef.argname,
                        getlocation(fixturedef.func, funcitem.config.rootdir),
                        source_path,
                        source_lineno,
                    )
                )
                fail(msg)
        else:
            # indices might not be set if old-style metafunc.addcall() was used
            param_index = funcitem.callspec.indices.get(argname, 0)
            # if a parametrize invocation set a scope it will override
            # the static scope defined with the fixture function
            paramscopenum = funcitem.callspec._arg2scopenum.get(argname)
            if paramscopenum is not None:
                scope = scopes[paramscopenum]

        subrequest = YieldSubRequest(self, scope, param, param_index, fixturedef)

        # check if a higher-level scoped fixture accesses a lower level one
        subrequest._check_scope(argname, self.scope, scope)

        # clear sys.exc_info before invoking the fixture (python bug?)
        # if its not explicitly cleared it will leak into the call
        exc_clear()

        try:
            # call the fixture function
            cache_store = getattr(
                self, 'cached_store_for_%s' % scope, lambda: None)()
            if cache_store and not hasattr(cache_store, '_fixturedef_cached_results'):
                cache_store._fixturedef_cached_results = dict()
            if hasattr(fixturedef, 'cached_result'):
                fixturedef_cached_result = cache_store._fixturedef_cached_results.get(argname)
                if fixturedef_cached_result:
                    fixturedef.cached_result = fixturedef_cached_result
                else:
                    del fixturedef.cached_result
            fixturedef.execute(request=subrequest)
        finally:
            # if fixture function failed it might have registered finalizers
            self.session._setupstate.addfinalizer(
                functools.partial(
                    fixturedef.finish, request=subrequest),
                subrequest.node)
            cached_result = getattr(fixturedef, 'cached_result', None)
            if cache_store and cached_result:
                cache_store._fixturedef_cached_results[argname] = cached_result


class YieldSubRequest(CachedResultStore, SubRequest):

    def __init__(self, *args, **kwargs):
        super(YieldSubRequest, self).__init__(*args, **kwargs)
        self._fixturedef_finalizers = []

    def addfinalizer(self, finalizer):
        self._fixturedef_finalizers.append(finalizer)


class YieldFixtureRequest(CachedResultStore, FixtureRequest):
    pass
