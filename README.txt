a. Kira Ariyan (kna2121) Ralph Betesh (rb3557)

b.  INTEGRATED-DATASET.csv
    main.py 
    example-run.txt
    README.txt

c. Use the standard VM config - we required no extra memory.

    Make sure you are in the project folder
    - cd proj3

    Install venv
    - sudo apt update
    - sudo apt install python3-venv -y
    - python3 -m venv venv

    Set up venv
    - source venv/bin/activate
    - pip install pandas flask

    Run Program - ensure that the csv is in the proper directory
    - python3 main.py INTEGRATED-DATASET.csv 0.1 0.8

d. We used the datasets: 311 Service Requests from 2019 to Present, Evictions, and Issued Licenses. We downloaded them using the following steps:

Step 1.1: Download the datasets
Licenses (all): wget -O licenses.csv "https://data.cityofnewyork.us/api/views/w7w3-xahh/rows.csv?accessType=DOWNLOAD"
311 Requests (past 5 years): wget -O 311.csv "https://data.cityofnewyork.us/resource/erm2-nwe9.csv?\$where=created_date>='2019-01-01T00:00:00'"
Evictions: wget -O evictions.csv "https://data.cityofnewyork.us/api/views/6z8x-wfk4/rows.csv?accessType=DOWNLOAD"

Step 1.2: Verify Downloads
ls -lh *.csv
You should see: licenses.csv 311.csv evictions.csv

Step 2: Load CSVs into Postgres
Make sure PostgreSQL is installed and running.
Create a database named proj3: createdb proj3
Ensure your PostgreSQL user (e.g., rb3557) has access. Create the user if necessary: sudo -u postgres createuser rb3557 sudo -u postgres psql ALTER USER rb3557 WITH PASSWORD 'password';
Create a Python script called (e.g. load_data.py) with the following:
import pandas as pd from sqlalchemy import create_engine
# Connect to database
engine = create_engine('postgresql://‘usename:password’@localhost/proj3')
# Load in each CSV
for filename, table in [("licenses.csv", "licenses"), ("311.csv", "complaints"), ("evictions.csv", "evictions")]: print(f"Loading {filename} into table '{table}'...") df = pd.read_csv(filename, low_memory=False) df.to_sql(table, engine, if_exists='replace', index=False)
# Run the script: python3 load_data.py

Step 3: Normalize Address Columns
Connect to PostgreSQL: sudo -u postgres psql proj3
Then run the following queries:
-- Licenses 
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS normalized_address TEXT; UPDATE licenses SET normalized_address = LOWER(TRIM(REPLACE(REPLACE(CONCAT_WS(' ', "Building Number", "Street1", "Street2", "Street3", "City", "State", "ZIP Code"), '.', ''), ',', ''))) WHERE "Building Number" IS NOT NULL AND "Street1" IS NOT NULL;
-- Complaints 
ALTER TABLE complaints ADD COLUMN IF NOT EXISTS normalized_address TEXT; UPDATE complaints SET normalized_address = LOWER(TRIM(REPLACE(REPLACE(incident_address, '.', ''), ',', ''))) WHERE incident_address IS NOT NULL;
-- Evictions 
ALTER TABLE evictions ADD COLUMN IF NOT EXISTS normalized_address TEXT; UPDATE evictions SET normalized_address = LOWER(TRIM(REPLACE(REPLACE("Eviction Address", '.', ''), ',', ''))) WHERE "Eviction Address" IS NOT NULL;


Step 4: Integrate the data

For context, we joined the datasets using the normalized_address field.  The reason we did this is because for the licenses table, the address was originally broken down into different fields so we had to create a column called normalized_address (and then normalize the other tables’ addresses based on that, creating their own normalized_address fields) and used that to combine the 3 datasets. We only included commercial addresses so we can use this data to find business-related trends.
CREATE TABLE integrated_dataset AS SELECT l."License Number", l."Business Name", l."DBA/Trade Name", l."Business Unique ID", l."Business Category", l."License Type", l."License Status", l."Initial Issuance Date", l."Expiration Date", l."City" AS license_city, l."State" AS license_state, l."ZIP Code" AS license_zip, 
c.unique_key AS complaint_id, c.created_date, c.closed_date, c.complaint_type, c.descriptor, c.incident_address, c.incident_zip, c.address_type AS complaint_address_type, c.status, c.resolution_description,
e."Court Index Number", e."Docket Number ", e."Eviction Address", e."Executed Date", e."Residential/Commercial" AS eviction_type, e."Eviction Postcode", e."BOROUGH" AS eviction_borough,
COALESCE(l.normalized_address, c.normalized_address, e.normalized_address) AS join_address FROM licenses l FULL OUTER JOIN complaints c ON l.normalized_address = c.normalized_address FULL OUTER JOIN evictions e ON COALESCE(l.normalized_address, c.normalized_address) = e.normalized_address;

Step 5: Export to CSV
\copy (SELECT * FROM integrated_dataset) TO 'INTEGRATED-DATASET.csv' CSV HEADER;


e. The internal design of main.py is as follows - the program expects 4 command line arguments, (main.py, the dataset csv, the minimum support and minumum confidence).
If the program does not receive these arguments it exits immediately. If it properly retrieves the arguments, the program then calls 2 functions, get_frequent_itemsets and
get_association_rules. get_frequent_itemsets takes in a pandas dataframe generated using the csv file and performs the apriori algorithm as described in
Section 2.1 of Agrawal's paper "Fast Algorithms for Mining Association Rules. First it finds the large 1-itemsets by counting item occurences.
Then the itemsets are used to generate candidate pairings for possible association rules. We use the algorithm described in 2.1.1 for candidate generation.
We joined and pruned potential candidates to generate a list, and then ensure that each of these candidates have the minumum support. Finally, the function extends the 
proper itemsets. We did not implement the subset function described in Section 2.1.2 or the possible variations. The next function, get_association_rules checks possible combinations from 
the frequent itemsets and calculates the confidence for each. If the confidence is high enough, that pair is saved as a high-confidence association rule.


f. python main.py INTEGRATED-DATASET.csv 0.1 0.8 
We chose these parameters because the primary goal of our project is to uncover meaningful patterns that could indicate increased risk of evictions or 
foreclosures amongst New York City retail stores, with relation to lots of variables and high confidence. This is the first step in our goal to observe trends, 
correlations, and combinations of attributes that frequently co-occur in commercial addresses where evictions or complaint activity is present and potentially 
help these businesses save themselves before it's too late. These association rules give us insight into patterns between service complaints and eviction statuses.
Some businesses being evicted have registered licenses and complaints in the past which have been left unresolved. Most businesses in NY are very well documented and licensed,
which leads us to look deeper into evictions and unresolved 311 requests/complaints.