# tools/chunk_merge.py
# ArkEcho Systems (c) 2025. All Rights Reserved.
"""
Merge multiple text files (chunks) into one file.
Usage: python chunk_merge.py part1.txt part2.txt ... output.txt
"""
import sys

def merge(files, outfile):
    with open(outfile, "w") as fout:
        for fname in files:
            with open(fname, "r") as fin:
                for line in fin:
                    fout.write(line)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python chunk_merge.py <input_files...> <output_file>")
        sys.exit(1)
    *input_files, output_file = sys.argv[1:]
    merge(input_files, output_file)
