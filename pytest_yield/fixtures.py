import inspect
import functools
import py

from _pytest.compat import NOTSET, getlocation, exc_clear
from _pytest.fixtures import FixtureRequest, scopes, SubRequest
from pytest import fail


class YieldSubRequest(SubRequest):

    def __init__(self, *args, **kwargs):
        super(YieldSubRequest, self).__init__(*args, **kwargs)
        self._fixturedef_finalizers = []

    def addfinalizer(self, finalizer):
        self._fixturedef_finalizers.append(finalizer)


class YieldFixtureRequest(FixtureRequest):

    def __init__(self, pyfuncitem):
        super(YieldFixtureRequest, self).__init__(pyfuncitem)
        self.fixturedef_cached_result = {}

    def cached_result_obj_for_function(self):
        return self

    def cached_result_obj_for_class(self):
        return self.node.cls

    def cached_result_obj_for_module(self):
        return self.node.module

    def _compute_fixture_value(self, fixturedef):
        """
        Creates a SubRequest based on "self" and calls the execute method of the given fixturedef object. This will
        force the FixtureDef object to throw away any previous results and compute a new fixture value, which
        will be stored into the FixtureDef object itself.

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

        subrequest = YieldSubRequest(
            self, scope, param, param_index, fixturedef)

        # check if a higher-level scoped fixture accesses a lower level one
        subrequest._check_scope(argname, self.scope, scope)

        # clear sys.exc_info before invoking the fixture (python bug?)
        # if its not explicitly cleared it will leak into the call
        exc_clear()

        try:
            # call the fixture function
            cache_store = getattr(
                self, 'cached_result_obj_for_%s' % scope, lambda: None)()
            if hasattr(fixturedef, 'cached_result'):
                fixturedef_cached_result = getattr(
                    cache_store, '_fixturedef_cached_result_%s' % argname, None)
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
                setattr(cache_store, '_fixturedef_cached_result_%s' % argname,
                        getattr(fixturedef, 'cached_result', None))
