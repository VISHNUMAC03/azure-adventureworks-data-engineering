"""Build the CSV snapshot of the gold layer that the Power BI report reads.

Applies the same rules as the Databricks clean layer (one Sales table for 2015-2017,
typed dates, OrderNumber S -> T) and shapes the data into a star schema:
Sales and Returns facts, and Calendar, Products, Customers and Territories dimensions.

Usage: python prepare_data.py <folder with the 10 AdventureWorks CSVs> [output folder]
"""
import sys
from pathlib import Path

import pandas as pd

src = Path(sys.argv[1])
out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent / "data"
out.mkdir(parents=True, exist_ok=True)


def read(name):
    return pd.read_csv(src / f"{name}.csv", encoding="latin-1")


# Dimensions
cal = read("Calendar")
cal["Date"] = pd.to_datetime(cal["Date"], format="%m/%d/%Y")
cal["Year"] = cal["Date"].dt.year
cal["Quarter"] = "Q" + cal["Date"].dt.quarter.astype(str)
cal["MonthNum"] = cal["Date"].dt.month
cal["Month"] = cal["Date"].dt.strftime("%b")
cal["MonthStart"] = cal["Date"].dt.to_period("M").dt.start_time

cat = read("Product_Categories")
sub = read("Product_Subcategories")
prod = read("Products").merge(sub, on="ProductSubcategoryKey", how="left").merge(
    cat, on="ProductCategoryKey", how="left")
prod = prod[["ProductKey", "ProductName", "ModelName", "ProductSKU", "ProductColor",
             "SubcategoryName", "CategoryName", "ProductCost", "ProductPrice"]]
prod = prod.rename(columns={"SubcategoryName": "Subcategory", "CategoryName": "Category",
                            "ProductColor": "Color"})

cus = read("Customers")
cus["AnnualIncome"] = (cus["AnnualIncome"].astype(str)
                       .str.replace(r"[$,\s]", "", regex=True).astype(float))
birth = pd.to_datetime(cus["BirthDate"], format="%m/%d/%Y", errors="coerce")
age = ((pd.Timestamp("2017-06-30") - birth).dt.days // 365).astype("Int64")
cus["AgeGroup"] = pd.cut(age, [0, 34, 44, 54, 64, 200],
                         labels=["Under 35", "35-44", "45-54", "55-64", "65+"]).astype(str)
cus["IncomeBand"] = pd.cut(cus["AnnualIncome"], [-1, 40000, 80000, 120000, 10**9],
                           labels=["Low (<=40K)", "Mid (40-80K)", "High (80-120K)",
                                   "Very high (>120K)"]).astype(str)
cus["Gender"] = cus["Gender"].map({"M": "Male", "F": "Female"}).fillna("Unknown")
cus["MaritalStatus"] = cus["MaritalStatus"].map({"M": "Married", "S": "Single"})
cus["HomeOwner"] = cus["HomeOwner"].map({"Y": "Yes", "N": "No"})
# Names and email addresses are not needed for analysis, so they are left out.
cus = cus[["CustomerKey", "Gender", "MaritalStatus", "AgeGroup", "AnnualIncome", "IncomeBand",
           "TotalChildren", "EducationLevel", "Occupation", "HomeOwner"]]

ter = read("Territories")

# Facts
sales = pd.concat([read(f"Sales_{y}") for y in (2015, 2016, 2017)], ignore_index=True)
sales["OrderDate"] = pd.to_datetime(sales["OrderDate"], format="%m/%d/%Y")
sales["StockDate"] = pd.to_datetime(sales["StockDate"], format="%m/%d/%Y")
sales["OrderNumber"] = sales["OrderNumber"].str.replace("S", "T", regex=False)
sales = sales.merge(prod[["ProductKey", "ProductPrice", "ProductCost"]], on="ProductKey")
sales["Revenue"] = (sales["OrderQuantity"] * sales["ProductPrice"]).round(2)
sales["Cost"] = (sales["OrderQuantity"] * sales["ProductCost"]).round(2)
sales["Profit"] = (sales["Revenue"] - sales["Cost"]).round(2)
sales = sales.drop(columns=["ProductPrice", "ProductCost"])

ret = read("Returns")
ret["ReturnDate"] = pd.to_datetime(ret["ReturnDate"], format="%m/%d/%Y")

for name, df in {"Calendar": cal, "Products": prod, "Customers": cus, "Territories": ter,
                 "Sales": sales, "Returns": ret}.items():
    df.to_csv(out / f"{name}.csv", index=False, date_format="%Y-%m-%d")
    print(f"{name}: {len(df):,} rows")
