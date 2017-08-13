class Notifier(object):

    def __init__(self):
        self.observers = []

    def register(self, observer):
        self.observers.append(observer)

    def unregister(self, observer):
        pass

    def notify(self, observer, method, *args):
        if hasattr(observer, method):
            f = getattr(observer, method)
            new_args = []
            new_args.append(self)
            for arg in args:
                new_args.append(arg)
            f(*new_args)
        else:
            pass

    def notify_all(self, method, *args):
        for observer in self.observers:
            self.notify(observer, method, *args)
