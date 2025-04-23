import sys
import pandas as pd
from itertools import combinations

def get_frequent_itemsets(df, min_sup):
    itemsets = []
    support = {}
    baskets = []

    # Convert each row into a set of items
    for _, basket in df.iterrows():
        transaction = set()
        for col in df.columns:
            value = baskets[col]
            if pd.notna(value):
                transaction.add(f"{col}={str(value)}")
        baskets.append(transaction)

    num_baskets = len(baskets)

    # Count First pass, large 1-itemsets (2.1 Algorithm Apriori)
    item_counts = {}
    for basket in baskets:
        for item in basket:
            item_counts[item] = item_counts.get(item, 0) + 1

    Lk = []
    for item, count in item_counts.items():
        supp = count / num_baskets
        if supp >= min_sup:
            itemset = tuple([item])
            Lk.append(itemset)
            support[itemset] = supp

    itemsets.extend(Lk)
    k=2 

    while Lk:
        candidates = []
        Lk_sorted = sorted(Lk)
        for i in range(len(Lk_sorted)):
            for j in range(i + 1, len(Lk_sorted)):
                a, b = Lk_sorted[i], Lk_sorted[j]
                if a[:k-2] == b[:k-2]:  # Join only if first k-2 items match
                    candidate = tuple(sorted(set(a) | set(b)))
                    if len(candidate) == k:
                        candidates.append(candidate)

        Lk_set = set(Lk)
        pruned_candidates = []
        for candidate in candidates:
            all_subsets_frequent = all(
                tuple(sorted(subset)) in Lk_set
                for subset in itertools.combinations(candidate, k - 1)
            )
            if all_subsets_frequent:
                pruned_candidates.append(candidate)
        # Step 2.3: Count support for each candidate
        candidate_counts = {c: 0 for c in pruned_candidates}
        for basket in baskets:
            for candidate in pruned_candidates:
                if set(candidate).issubset(basket):
                    candidate_counts[candidate] += 1

    # Step 2.4: Keep only those with enough support → Lk
        Lk = []
        for candidate, count in candidate_counts.items():
            supp = count / num_baskets
            if supp >= min_sup:
                Lk.append(candidate)
                support[candidate] = supp

        itemsets.extend(Lk)
        k += 1
    return itemsets, support

def get_association_rules(freq_itemsets, min_conf):
    rules = []
    for itemset in freq_itemsets:
        if len(itemset) < 2:
            continue
        for i in range(1, len(itemset)):
            for left in combinations(itemset, i):
                left = frozenset(left)
                right = itemset - left
                conf = freq_itemsets[itemset] / freq_itemsets[left]
                if conf >= min_conf:
                    rules.append((left, right, conf, freq_itemsets[itemset]))
    return rules

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Necessary arguments, min_sup and min_conf are missing.")
        sys.exit(1)

    filename = sys.argv[1]
    min_sup = float(sys.argv[2])
    min_conf = float(sys.argv[3])

    df = pd.read_csv(filename)
    freq_itemsets = get_frequent_itemsets(df, min_sup)
    rules = get_association_rules(freq_itemsets, min_conf)

    with open("output.txt", "w") as f:
        f.write(f"==Frequent itemsets (min_sup={min_sup*100:.0f}%)\n")
        for itemset, sup in sorted(freq_itemsets.items(), key=lambda x: -x[1]):
            f.write(f"[{','.join(sorted(itemset))}], {sup*100:.4f}%\n")

        f.write(f"\n==High-confidence association rules (min_conf={min_conf*100:.0f}%)\n")
        for left, right, conf, sup in sorted(rules, key=lambda x: -x[2]):
            f.write(f"[{','.join(sorted(left))}] => [{','.join(sorted(right))}] (Conf: {conf*100:.1f}%, Supp: {sup*100:.4f}%)\n")

