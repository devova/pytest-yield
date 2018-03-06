def concurrent(*args, **kwargs):
    def _concurrent(func):
        func.is_concurrent = True
        func.__dict__.update(**kwargs)
        return func
    if len(args) == 1 and callable(args[0]):
        # No arguments, this is the decorator
        return _concurrent(args[0])
    else:
        return _concurrent

class Report(str):
    pass