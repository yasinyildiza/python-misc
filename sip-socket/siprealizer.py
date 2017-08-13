from xsocket import udpclient
from xsocket import tcpclient
from xsocket import tcpserver
from xsocket import udpserver

from xsip import sipdecoder
from xsip import siprequest
from xsip import sipresponse
from xsip import sipscenario

class SipRealizer(object):

    def __init__(self):
        self.scenario = None
        self.agent    = None

    def init_scenario(self, filepath):
        self.scenario = sipscenario.Scenario()
        self.scenario.parsef(filepath)

    def init_agent(self):
        agent = None
        args = []

        if self.scenario.agent.type == sipscenario.AGENT_CLIENT:

            if self.scenario.agent.protocol == sipscenario.PROTOCOL_UDP:
                agent = udpclient.Client

            elif self.scenario.agent.protocol == sipscenario.PROTOCOL_TCP:
                agent = tcpclient.Client

            else:
                raise Exception('unknown protocol: {protocol}'.format(protocol=self.scenario.agent.protocol))

            args.append(self.scenario.agent.ip)
            args.append(self.scenario.agent.port)
            args.append(self.scenario.agent.timeout)

        elif self.scenario.agent.type == sipscenario.AGENT_SERVER:

            if self.scenario.agent.protocol == sipscenario.PROTOCOL_UDP:
                agent = udpserver.Server

            elif self.scenario.agent.protocol == sipscenario.PROTOCOL_TCP:
                agent = tcpserver.Server

            else:
                raise Exception('unknown protocol: {protocol}'.format(protocol=self.scenario.agent.protocol))

            args.append(self.scenario.agent.port)
            args.append(self.scenario.agent.buffersize)

        else:

            raise Exception('unknown agent type: {type}'.format(type=self.scenario.agent.type))

        args.append(False) # sendloop
        args.append(False) # recvloop

        self.agent = agent(*args)

        if self.scenario.agent.type == sipscenario.AGENT_CLIENT:
            self.agent.connect()
        elif self.scenario.agent.type == sipscenario.AGENT_SERVER:
            self.agent.register(self)
            self.agent.accept()
        else:
            pass

    def handle_message(self, message):
        # TODO
        # there is no direct send/recv for server mode
        # first, wait for a client to connect
        # then register to corresponding session
        # currently, this part supports only client mode

        sip_message = message.build()

        if message.action == sipscenario.ACTION_SEND:
            print('sending...')
            content = sip_message.encode()
            self.agent.send(content)
            print('sent')
        elif message.action == sipscenario.ACTION_RECV:
            print('receiving...')
            content = self.agent.recv(self.scenario.agent.buffersize)
            sip_message2 = sipdecoder.decode(content)
            print('received')

            print('checking...')
            # TODO
            # compare sip_message and sip_message2
            print('checked')

    def handle_messages(self):
        for message in self.scenario.messages:
            self.handle_message(message)

    def realize(self, filepath):
        self.init_scenario(filepath)
        self.init_agent()
        self.handle_messages()
