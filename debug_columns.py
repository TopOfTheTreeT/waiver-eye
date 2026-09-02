import csv

half_ppr_file = r'c:\_Projects\waiver-eye\example-data\Half PPR 2026 Draft Rankings (08_29_2026) - Half PPR Cheat Sheet (08_29).csv'

with open(half_ppr_file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    
    # Read header
    header = next(reader)
    print(f"Total columns: {len(header)}")
    print("\nColumn layout:")
    for i, col in enumerate(header):
        print(f"{i:2d}: {col}")
    
    # Print first few data rows with indices
    print("\n\nFirst data row (with indices):")
    row = next(reader)
    for i, val in enumerate(row):
        if val:
            print(f"{i:2d}: {val}")
