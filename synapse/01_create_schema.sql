-- Synapse serverless SQL pool · database: awdatabase
-- Gold layer lives in its own schema.

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'final')
    EXEC('CREATE SCHEMA final');
GO
