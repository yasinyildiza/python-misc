import jobject
import sipheader
import siprequest
import sipresponse

PROTOCOL_UDP = 'udp'
PROTOCOL_TCP = 'tcp'

AGENT_CLIENT = 'client'
AGENT_SERVER = 'server'

MESSAGE_REQUEST  = 'request'
MESSAGE_RESPONSE = 'response'

ACTION_SEND = 'send'
ACTION_RECV = 'recv'

class Agent(jobject.JObject):

    KEY_TYPE       = 'type'
    KEY_PROTOCOL   = 'protocol'
    KEY_IP         = 'ip'
    KEY_PORT       = 'port'
    KEY_BUFFERSIZE = 'buffersize'
    KEY_TIMEOUT    = 'timeout'

    def __init__(self):
        jobject.JObject.__init__(self)

        self.type       = None
        self.ip         = None
        self.protocol   = None
        self.port       = None
        self.buffersize = None
        self.timeout    = None

    def parsex(self):
        raise Exception('Agent::parsex method must be implemented by child class')

    def parse(self):
        self.type       = self.get_field(self.KEY_TYPE)
        self.protocol   = self.get_field(self.KEY_PROTOCOL)
        self.port       = self.get_field(self.KEY_PORT, data_types=(int, long))
        self.buffersize = self.get_field(self.KEY_BUFFERSIZE, data_types=(int, long))

        self.parsex()

    def describe_field(self, name, value):
        print('--- {name} ---'.format(name=name))
        print(value)

    def describex(self):
        raise Exception('Agent::describex method must be implemented by child class')

    def describe(self):
        print('### {type} AGENT ###'.format(type=self.type))
        self.describe_field(self.KEY_PROTOCOL, self.protocol)
        self.describex()
        print('###')

class AgentClient(Agent):

    def __init__(self):
        Agent.__init__(self)

    def parsex(self):
        self.ip         = self.get_field(self.KEY_IP)
        self.timeout    = self.get_field(self.KEY_TIMEOUT, data_types=(int, long))

    def describex(self):
        self.describe_field(self.KEY_IP, self.ip)
        self.describe_field(self.KEY_PORT, self.port)
        self.describe_field(self.KEY_BUFFERSIZE, self.buffersize)
        self.describe_field(self.KEY_TIMEOUT, self.timeout)

class AgentServer(Agent):

    def __init__(self):
        Agent.__init__(self)

    def parsex(self):
        pass

    def describex(self):
        self.describe_field(self.KEY_PORT, self.port)
        self.describe_field(self.KEY_BUFFERSIZE, self.buffersize)

class Header(jobject.JObject):

    KEY_NAME  = 'name'
    KEY_VALUE = 'value'

    def __init__(self):
        jobject.JObject.__init__(self)

        self.name  = None
        self.value = None

    def parse(self):
        self.name  = self.get_field(self.KEY_NAME)
        self.value = self.get_field(self.KEY_VALUE)

    def describe(self):
        print('$$$ {name} $$$'.format(name=self.name))
        print(self.value)

    def build(self):
        sip_header = sipheader.SipHeader()
        sip_header.set_name(self.name)
        sip_header.set_value(self.value)

        return sip_header

class Message(jobject.JObject):

    KEY_TYPE          = 'type'
    KEY_VERSION       = 'version'
    KEY_ACTION        = 'action'
    KEY_METHOD        = 'method'
    KEY_URI           = 'uri'
    KEY_RESPONSE_CODE = 'code'
    KEY_REASON_PHRASE = 'reason'
    KEY_HEADERS       = 'headers'
    KEY_CONTENT       = 'content'

    def __init__(self):
        jobject.JObject.__init__(self)

        self.version       = None
        self.action        = None
        self.type          = None

        # request specific
        self.method        = None
        self.uri           = None

        # respose specific
        self.response_code = None
        self.reason_phrase = None

        # header list
        self.headers       = []

        # sip content
        self.content       = None

    def parsex(self):
        raise Exception('Message::parsex method must be implemented by child class')

    def parse(self):
        self.version = self.get_field(self.KEY_VERSION)
        self.action  = self.get_field(self.KEY_ACTION)
        self.type    = self.get_field(self.KEY_TYPE)

        self.parsex()

        jheaders = self.get_field(self.KEY_HEADERS, data_types=(list,))
        for jheader in jheaders:
            header = Header()
            header.parsej(jheader)
            self.headers.append(header)

        self.content = self.get_field(self.KEY_CONTENT, optional=True, default='')

    def describe_field(self, name, value):
        print('--- {name} ---'.format(name=name))
        print(value)

    def describex(self):
        raise Exception('Message::describex method must be implemented by child class')

    def describe(self):
        print('### {type} MESSAGE ###'.format(type=self.type))
        self.describe_field(self.KEY_VERSION, self.version)
        self.describe_field(self.KEY_ACTION, self.action)
        self.describex()
        for haeder in self.headers:
            header.describe()
        self.describe_field(self.KEY_CONTENT, self.content)
        print('###')

    def buildx(self):
        raise Exception('Message::buildx method must be implemented by child class')

    def build(self):
        sip_message = self.buildx()

        sip_message.set_sip_version(self.version)

        for header in self.headers:
            sip_message.add_headerx(header.build())

        sip_message.set_content(self.content)

        return sip_message

class MessageRequest(Message):

    def __init__(self):
        Message.__init__(self)

    def parsex(self):
        self.method = self.get_field(self.KEY_METHOD)
        self.uri    = self.get_field(self.KEY_URI)

    def describex(self):
        self.describe_field(self.KEY_METHOD, self.method)
        self.describe_field(self.KEY_URI, self.uri)

    def buildx(self):
        sip_message = siprequest.SipRequest()
        sip_message.set_method(self.method)
        sip_message.set_uri(self.uri)

        return sip_message

class MessageResponse(Message):

    def __init__(self):
        Message.__init__(self)

    def parsex(self):
        self.response_code   = self.get_field(self.KEY_RESPONSE_CODE, data_types=(int, long))
        self.reason_phrase = self.get_field(self.KEY_REASON_PHRASE)

    def describex(self):
        self.describe_field(self.KEY_RESPONSE_CODE, self.response_code)
        self.describe_field(self.KEY_REASON_PHRASE, self.reason_phrase)

    def buildx(self):
        sip_message = sipresponse.SipResponse()
        sip_message.set_response_code(self.response_code)
        sip_message.set_reason_phrase(self.reason_phrase)

        return sip_message

class Scenario(jobject.JObject):

    KEY_AGENT    = 'agent'
    KEY_MESSAGES = 'messages'

    def __init__(self):
        jobject.JObject.__init__(self)

        self.agent    = None
        self.messages = None

    def parse_agent(self):
        jagent = self.get_field(self.KEY_AGENT, data_types=(dict,))

        name = jagent.get(Agent.KEY_TYPE, None)

        if name == AGENT_CLIENT:
            self.agent = AgentClient()
        elif name == AGENT_SERVER:
            self.agent = AgentServer()
        else:
            raise Exception('unknown agent type: {agent_type}'.format(agent_type=name))

        self.agent.parsej(jagent)

    def parse_message(self, jmessage):
        if not isinstance(jmessage, (dict,)):
            raise Exception('message must be of type {type}'.format(type=dict))

        name = jmessage.get(Message.KEY_TYPE, None)

        if name == MESSAGE_REQUEST:
            message = MessageRequest()
        elif name == MESSAGE_RESPONSE:
            message = MessageResponse()
        else:
            raise Exception('unknown message type: {message_type}'.format(message_type=name))

        message.parsej(jmessage)
        self.messages.append(message)

    def parse_messages(self):
        jmessages = self.get_field(self.KEY_MESSAGES, data_types=(list,))

        self.messages = []
        for jmessage in jmessages:
            self.parse_message(jmessage)

    def parse(self):
        self.parse_agent()
        self.parse_messages()

    def describe(self):
        print('*** SCENARIO ***')
        self.agent.describe()
        for message in self.messages:
            message.describe()
        print('*** END ***')
