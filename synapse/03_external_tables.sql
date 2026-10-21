-- External tables (CETAS): materialise gold data back to the lake as Parquet,
-- so Power BI and other tools read a stable, pre-shaped table.
--
-- Prerequisite: the Synapse workspace managed identity has the
-- "Storage Blob Data Contributor" role on the awvmac03 storage account.

-- 1. Master key: protects the credential below.
--    Set your own strong password at run time. Never commit a real password.
IF NOT EXISTS (SELECT 1 FROM sys.symmetric_keys WHERE name = '##MS_DatabaseMasterKey##')
    CREATE MASTER KEY ENCRYPTION BY PASSWORD = '<your-strong-password>';
GO

-- 2. Credential: Synapse authenticates to ADLS with its managed identity (no keys or SAS tokens).
CREATE DATABASE SCOPED CREDENTIAL cred_awvmac03
WITH IDENTITY = 'Managed Identity';
GO

-- 3. Data sources for the silver and gold containers.
CREATE EXTERNAL DATA SOURCE source_clean
WITH (
    LOCATION = 'https://awvmac03.dfs.core.windows.net/clean',
    CREDENTIAL = cred_awvmac03
);
GO

CREATE EXTERNAL DATA SOURCE source_final
WITH (
    LOCATION = 'https://awvmac03.dfs.core.windows.net/final',
    CREDENTIAL = cred_awvmac03
);
GO

-- 4. Snappy-compressed Parquet output format.
CREATE EXTERNAL FILE FORMAT format_parquet
WITH (
    FORMAT_TYPE = PARQUET,
    DATA_COMPRESSION = 'org.apache.hadoop.io.compress.SnappyCodec'
);
GO

-- 5. CETAS: create the external table and write its data to final/extsales/ in one statement.
CREATE EXTERNAL TABLE final.extsales
WITH (
    LOCATION = 'extsales',
    DATA_SOURCE = source_final,
    FILE_FORMAT = format_parquet
)
AS
SELECT * FROM final.sales;
GO

SELECT TOP 100 * FROM final.extsales;
GO
