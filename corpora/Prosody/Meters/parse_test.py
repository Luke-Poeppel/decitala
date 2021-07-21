import pandas as pd

fp = "/Users/lukepoeppel/decitala/corpora/Prosody/Meters/ProsodicMeters.csv"
parsed = pd.read_csv(fp)
for i, row in parsed.iterrows():
    print(row["origin"])