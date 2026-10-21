-- Gold views over the clean (silver) Parquet files, using OPENROWSET.
-- Serverless SQL reads the files in place: no data is copied and you pay per query.
-- CREATE OR ALTER makes the script safe to re-run.

CREATE OR ALTER VIEW final.calendar AS
SELECT * FROM OPENROWSET(
    BULK 'https://awvmac03.dfs.core.windows.net/clean/Calendar/',
    FORMAT = 'PARQUET'
) AS query1;
GO

CREATE OR ALTER VIEW final.customers AS
SELECT * FROM OPENROWSET(
    BULK 'https://awvmac03.dfs.core.windows.net/clean/Customers/',
    FORMAT = 'PARQUET'
) AS query1;
GO

CREATE OR ALTER VIEW final.categories AS
SELECT * FROM OPENROWSET(
    BULK 'https://awvmac03.dfs.core.windows.net/clean/Product_Categories/',
    FORMAT = 'PARQUET'
) AS query1;
GO

CREATE OR ALTER VIEW final.subcategories AS
SELECT * FROM OPENROWSET(
    BULK 'https://awvmac03.dfs.core.windows.net/clean/Product_Subcategories/',
    FORMAT = 'PARQUET'
) AS query1;
GO

CREATE OR ALTER VIEW final.products AS
SELECT * FROM OPENROWSET(
    BULK 'https://awvmac03.dfs.core.windows.net/clean/Products/',
    FORMAT = 'PARQUET'
) AS query1;
GO

CREATE OR ALTER VIEW final.returns AS
SELECT * FROM OPENROWSET(
    BULK 'https://awvmac03.dfs.core.windows.net/clean/Returns/',
    FORMAT = 'PARQUET'
) AS query1;
GO

CREATE OR ALTER VIEW final.territories AS
SELECT * FROM OPENROWSET(
    BULK 'https://awvmac03.dfs.core.windows.net/clean/Territories/',
    FORMAT = 'PARQUET'
) AS query1;
GO

CREATE OR ALTER VIEW final.sales AS
SELECT * FROM OPENROWSET(
    BULK 'https://awvmac03.dfs.core.windows.net/clean/Sales/',
    FORMAT = 'PARQUET'
) AS query1;
GO
