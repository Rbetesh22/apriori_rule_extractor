import sys
import pandas as pd
from itertools import combinations
# from mlxtend.frequent_patterns import apriori, association_rules

def get_frequent_itemsets(df, min_sup):
    itemsets = []
    support = {}
    baskets = []

    # Convert each row into a set of items
    for _, basket in df.iterrows():
        transaction = set()
        for col in df.columns:
            value = basket[col]
            if pd.notna(value):
                transaction.add(f"{col}={str(value)}")
        baskets.append(transaction)

    num_baskets = len(baskets)

    # First pass, find large 1-itemsets (2.1 Algorithm Apriori) k = 1 
    item_counts = {}
    for basket in baskets:
        for item in basket:
            if item in item_counts:
                item_counts[item] +=1
            else:
                item_counts[item] = 1
    
    L1 = []
    for item, count in item_counts.items():
        supp = count / num_baskets
        if supp >= min_sup: # check threshold
            itemset = tuple([item])
            L1.append((item,))
            support[(item,)] = supp
    itemsets.extend(L1)
    
    # k ≥ 2 
    # join and prune
    
    k=2 
    prev = L1

    while prev:
        # Step 2.1: Join step — generate candidate k-itemsets
        candidates = []
        for i in range(len(prev)):
            for j in range(i + 1, len(prev)):
                a, b = prev[i], prev[j]
                if a[:k-2] == b[:k-2]:  # Join only if first k-2 items match
                    candidate = tuple(sorted(set(a) | set(b)))
                    if candidate not in candidates:
                        candidates.append(candidate)
        
        # Step 2.2: Prune step — remove if any (k-1) subset is not frequent
        prev_set = set(prev)
        pruned = []
        for candidate in candidates:
            all_subsets_frequent = all(
                tuple(sorted(subset)) in prev_set
                for subset in combinations(candidate, k - 1)
            )
            if all_subsets_frequent:
                pruned.append(candidate)

        # Step 2.3: Count support for each candidate
        candidate_counts = {c: 0 for c in pruned}
        for basket in baskets:
            for candidate in pruned:
                if set(candidate).issubset(basket):
                    candidate_counts[candidate] += 1

    # Step 2.4: Keep only those with enough support
        Lk = []
        for candidate, count in candidate_counts.items():
            supp = count / num_baskets
            if supp >= min_sup:
                Lk.append(candidate)
                support[candidate] = supp
        # add a break if no more new freq itemsets 
        if not Lk:
            break
        
        itemsets.extend(Lk)
        k += 1
    return itemsets, support

def get_association_rules(support_dict, min_conf):
    rules = []
    for itemset in support_dict.keys():
        if len(itemset) < 2:
            continue
        for i in range(1, len(itemset)):
            for left in combinations(itemset, i):
                left = tuple(sorted(left))
                right = tuple(sorted(set(itemset) - set(left)))
                conf = support_dict[itemset] / support_dict[left]
                if conf >= min_conf:
                    rules.append((left, right, conf, support_dict[itemset]))
    return rules

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Necessary arguments, min_sup and min_conf are missing.")
        sys.exit(1)

    filename = sys.argv[1]
    min_sup = float(sys.argv[2])
    min_sup_percent = min_sup * 100
    min_conf = float(sys.argv[3])
    min_conf_percent = min_conf*100

    df = pd.read_csv(filename)
    itemsets, support = get_frequent_itemsets(df, min_sup)
    rules = get_association_rules(support, min_conf)


    with open("output.txt", "w") as f:
        f.write(f"==Frequent itemsets (min_sup={min_sup_percent}%)\n")
        for itemset, sup in sorted(support.items(), key=lambda x: -x[1]):
            f.write(f"[{','.join(sorted(itemset))}], {sup*100:.4f}%\n")

        f.write(f"\n==High-confidence association rules (min_conf={min_conf_percent}%)\n")
        for left, right, conf, sup in sorted(rules, key=lambda x: -x[2]):
            f.write(f"[{','.join(sorted(left))}] => [{','.join(sorted(right))}] (Conf: {conf*100:.1f}%, Supp: {sup*100:.4f}%)\n")

