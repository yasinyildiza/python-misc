import argparse

import siprealizer

def main():
    parser = argparse.ArgumentParser(description='realizes a given scenario file')

    parser.add_argument('filepath', type=str, help='path to the scenario file')

    args = parser.parse_args()

    realizer = siprealizer.SipRealizer()
    realizer.realize(filepath)

if __name__ == '__main__':
    main()
