import os
import sys
import time

class ConsoleUpdater(object):

	BACKSPACE = '\b'

	LAST_MESSAGE = ''

	@classmethod
	def update(cls, message):
		sys.stdout.write(cls.BACKSPACE * len(cls.LAST_MESSAGE))
		sys.stdout.write(message)
		cls.LAST_MESSAGE = message

def test():
	time.sleep(2)
	ConsoleUpdater.update('line I')
	time.sleep(2)
	ConsoleUpdater.update('line II')
	time.sleep(2)
	ConsoleUpdater.update('line III')

def main():
	test()

if __name__ == '__main__':
	main()
