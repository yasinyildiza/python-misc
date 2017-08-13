import sipheader

class SipMessage(object):

    NEW_LINE = '\r\n'

    MESSAGE_TYPE_REQUEST  = 'REQUEST'
    MESSAGE_TYPE_RESPONSE = 'RESPONSE'

    def __init__(self):

        # request or response
        self.message_type = None

        # global sip version
        self.sip_version  = None

        # request intro
        self.method = None
        self.uri    = None

        # response intro
        self.response_code = None
        self.reason_phrase = None

        # header list
        self.headers = []

        # message content
        self.content = None

        # raw message
        self.raw = None

    def set_message_type(self, message_type):
        self.message_type = message_type

    def set_sip_version(self, sip_version):
        self.sip_version = sip_version

    def set_content(self, content):
        self.content = content

    def add_headerx(self, header):
        self.headers.append(header)

    def add_header(self, name, value):
        header = sipheader.SipHeader()
        header.set_name(name)
        header.set_value(value)
        self.add_headerx(header)

    def decode_intro(self, s1, s2, s3):
        raise NotImplementedError

    def encode_intro(self):
        raise NotImplementedError

    def describe_intro(self):
        raise NotImplementedError

    def decode(self, content):
        self.raw = content

        lines = content.splitlines()

        if len(lines) == 0:
            return

        i = 0
        intro = lines[i]
        i += 1

        intro_s = intro.strip().split()

        if len(intro_s) != 3:
            return

        self.decode_intro(intro_s[0], intro_s[1], intro_s[2])

        content_started = False
        content_lines = []
        while i < len(lines):
            line = lines[i]

            if content_started:
                content_lines.append(line)
            else:
                if len(line.strip()) == 0:
                    content_started = True
                else:
                    header = sipheader.SipHeader()
                    header.decode(line)
                    self.headers.append(header)

            i += 1

        self.content = self.NEW_LINE.join(content_lines)

    def encode(self):
        lines = []

        line = self.encode_intro()
        lines.append(line)
        lines.append(self.NEW_LINE)

        for header in self.headers:
            line = header.encode()
            lines.append(line)
            lines.append(self.NEW_LINE)

        lines.append(self.NEW_LINE)

        lines.append(self.content or '')

        lines.append(self.NEW_LINE)

        return ''.join(lines)

    def describe_field(self, name, value):
        print('### {name} ###'.format(name=name))
        print(value)

    def describe(self):
        print('*** {type} ***'.format(type=self.message_type))

        self.describe_intro()

        print('--- HEADERS ({count}) ---'.format(count=len(self.headers)))

        for header in self.headers:
            header.describe()

        self.describe_field('CONTENT', self.content)

        print('*** END ***')
