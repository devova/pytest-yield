from _pytest.mark import MarkGenerator


concurrent = MarkGenerator().concurrent


class Report(str):
    pass