# Business Retail Analysis

A Power BI dashboard and root cause analysis of an online retailer's sales, built with Python (pandas), Power BI and DAX.

**Question I set out to answer:** why did monthly revenue roughly double between August and November 2011, and what drove it?

## Dashboard

**Page 1: Business Revenue Dashboard.** Year and country slicers, revenue cards, cumulative sales, monthly trend, month-over-month change.

![Business Revenue Dashboard](Screenshot%202026-11-02%20142244.png)

**Page 2: United Kingdom revenue details.** Revenue, orders, customers and orders per customer by country, top products in November 2011, and the share of revenue with no CustomerID.

![United Kingdom Revenue Details](Screenshot%202026-11-02%20142145.png)

## Dataset

Source: [Online Retail E-commerce dataset on Kaggle](https://www.kaggle.com/datasets/ineubytes/online-retail-ecommerce-dataset) (transactions from an online retailer, December 2010 to December 2011).

The raw data is not included in this repo. Download it from the link above and check the licence on that page before reusing it.

## Tools

Python, pandas, Power BI, DAX

## What I built

**1. Data cleaning (pandas)**
- Removed cancelled invoices (InvoiceNo starting with `C`) and rows with zero or negative quantity or unit price, so revenue reflects completed sales only.
- Converted `InvoiceDate` to a proper datetime, added a `Month` column, and kept a plain date for the Power BI date relationship.
- Rows with no CustomerID were kept in the revenue figures, and flagged separately in the analysis (see Limitations).

```python
cleaning_records = data[
    ~data['InvoiceNo'].astype(str).str.startswith('C') &
    (data['Quantity'] > 0) &
    (data['UnitPrice'] > 0)
].copy()

cleaning_records['InvoiceDate'] = pd.to_datetime(cleaning_records['InvoiceDate'], format='%Y-%m-%d %H:%M:%S')
cleaning_records['Month'] = cleaning_records['InvoiceDate'].dt.to_period('M')
cleaning_records['InvoiceDate'] = cleaning_records['InvoiceDate'].dt.date
```

**2. Date table and time intelligence (DAX)**
- A dedicated `All_dates` table (one row per day, marked as the date table) related to the sales table.
- Measures: Total Revenue, Cumulative Sales (year-to-date), Same Period Last Year, Previous Month, Month-over-Month %.
- Orders and customers measures use `DISTINCTCOUNT` and `DISTINCTCOUNTNOBLANK`, so rows with no CustomerID are not counted as a customer.
- Every measure was checked against a manual calculation.

**3. Root cause analysis of the August to November 2011 surge**

I split revenue into orders, customers and orders per customer, then sliced by country and product.

| Metric (UK) | August 2011 | November 2011 |
|---|---|---|
| Revenue share of total | about 80% | about 88% |
| Customers | 835 | 1,506 (up 80%) |
| Orders per customer | 1.36 | 1.59 (up 17%) |

Findings:
- About 96% of the increase came from the UK.
- The surge came mainly from **more customers**, not from existing customers buying much more often.
- Seasonal products led the growth.

## Limitations

- **Missing CustomerID:** 26% of UK November revenue has no CustomerID, so it sits outside the customer metrics. This share was 18% in August.
- **One year of data:** it cannot separate seasonality from growth. The seasonal explanation is a hypothesis to test, not proof.
- **December 2011 is partial** (9 days), so it is excluded from trend charts.

## Files

- `Online_Retail_Clean.pbix`: the Power BI report
- `Business Retail.py`: data cleaning and verification checks in pandas
- Dashboard screenshots (`.png`)

## How to open

Open the `.pbix` file in Power BI Desktop. Download the dataset from the Kaggle link above if you want to refresh the data.
