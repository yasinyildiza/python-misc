import sipdecoder
import siprequest
import sipresponse

class SipHandler(object):

    def __init__(self):
        pass

    def handle(self, content):
        sip_message = sipdecoder.decode(content)
        messages = []
        return messages
