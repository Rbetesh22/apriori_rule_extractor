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
            value = basket[col]
            if pd.notna(value):
                transaction.add(f"{col}={str(value)}")
        baskets.append(transaction)

    num_baskets = len(baskets)

    # First pass, find large 1-itemsets (Section 2.1 Algorithm Apriori) k = 1 
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
        # Join step — generate candidate k-itemsets (Section 2.1.1 Algorithm Apriori)
        candidates = []
        for i in range(len(prev)):
            for j in range(i + 1, len(prev)):
                a = prev[i]
                b = prev[j]
                if a[:k-2] == b[:k-2]:  # join only if first k-2 items match 
                    candidate = tuple(sorted(set(a) | set(b))) # Create candidates for relations
                    if candidate not in candidates:
                        candidates.append(candidate)
        
        # Prune step — Loop through candidates and remove if any (k-1) subset is not frequent
        prev_set = set(prev)
        pruned = []
        for candidate in candidates:
            all_valid = True
            subsets = combinations(candidate, k-1) # Generate combinations 
            for subset in subsets:
                sort = tuple(sorted(subset))
                if sort not in prev_set:
                    all_valid = False
                    break

            if all_valid:
                pruned.append(candidate)

        # Count support for each candidate
        candidate_counts = {c: 0 for c in pruned}
        for basket in baskets:
            for candidate in pruned:
                if set(candidate).issubset(basket):
                    candidate_counts[candidate] += 1

    # Keep only those with high enough support
        Lk = []
        for candidate, count in candidate_counts.items():
            supp = count / num_baskets
            if supp >= min_sup:
                Lk.append(candidate)
                support[candidate] = supp
        
        if not Lk:
            break
        
        itemsets.extend(Lk)
        k += 1
    return itemsets, support

def get_association_rules(support_dict, min_conf):
    rules = []
    # loops through all of the frequent itemsets from earlier
    for itemset in support_dict:
        itemset = frozenset(itemset)
        if len(itemset) < 2:
            continue  # Makes sure there is a minimum of 2 items - to make rule
        full_tuple = tuple(sorted(itemset)) #sort to match dict keys
        full_support = support_dict.get(full_tuple)
        # try splitting into each possible left/right combo
        for i in range(1, len(itemset)):
            for left in combinations(itemset, i):
                left_frozen = frozenset(left)
                right_frozen = itemset - left_frozen
                left_tuple = tuple(sorted(left))
                right_tuple = tuple(sorted(right_frozen))
                # skip empties
                if len(left_frozen) == 0 or len(right_frozen) == 0:
                    continue
                #skip uninteresting rules (where support didn't change)
                if support_dict.get(left_tuple) == full_support or support_dict.get(right_tuple) == full_support:
                    continue

                if left_tuple not in support_dict:
                    continue  #should not happen but just in case
                # calculate confidence
                conf = full_support / support_dict[left_tuple]
                # if conf is high enough, add to rule set
                if conf >= min_conf:
                    rules.append((left_tuple, right_tuple, conf, full_support))
    return rules


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Necessary arguments, dataset, minimum support and/or minimum confidence are missing.")
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