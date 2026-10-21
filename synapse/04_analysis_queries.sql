-- Example business questions answered from the gold layer.

-- Orders and units by year
SELECT c.Year,
       COUNT(DISTINCT s.OrderNumber) AS orders,
       SUM(s.OrderQuantity)          AS units
FROM final.sales s
JOIN final.calendar c ON c.Date = s.OrderDate
GROUP BY c.Year
ORDER BY c.Year;
GO

-- Revenue by product category
SELECT cat.CategoryName,
       ROUND(SUM(s.OrderQuantity * p.ProductPrice), 2) AS revenue
FROM final.sales s
JOIN final.products      p   ON p.ProductKey = s.ProductKey
JOIN final.subcategories sub ON sub.ProductSubcategoryKey = p.ProductSubcategoryKey
JOIN final.categories    cat ON cat.ProductCategoryKey = sub.ProductCategoryKey
GROUP BY cat.CategoryName
ORDER BY revenue DESC;
GO

-- Return rate by territory
SELECT t.Region, t.Country,
       SUM(r.ReturnQuantity) AS returned_units
FROM final.returns r
JOIN final.territories t ON t.SalesTerritoryKey = r.TerritoryKey
GROUP BY t.Region, t.Country
ORDER BY returned_units DESC;
GO
