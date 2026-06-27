import csv
import os

INPUT = "Marketplace.csv"
OUTPUT_PREFIX = "Marketplace_part_"
CHUNK_SIZE = 1000  # rows per file

path = INPUT
folder = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(folder, path)

with open(file_path, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    headers = next(reader)

    file_count = 1
    row_count = 0
    out_file = open(os.path.join(folder, f"{OUTPUT_PREFIX}{file_count}.csv"), "w", newline='', encoding="utf-8")
    writer = csv.writer(out_file)
    writer.writerow(headers)

    for row in reader:
        row_count += 1
        writer.writerow(row)

        if row_count % CHUNK_SIZE == 0:
            out_file.close()
            file_count += 1
            out_file = open(os.path.join(folder, f"{OUTPUT_PREFIX}{file_count}.csv"), "w", newline='', encoding="utf-8")
            writer = csv.writer(out_file)
            writer.writerow(headers)

    out_file.close()

print(f"Splitting complete! Generated {file_count} files.")
