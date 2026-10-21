-- Gold views over the clean (silver) Parquet files, using OPENROWSET.
-- Serverless SQL reads the files in place: no data is copied and you pay per query.
-- CREATE OR ALTER makes the script safe to re-run.
-- View names match the seven views in awdatabase.final.

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

CREATE OR ALTER VIEW final.Product_Subcategories AS
SELECT * FROM OPENROWSET(
    BULK 'https://awvmac03.dfs.core.windows.net/clean/Product_Subcategories/',
    FORMAT = 'PARQUET'
) AS query1;
GO

CREATE OR ALTER VIEW final.Products AS
SELECT * FROM OPENROWSET(
    BULK 'https://awvmac03.dfs.core.windows.net/clean/Products/',
    FORMAT = 'PARQUET'
) AS query1;
GO

CREATE OR ALTER VIEW final.Returns AS
SELECT * FROM OPENROWSET(
    BULK 'https://awvmac03.dfs.core.windows.net/clean/Returns/',
    FORMAT = 'PARQUET'
) AS query1;
GO

CREATE OR ALTER VIEW final.Sales AS
SELECT * FROM OPENROWSET(
    BULK 'https://awvmac03.dfs.core.windows.net/clean/Sales/',
    FORMAT = 'PARQUET'
) AS query1;
GO

CREATE OR ALTER VIEW final.Territories AS
SELECT * FROM OPENROWSET(
    BULK 'https://awvmac03.dfs.core.windows.net/clean/Territories/',
    FORMAT = 'PARQUET'
) AS query1;
GO
