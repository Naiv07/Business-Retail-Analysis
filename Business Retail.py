"""
ONLINE RETAIL - ANALYSIS + POWER BI EXPORT

Tables, in the order they are created:
  data              raw file, never changed
  cleaning_records  every valid sale (no cancellations, Quantity > 0, UnitPrice > 0)
                    + Revenue + Month      -> REVENUE questions and the Power BI export
  sales_products    cleaning_records minus the 14 non-product codes
                                           -> PRODUCT rankings
  customer_sales    sales_products that have a CustomerID
                                           -> CUSTOMER analysis
(clean_records is gone: customer_sales replaces it.)
"""

import pandas as pd

pd.set_option('display.max_columns', None)

SRC = r"C:\Users\troos\OneDrive\Documents\Projects\Practice Dataset\Online Retail.csv"
OUT = r"C:\Users\troos\OneDrive\Documents\Projects\Practice Dataset\Online Retail Clean.csv"   # NEW file, raw file stays untouched

"""
def check(label, actual, expected):
    Print OK or MISMATCH so every checkpoint is visible
    status = 'OK' if actual == expected else f'MISMATCH (expected {expected})'
    print(f'CHECK {label}: {actual} -> {status}')
"""

# ---------------------------------------------------------------- 1. LOAD
data = pd.read_csv(SRC)
print('\nDimension of the dataset:', data.shape)
print('\nNo. of null data points:\n', data.isnull().sum())

# ---------------------------------------------------------------- 2. cleaning_records
cleaning_records = data[
    ~data['InvoiceNo'].astype(str).str.startswith('C') &
    (data['Quantity'] > 0) &
    (data['UnitPrice'] > 0)
].copy()

cleaning_records['Revenue'] = cleaning_records['UnitPrice'] * cleaning_records['Quantity']

# Convert the date ONCE here, so every table built from this one inherits Month and InvoiceDate
cleaning_records['InvoiceDate'] = pd.to_datetime(cleaning_records['InvoiceDate'], format='%Y-%m-%d %H:%M:%S')
cleaning_records['Month'] = cleaning_records['InvoiceDate'].dt.to_period('M')
cleaning_records['InvoiceDate'] = cleaning_records['InvoiceDate'].dt.date

"""check('cleaning_records rows', len(cleaning_records), 530104)
check('null CustomerID in cleaning_records', int(cleaning_records['CustomerID'].isna().sum()), 132220)"""
print('Last invoice date:', cleaning_records['InvoiceDate'].max(), '(December 2011 is a PARTIAL month)')

# ---------------------------------------------------------------- 3. sales_products
r"""
HOW THE 14 NON-PRODUCT CODES WERE FOUND (reference for later, no need to re-run)

1. Real product codes look like 5 digits with an optional trailing letter (85123A).
   Anything that breaks that shape is suspicious. This line listed every such code:

       unique_codes = cleaning_records[~cleaning_records['StockCode'].str.match(r'^\d{5}[A-Za-z]?$')]
       print(unique_codes['StockCode'].unique().tolist())

   The earlier, narrower version only caught codes made purely of letters, so it missed
   'BANK CHARGES' (has a space) and 'C2' (has a digit):

       non_numeric = cleaning_records[cleaning_records['StockCode'].str.match(r'^[A-Za-z]+$')]

2. The code alone cannot tell you if a code is a product. The DESCRIPTION decides. To see them:

       check = ['POST', '15056BL', 'C2', 'DOT', 'M', 'BANK CHARGES', '15056bl', 'AMAZONFEE', 'DCGS0076', 'DCGS0003',
                'gift_0001_40', 'DCGS0070', 'm', 'gift_0001_50', 'gift_0001_30', 'gift_0001_20', 'DCGS0069',
                'gift_0001_10', 'S', 'DCGS0004', 'B']
       pd.set_option('display.max_rows', None)
       pd.set_option('display.max_colwidth', None)
       print(cleaning_records[cleaning_records['StockCode'].isin(check)])

3. Verdicts:
   DROPPED (fees / not merchandise): POST, DOT (postage), M, m (manual), AMAZONFEE, S (samples),
       B (bad debt adjustment), C2 (carriage), BANK CHARGES, gift_0001_10/20/30/40/50 (gift vouchers)
   KEPT (real products, even though the code looks odd):
       PADS, DCGSSBOY, DCGSSGIRL, DCGS0003/0004/0069/0070/0076, 15056BL and 15056bl (same parasol, two letter cases)
   Proof the 3 restored products are still in sales_products (expect DCGSSBOY 11, DCGSSGIRL 13, PADS 3):

       restored = ['PADS', 'DCGSSBOY', 'DCGSSGIRL']
       print(sales_products[sales_products['StockCode'].isin(restored)].groupby('StockCode').size())

4. Row-count proof: 14 codes remove 2,159 + 184 = 2,343 rows, 530,104 - 2,343 = 527,761.

5. Do NOT overwrite cleaning_records with the filtered table (the earlier mistake):

       cleaning_records = cleaning_records[~cleaning_records['StockCode'].isin(codes)]   # loses the full table

   Save the result under a new name instead (sales_products below).

6. Dropping rows with no CustomerID (customer_sales) loses revenue that still counts in the
   TOTAL revenue. That is why revenue questions use cleaning_records, not customer_sales.
"""
codes = ['POST', 'DOT', 'M', 'm', 'AMAZONFEE', 'S', 'B', 'C2', 'BANK CHARGES',
         'gift_0001_10', 'gift_0001_20', 'gift_0001_30', 'gift_0001_40', 'gift_0001_50']

sales_products = cleaning_records[~cleaning_records['StockCode'].isin(codes)].copy()
#check('sales_products rows', len(sales_products), 527761)

# ---------------------------------------------------------------- 4. customer_sales
customer_sales = sales_products[sales_products['CustomerID'].notna()].copy()
#check('customer_sales rows', len(customer_sales), 396340)

# ================================================================ PROBLEM 1: monthly revenue -> cleaning_records
monthly_rev = cleaning_records.groupby('Month').agg(
    total_quantity=('Quantity', 'sum'),
    total_revenue=('Revenue', 'sum')
).reset_index()
monthly_rev['percent_change'] = (monthly_rev['total_revenue'].pct_change() * 100).round(2)
print('\nMonthly revenue (Dec 2011 is partial, ignore its percent_change):\n', monthly_rev)

grand_total_rev = cleaning_records['Revenue'].sum()
#check('grand total revenue', round(grand_total_rev, 2), 10666684.54)
#check('monthly sum equals grand total', round(monthly_rev['total_revenue'].sum(), 2), round(grand_total_rev, 2))

# ================================================================ PROBLEM 2: top 3 products per country -> sales_products
top_products = sales_products.groupby(['Country', 'Description']).agg(
    total_revenue=('Revenue', 'sum')
).reset_index()

top_3_products_per_country = (
    top_products
    .sort_values(['Country', 'total_revenue'], ascending=[True, False])
    .groupby('Country')
    .head(3)
)
print('\nTop 3 products per country:\n', top_3_products_per_country)
print('\nAustria only:\n', top_3_products_per_country[top_3_products_per_country['Country'] == 'Austria'])

# ================================================================ PROBLEM 3: customers above country average -> customer_sales
customer_totals = customer_sales.groupby(['CustomerID', 'Country']).agg(
    total_revenue=('Revenue', 'sum')
).reset_index()

customer_totals['country_avg_revenue'] = customer_totals.groupby('Country')['total_revenue'].transform('mean')
above_avg_customers = customer_totals[
    customer_totals['total_revenue'] > customer_totals['country_avg_revenue']
].sort_values('Country')

#check('above-average customers', len(above_avg_customers), 954)
print('\nAbove-average customers per country:\n', above_avg_customers.groupby('Country')['CustomerID'].count())
print('\nUnique Customer IDs: ',cleaning_records['CustomerID'].nunique())

# ================================================================ POWER BI EXPORT
# ONE file with ALL valid sales + two flag columns, instead of three separate CSVs.
# In Power BI, CALCULATE then picks the right slice of the same table.
powerbi = cleaning_records.copy()
powerbi['IsProduct'] = ~powerbi['StockCode'].isin(codes)        # False for fees / postage / vouchers
powerbi['HasCustomer'] = powerbi['CustomerID'].notna()
powerbi['CustomerID'] = powerbi['CustomerID'].astype('Int64')   # 12415 instead of 12415.0
powerbi['Month'] = powerbi['Month'].astype(str)                 # Period type is not a CSV-friendly type

#check('powerbi rows', len(powerbi), 530104)
#check('powerbi revenue', round(powerbi['Revenue'].sum(), 2), 10666684.54)
#check('powerbi product rows', int(powerbi['IsProduct'].sum()), 527761)

powerbi.to_csv(OUT, index=False)
print('\nExported to:', OUT)