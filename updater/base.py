class BaseUpdater():

    def __init__(self, page) -> None:
        self.page = page

    def update(self):
        raise NotImplementedError()

    def _retrive(self):
        raise NotImplementedError()
