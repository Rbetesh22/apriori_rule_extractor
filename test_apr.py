import sys
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

# ------------------------------
# Step 1: Parse command line args
# ------------------------------
if len(sys.argv) != 4:
    print("Usage: python3 main.py INTEGRATED-DATASET.csv min_sup min_conf")
    sys.exit(1)

input_file = sys.argv[1]
min_sup = float(sys.argv[2])
min_conf = float(sys.argv[3])

# ------------------------------
# Step 2: Load and preprocess data
# ------------------------------
df = pd.read_csv(input_file)

# Filter for relevant columns
df = df[["Business Category", "License Type", "License Status", "complaint_type", "eviction_count"]]

# Drop rows with NA in any categorical column
df.dropna(subset=["Business Category", "License Type", "License Status"], inplace=True)

# Convert eviction_count to a binary category
df['has_eviction'] = df['eviction_count'].apply(lambda x: 'eviction' if x > 0 else None)

# Transform each row into a list of non-null string items
records = []
for _, row in df.iterrows():
    items = [str(val) for val in row[:-1] if pd.notnull(val)]  # exclude eviction_count
    if row['has_eviction']:
        items.append(row['has_eviction'])
    records.append(items)

# ------------------------------
# Step 3: Encode transactions
# ------------------------------
te = TransactionEncoder()
te_ary = te.fit(records).transform(records)
df_hot = pd.DataFrame(te_ary, columns=te.columns_)

# ------------------------------
# Step 4: Run Apriori Algorithm
# ------------------------------
frequent_itemsets = apriori(df_hot, min_support=min_sup, use_colnames=True)
frequent_itemsets.sort_values(by="support", ascending=False, inplace=True)

# ------------------------------
# Step 5: Generate Rules
# ------------------------------
rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_conf)
rules = rules[(rules['consequents'].apply(lambda x: len(x) == 1)) &
              (~rules.apply(lambda row: row['consequents'].issubset(row['antecedents']), axis=1))]
rules.sort_values(by="confidence", ascending=False, inplace=True)

# ------------------------------
# Step 6: Write to output.txt
# ------------------------------
with open("output.txt", "w") as f:
    f.write("==Frequent itemsets (min_sup={:.1f}%)\n".format(min_sup * 100))
    for _, row in frequent_itemsets.iterrows():
        items = list(row['itemsets'])
        support = row['support'] * 100
        f.write(f"[{','.join(items)}], {support:.4f}%\n")

    f.write("\n==High-confidence association rules (min_conf={:.1f}%)\n".format(min_conf * 100))
    for _, row in rules.iterrows():
        lhs = ','.join(sorted(row['antecedents']))
        rhs = ','.join(sorted(row['consequents']))
        support = row['support'] * 100
        confidence = row['confidence'] * 100
        f.write(f"[{lhs}] => [{rhs}] (Conf: {confidence:.1f}%, Supp: {support:.4f}%)\n")

