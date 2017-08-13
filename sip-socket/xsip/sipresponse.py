import sipmessage

class SipResponse(sipmessage.SipMessage):

    def __init__(self):
        sipmessage.SipMessage.__init__(self)

        self.set_message_type(self.MESSAGE_TYPE_RESPONSE)

    def set_response_code(self, response_code):
        self.response_code = response_code

    def set_reason_phrase(self, reason_phrase):
        self.reason_phrase = reason_phrase

    def decode_intro(s1, s2, s3):
        self.set_sip_version(s1)
        self.set_response_code(s2)
        self.set_reason_phrase(s3)

    def encode_intro(self):
        return '{sip_version} {response_code} {reason_phrase}'.format(
            sip_version=self.sip_version,
            response_code=self.response_code,
            reason_phrase=self.reason_phrase)

    def describe_intro(self):
        self.describe_field('SIP VERSION', self.sip_version)
        self.describe_field('RESPONSE CODE', self.response_code)
        self.describe_field('REASON PHRASE', self.reason_phrase)
