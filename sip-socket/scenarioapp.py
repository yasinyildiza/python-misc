import argparse

from xsip import sipscenario

def main():
    parser = argparse.ArgumentParser(description='parses and describes the content of a sip scenario file')

    parser.add_argument('filepath', type=str, help='path to the scenario file')

    args = parser.parse_args()

    scenario = sipscenario.Scenario()
    scenario.parsef(args.filepath)
    scenario.describe()

if __name__ == '__main__':
    main()
