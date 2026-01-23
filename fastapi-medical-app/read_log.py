
import sys

def read_file(filename):
    try:
        with open(filename, "r", encoding="utf-16") as f:
            return f.read()
    except Exception as e:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e2:
            return f"Error reading file: {e} / {e2}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python read_log.py <filename>")
    else:
        print(read_file(sys.argv[1]))
