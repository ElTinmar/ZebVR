import csv
import sys

def csv_to_markdown(csv_file, md_file):
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))

    headers = reader[0]
    rows = reader[1:]

    with open(md_file, "w", encoding="utf-8") as f:
        # Header row
        f.write("| " + " | ".join(headers) + " |\n")
        # Separator row
        f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
        # Data rows
        for row in rows:
            f.write("| " + " | ".join(row) + " |\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python csv_to_md.py input.csv output.md")
        sys.exit(1)

    csv_to_markdown(sys.argv[1], sys.argv[2])
