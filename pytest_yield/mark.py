def concurrent(func):
    func.is_concurrent = True
    return func


class Report(str):
    pass