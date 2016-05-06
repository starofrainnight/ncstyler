
import argparse

def main():
    description='''A styler just target to naming conventions of source code'''

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("file_path", help="Source file path")
    
    args = parser.parse_args()
    print(args)
    
if __name__ == "__main__":
    # Execute only if run as a script
    main()
