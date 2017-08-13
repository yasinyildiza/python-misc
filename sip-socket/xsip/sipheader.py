class SipHeader(object):

    SPLITTER = ':'

    def __init__(self):
        self.name  = None
        self.value = None

    def set_name(self, name):
        self.name = name

    def set_value(self, value):
        self.value = value

    def decode(self, line):
        if self.SPLITTER not in line:
            return

        s = line.split(self.SPLITTER)

        self.name = s[0].strip()
        self.value = ''.join(s[1:]).strip()

    def encode(self):
        return '{name}{splitter} {value}'.format(
            name=self.name,
            splitter=self.SPLITTER,
            value=self.value)

    def describe(self):
        print('--- {name} ---'.format(name=self.name))
        print(self.value)
