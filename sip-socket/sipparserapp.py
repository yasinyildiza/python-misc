import argparse

from xsip import sipdecoder

def main():
    parser = argparse.ArgumentParser(description='decode sip message read from a given file')

    parser.add_argument('filepath', type=str, help='path to the file containing sip message')

    args = parser.parse_args()

    with open(args.filepath) as file:
        content = file.read()

    message = sipdecoder.decode(content)

    if message is None:
        print('invalid sip content')
    else:
        message.describe()

if __name__ == '__main__':
    main()
