import sys

from convert import compile_file

def main(file_name, style_file, defs_file):
    compile_file(file_name, ".", "out", style_file, defs_file)

if __name__ == "__main__":
    if not len(sys.argv) == 4:
        print(f"Usage python {sys.argv[0]} <file name> <style file> <defs file>")
        exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
