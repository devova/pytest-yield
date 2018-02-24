class Hooks:
    def pytest_round_finished(self):
        pass

def pytest_configure(config):
    config.pluginmanager.add_hookspecs(Hooks)