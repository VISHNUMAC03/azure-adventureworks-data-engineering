-- Example business questions answered from the gold layer.

-- Orders and units sold by region (result shown in screenshots/09-synapse-sales-by-region.png)
SELECT t.Region,
       COUNT(DISTINCT s.OrderNumber) AS Orders,
       SUM(s.OrderQuantity)          AS UnitsSold
FROM final.Sales s
JOIN final.Territories t ON s.TerritoryKey = t.SalesTerritoryKey
GROUP BY t.Region
ORDER BY UnitsSold DESC;
GO

-- Orders and units by year
SELECT c.Year,
       COUNT(DISTINCT s.OrderNumber) AS orders,
       SUM(s.OrderQuantity)          AS units
FROM final.Sales s
JOIN final.calendar c ON c.Date = s.OrderDate
GROUP BY c.Year
ORDER BY c.Year;
GO

-- Returned units by territory
SELECT t.Region, t.Country,
       SUM(r.ReturnQuantity) AS returned_units
FROM final.Returns r
JOIN final.Territories t ON t.SalesTerritoryKey = r.TerritoryKey
GROUP BY t.Region, t.Country
ORDER BY returned_units DESC;
GO
