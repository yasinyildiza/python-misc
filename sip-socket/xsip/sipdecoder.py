import sipmessage
import siprequest
import sipresponse

def decode(content):
    lines = content.splitlines()

    if len(lines) == 0:
        return

    intro = lines[0]

    s = intro.strip().split()

    if len(s) != 3:
        return

    try:
        int(s[0])
    except ValueError:
        message_type = sipmessage.SipMessage.MESSAGE_TYPE_REQUEST
    else:
        message_type = sipmessage.SipMessage.MESSAGE_TYPE_RESPONSE

    if message_type == sipmessage.SipMessage.MESSAGE_TYPE_REQUEST:
        message = siprequest.SipRequest()
    else:
        message = sipresponse.SipResponse()

    message.decode(content)

    return message
