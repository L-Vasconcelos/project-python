-- Instrução: Na tabela FactSales, agrupe por ano de OrderDate e some o valor das vendas (SalesAmount).

select * from FactSales
 
 select
 year (datekey) as 'ano',
 sum (salesamount) as 'total_sales'
 from FactSales
 group by year (datekey);

 -- Instrução: Realize uma junção entre FactSales e DimProduct para listar SalesOrderNumber, SalesAmount e ProductName.

select top 10 * from FactSales
select top 10 * from DimProduct

select top 10
fc.SalesQuantity,
fc.salesamount,
dp.ProductName
from FactSales as fc
left join DimProduct as dp on
fc.ProductKey = dp.ProductKey
order by SalesAmount desc;

-- Instrução: Use DimStore e DimGeography para listar StoreKey, StoreName e RegionCountryName de cada loja.

select * from DimStore
select * from DimGeography

select 
ds.storekey,
ds.storename,
dg.regioncountryname
from DimStore as ds
left join DimGeography as dg on
ds.GeographyKey = dg.GeographyKey
order by StoreKey asc;


-- Instrução: Usando a tabela FactSales, retorne SalesOrderNumber e SalesAmount para a transação com o valor mais alto (SalesAmount).

select * from FactSales;

select  
saleskey as 'id_chave',
salesamount as 'venda_atotal'
from FactSales
where SalesAmount = 
(select max(salesamount) from FactSales);

