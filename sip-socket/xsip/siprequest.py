import sipmessage

class SipRequest(sipmessage.SipMessage):

    def __init__(self):
        sipmessage.SipMessage.__init__(self)

        self.set_message_type(self.MESSAGE_TYPE_REQUEST)

    def set_method(self, method):
        self.method = method

    def set_uri(self, uri):
        self.uri = uri

    def decode_intro(self, s1, s2, s3):
        self.set_method(s1)
        self.set_uri(s2)
        self.set_sip_version(s3)

    def encode_intro(self):
        return '{method} {uri} {sip_version}'.format(
            method=self.method,
            uri=self.uri,
            sip_version=self.sip_version)

    def describe_intro(self):
        self.describe_field('METHOD', self.method)
        self.describe_field('URI', self.uri)
        self.describe_field('SIP VERSION', self.sip_version)

