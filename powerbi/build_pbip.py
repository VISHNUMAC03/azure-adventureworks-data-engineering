"""Generate the AdventureWorks Sales Power BI project (PBIP: TMDL semantic model + PBIR report).

Usage: python build_pbip.py [data folder] [--report-only]
The data folder defaults to ./data next to this script and is stored in the DataFolder parameter.
Open AdventureWorksSales.pbip in Power BI Desktop and select Refresh to load the data.
"""
import json
import shutil
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
DATA = Path(ARGS[0]).resolve() if ARGS else HERE / "data"
NAME = "AdventureWorksSales"
MODEL = HERE / f"{NAME}.SemanticModel"
REPORT = HERE / f"{NAME}.Report"
THEME_SRC = Path(r"C:\Program Files\Microsoft Power BI Desktop\bin\WebView2Resources"
                 r"\minerva\sharedresources\BaseThemes\CY24SU10.json")
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric"


def gid():
    return str(uuid.uuid4())


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not isinstance(content, str):
        content = json.dumps(content, indent=2)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------- semantic model

TABLES = {
    "Sales": [("OrderDate", "date"), ("StockDate", "date"), ("OrderNumber", "text"),
              ("ProductKey", "int"), ("CustomerKey", "int"), ("TerritoryKey", "int"),
              ("OrderLineItem", "int"), ("OrderQuantity", "int"), ("Revenue", "num"),
              ("Cost", "num"), ("Profit", "num")],
    "Returns": [("ReturnDate", "date"), ("TerritoryKey", "int"), ("ProductKey", "int"),
                ("ReturnQuantity", "int")],
    "Calendar": [("Date", "date"), ("Year", "int"), ("Quarter", "text"), ("MonthNum", "int"),
                 ("Month", "text"), ("MonthStart", "date")],
    "Products": [("ProductKey", "int"), ("ProductName", "text"), ("ModelName", "text"),
                 ("ProductSKU", "text"), ("Color", "text"), ("Subcategory", "text"),
                 ("Category", "text"), ("ProductCost", "num"), ("ProductPrice", "num")],
    "Customers": [("CustomerKey", "int"), ("Gender", "text"), ("MaritalStatus", "text"),
                  ("AgeGroup", "text"), ("AnnualIncome", "num"), ("IncomeBand", "text"),
                  ("TotalChildren", "int"), ("EducationLevel", "text"), ("Occupation", "text"),
                  ("HomeOwner", "text")],
    "Territories": [("SalesTerritoryKey", "int"), ("Region", "text"), ("Country", "text"),
                    ("Continent", "text")],
}
M_TYPE = {"date": "type date", "int": "Int64.Type", "num": "type number", "text": "type text"}
TMDL_TYPE = {"date": "dateTime", "int": "int64", "num": "double", "text": "string"}
FORMAT = {"date": "Short Date", "int": "0", "num": "#,0.00"}
HIDDEN = {"ProductKey", "CustomerKey", "TerritoryKey", "SalesTerritoryKey", "OrderLineItem",
          "MonthNum", "StockDate"}

MEASURES = {
    "Sales": [
        ("Total Revenue", "SUM(Sales[Revenue])", r"\$#,0"),
        ("Revenue ($K)", "DIVIDE([Total Revenue], 1000)", r"\$#,0.0\K"),
        ("Total Cost", "SUM(Sales[Cost])", r"\$#,0"),
        ("Total Profit", "SUM(Sales[Profit])", r"\$#,0"),
        ("Profit Margin", "DIVIDE([Total Profit], [Total Revenue])", "0.0%"),
        ("Total Orders", "DISTINCTCOUNT(Sales[OrderNumber])", "#,0"),
        ("Quantity Sold", "SUM(Sales[OrderQuantity])", "#,0"),
        ("Customers", "DISTINCTCOUNT(Sales[CustomerKey])", "#,0"),
        ("Avg Order Value", "DIVIDE([Total Revenue], [Total Orders])", r"\$#,0.00"),
        ("Revenue per Customer", "DIVIDE([Total Revenue], [Customers])", r"\$#,0.00"),
    ],
    "Returns": [
        ("Quantity Returned", "SUM(Returns[ReturnQuantity])", "#,0"),
        ("Return Rate", "DIVIDE([Quantity Returned], [Quantity Sold])", "0.00%"),
    ],
}

RELATIONSHIPS = [
    ("Sales", "ProductKey", "Products", "ProductKey"),
    ("Sales", "CustomerKey", "Customers", "CustomerKey"),
    ("Sales", "TerritoryKey", "Territories", "SalesTerritoryKey"),
    ("Sales", "OrderDate", "Calendar", "Date"),
    ("Returns", "ProductKey", "Products", "ProductKey"),
    ("Returns", "TerritoryKey", "Territories", "SalesTerritoryKey"),
    ("Returns", "ReturnDate", "Calendar", "Date"),
]


def table_tmdl(name, cols):
    t = "\t"
    out = [f"table {name}"]
    if name == "Calendar":
        out.append(f"{t}dataCategory: Time")
    out.append(f"{t}lineageTag: {gid()}")
    out.append("")
    for mname, expr, fmt in MEASURES.get(name, []):
        out += [f"{t}measure '{mname}' = {expr}", f"{t}{t}formatString: {fmt}",
                f"{t}{t}lineageTag: {gid()}", ""]
    for col, typ in cols:
        out.append(f"{t}column {col}")
        out.append(f"{t}{t}dataType: {TMDL_TYPE[typ]}")
        if name == "Calendar" and col == "Date":
            out.append(f"{t}{t}isKey")
        if typ in FORMAT:
            out.append(f"{t}{t}formatString: {FORMAT[typ]}")
        if col in HIDDEN:
            out.append(f"{t}{t}isHidden")
        out.append(f"{t}{t}lineageTag: {gid()}")
        out.append(f"{t}{t}summarizeBy: none")
        out.append(f"{t}{t}sourceColumn: {col}")
        if name == "Calendar" and col == "Month":
            out.append(f"{t}{t}sortByColumn: MonthNum")
        out += ["", f"{t}{t}annotation SummarizationSetBy = Automatic", ""]
    types = ", ".join(f'{{"{c}", {M_TYPE[ty]}}}' for c, ty in cols)
    m = [
        "let",
        f'    Source = Csv.Document(File.Contents(DataFolder & "\\{name}.csv"), '
        '[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        f'    Typed = Table.TransformColumnTypes(Promoted, {{{types}}}, "en-US")',
        "in",
        "    Typed",
    ]
    out.append(f"{t}partition {name} = m")
    out.append(f"{t}{t}mode: import")
    out.append(f"{t}{t}source =")
    out += [f"{t}{t}{t}{t}{line}" for line in m]
    out += ["", f"{t}annotation PBI_ResultType = Table", ""]
    return "\n".join(out)


def build_model():
    shutil.rmtree(MODEL, ignore_errors=True)
    d = MODEL / "definition"
    write(MODEL / "definition.pbism", {
        "$schema": f"{SCHEMA}/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.0", "settings": {}})
    write(MODEL / ".platform", platform("SemanticModel"))
    write(d / "database.tmdl", "database\n\tcompatibilityLevel: 1600\n")
    order = json.dumps(list(TABLES))
    write(d / "model.tmdl", "\n".join([
        "model Model",
        "\tculture: en-US",
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tsourceQueryCulture: en-US",
        "\tdataAccessOptions",
        "\t\tlegacyRedirects",
        "\t\treturnErrorValuesAsNull",
        "",
        f"annotation PBI_QueryOrder = {json.dumps(['DataFolder'] + list(TABLES))}",
        "",
        "annotation __PBI_TimeIntelligenceEnabled = 0",
        "",
        *[f"ref table {n}" for n in TABLES],
        "",
    ]))
    folder = str(DATA).replace('"', '""')
    write(d / "expressions.tmdl", "\n".join([
        f'expression DataFolder = "{folder}" meta [IsParameterQuery=true, Type="Text", '
        "IsParameterQueryRequired=true]",
        f"\tlineageTag: {gid()}",
        "",
        "\tannotation PBI_ResultType = Text",
        "",
    ]))
    rels = []
    for ft, fc, tt, tc in RELATIONSHIPS:
        rels += [f"relationship {gid()}", f"\tfromColumn: {ft}.{fc}", f"\ttoColumn: {tt}.{tc}", ""]
    write(d / "relationships.tmdl", "\n".join(rels))
    for name, cols in TABLES.items():
        write(d / "tables" / f"{name}.tmdl", table_tmdl(name, cols))
    _ = order


def platform(kind):
    return {"$schema": f"{SCHEMA}/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": kind, "displayName": NAME},
            "config": {"version": "2.0", "logicalId": gid()}}


# ---------------------------------------------------------------- report helpers

NAVY, ACCENT, GREY_BG, BORDER = "#1B2A41", "#2F6FED", "#F3F5F9", "#E3E7EE"
MEASURE_TABLE = {m[0]: t for t, ms in MEASURES.items() for m in ms}
CURRENCY_MILLIONS = {"Total Revenue", "Total Profit", "Total Cost"}


def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


AXES_CLEAN = {
    "categoryAxis": [{"properties": {"showAxisTitle": lit("false")}}],
    "valueAxis": [{"properties": {"showAxisTitle": lit("false")}}],
}


def fld(ref):
    """'Total Revenue' -> measure, 'Table.Column' -> column."""
    if "." in ref:
        table, prop = ref.split(".", 1)
        return "Column", table, prop
    return "Measure", MEASURE_TABLE[ref], ref


def field(ref):
    kind, table, prop = fld(ref)
    return {kind: {"Expression": {"SourceRef": {"Entity": table}}, "Property": prop}}


def projection(ref, active=False):
    kind, table, prop = fld(ref)
    p = {"field": field(ref), "queryRef": f"{table}.{prop}", "nativeQueryRef": prop}
    if kind == "Column" and active:
        p["active"] = True
    return p


def container(title=None):
    objs = {
        "background": [{"properties": {"show": lit("true"),
                                       "color": {"solid": {"color": lit("'#FFFFFF'")}},
                                       "transparency": lit("0D")}}],
        "border": [{"properties": {"show": lit("true"),
                                   "color": {"solid": {"color": lit(f"'{BORDER}'")}},
                                   "radius": lit("10D")}}],
        "padding": [{"properties": {"top": lit("8D"), "bottom": lit("8D"),
                                    "left": lit("10D"), "right": lit("10D")}}],
    }
    if title:
        objs["title"] = [{"properties": {"show": lit("true"), "text": lit(f"'{title}'"),
                                         "fontSize": lit("12D"), "bold": lit("true"),
                                         "fontColor": {"solid": {"color": lit(f"'{NAVY}'")}}}}]
    else:
        objs["title"] = [{"properties": {"show": lit("false")}}]
    return objs


class Page:
    def __init__(self, name, display):
        self.name, self.display, self.visuals = name, display, []

    def add(self, vtype, box, roles=None, title=None, sort=None, objects=None, chrome=True):
        x, y, w, h = box
        n = len(self.visuals)
        vname = f"{self.name}_v{n:02d}"
        visual = {"visualType": vtype}
        if roles:
            # Only axis-style roles mark columns active; table columns must not be.
            query = {"queryState": {role: {"projections": [
                projection(r, active=(role != "Values" or vtype == "slicer")) for r in refs]}
                for role, refs in roles.items()}}
            if sort:
                ref, direction = sort
                query["sortDefinition"] = {"sort": [{"field": field(ref), "direction": direction}],
                                           "isDefaultSort": True}
            visual["query"] = query
        if objects:
            visual["objects"] = objects
        visual["visualContainerObjects"] = container(title) if chrome else {
            "title": [{"properties": {"show": lit("false")}}],
            "background": [{"properties": {"show": lit("false")}}]}
        visual["drillFilterOtherVisuals"] = True
        self.visuals.append({
            "$schema": f"{SCHEMA}/item/report/definition/visualContainer/2.4.0/schema.json",
            "name": vname,
            "position": {"x": x, "y": y, "z": n * 1000, "height": h, "width": w, "tabOrder": n * 1000},
            "visual": visual,
        })

    # convenience builders
    def header(self, title, subtitle):
        self.text((24, 4, 1232, 70), [(title, 20, True, NAVY), (subtitle, 10, False, "#5B6B82")],
                  chrome=False)

    def text(self, box, lines, chrome=True, title=None):
        paragraphs = []
        for value, size, bold, color in lines:
            style = {"fontSize": f"{size}pt", "color": color}
            if bold:
                style["fontWeight"] = "bold"
            paragraphs.append({"textRuns": [{"value": value, "textStyle": style}]})
        self.add("textbox", box, title=title, chrome=chrome,
                 objects={"general": [{"properties": {"paragraphs": paragraphs}}]})

    def slicer(self, box, column, label):
        self.add("slicer", box, {"Values": [column]}, title=None, sort=(column, "Ascending"),
                 objects={"data": [{"properties": {"mode": lit("'Dropdown'")}}],
                          "header": [{"properties": {"show": lit("true"), "text": lit(f"'{label}'"),
                                                     "fontColor": {"solid": {"color": lit(f"'{NAVY}'")}}}}]})

    def card(self, box, measure):
        # Currency totals in millions with two decimals; counts and rates shown in full.
        units, precision = ("1000000D", "2D") if measure in CURRENCY_MILLIONS else ("1D", None)
        labels = {"fontSize": lit("22D"), "color": {"solid": {"color": lit(f"'{NAVY}'")}},
                  "labelDisplayUnits": lit(units)}
        if precision:
            labels["labelPrecision"] = lit(precision)
        self.add("card", box, {"Values": [measure]},
                 objects={"labels": [{"properties": labels}],
                          "categoryLabels": [{"properties": {"show": lit("true"), "fontSize": lit("10D")}}]})

    def chart(self, vtype, box, category, values, title, sort=None, labels=True, objects=None,
              label_units=None):
        objects = dict(objects or {})
        if labels:
            props = {"show": lit("true")}
            if label_units:
                props["labelDisplayUnits"] = lit(label_units)
            objects["labels"] = [{"properties": props}]
        if vtype in ("clusteredBarChart", "clusteredColumnChart"):
            objects["dataPoint"] = [{"properties": {"fill": {"solid": {"color": lit(f"'{ACCENT}'")}}}}]
        objects.update(AXES_CLEAN)
        if labels:
            objects["valueAxis"] = [{"properties": {"show": lit("false"), "showAxisTitle": lit("false")}}]
        roles = {"Category": [category], "Y": values}
        self.add(vtype, box, roles, title=title,
                 sort=sort or (values[0], "Descending"), objects=objects)


# ---------------------------------------------------------------- pages

def slicer_row(p, y=78):
    p.slicer((24, y, 296, 62), "Calendar.Year", "Year")
    p.slicer((336, y, 296, 62), "Territories.Country", "Country")
    p.slicer((648, y, 296, 62), "Products.Category", "Category")
    p.slicer((960, y, 296, 62), "Customers.Occupation", "Occupation")


def card_row(p, measures, y=150, h=86):
    w = (1232 - 16 * (len(measures) - 1)) / len(measures)
    for i, m in enumerate(measures):
        p.card((24 + i * (w + 16), y, w, h), m)


def build_pages():
    pages = []

    p = Page("overview", "Sales Overview")
    p.header("AdventureWorks Sales Dashboard",
             "Gold layer of the Azure pipeline · Jan 2015 – Jun 2017 · use the slicers to filter every visual")
    slicer_row(p)
    card_row(p, ["Total Revenue", "Total Profit", "Profit Margin", "Total Orders", "Customers",
                 "Return Rate"])
    p.add("lineChart", (24, 246, 800, 230),
          {"Category": ["Calendar.MonthStart"], "Y": ["Total Revenue", "Total Profit"]},
          title="Monthly revenue and profit", sort=("Calendar.MonthStart", "Ascending"),
          objects={"legend": [{"properties": {"show": lit("true"), "position": lit("'Top'")}}],
                   **AXES_CLEAN})
    p.add("donutChart", (840, 246, 416, 230),
          {"Category": ["Products.Category"], "Y": ["Total Revenue"]},
          title="Revenue by product category", sort=("Total Revenue", "Descending"),
          objects={"legend": [{"properties": {"show": lit("true"), "position": lit("'Right'")}}],
                   "labels": [{"properties": {"show": lit("true"), "labelStyle": lit("'Percent of total'")}}]})
    p.chart("clusteredBarChart", (24, 492, 400, 212), "Territories.Country", ["Total Revenue"],
            "Revenue by country")
    p.chart("clusteredColumnChart", (440, 492, 400, 212), "Calendar.Year", ["Total Orders"],
            "Orders by year", sort=("Calendar.Year", "Ascending"))
    p.text((856, 492, 400, 212), [
        ("Key insights (full period)", 12, True, NAVY),
        ("• $24.9M revenue, $10.5M profit (42% margin) from 25,164 orders.", 10, False, "#33415C"),
        ("• H1 2017 revenue ($9.19M) almost matched all of 2016 ($9.32M).", 10, False, "#33415C"),
        ("• Bikes bring 95% of revenue; accessories are 69% of units sold.", 10, False, "#33415C"),
        ("• The US and Australia bring 62% of revenue.", 10, False, "#33415C"),
        ("• Bikes have the highest return rate: 3.1% vs 2.2% overall.", 10, False, "#33415C"),
    ])
    pages.append(p)

    p = Page("products", "Products")
    p.header("Product performance", "Which products and categories drive revenue, volume and returns")
    slicer_row(p)
    card_row(p, ["Total Revenue", "Quantity Sold", "Avg Order Value", "Profit Margin",
                 "Quantity Returned"])
    p.chart("clusteredBarChart", (24, 246, 400, 458), "Products.Subcategory", ["Total Revenue"],
            "Revenue by subcategory", label_units="1000D")
    p.add("tableEx", (440, 246, 816, 270),
          {"Values": ["Products.ProductName", "Products.Category", "Revenue ($K)", "Quantity Sold",
                      "Profit Margin", "Return Rate"]},
          title="Products ranked by revenue", sort=("Revenue ($K)", "Descending"))
    p.chart("clusteredColumnChart", (440, 532, 400, 172), "Products.Category", ["Return Rate"],
            "Return rate by category")
    p.chart("clusteredColumnChart", (856, 532, 400, 172), "Products.Category", ["Quantity Sold"],
            "Units sold by category")
    pages.append(p)

    p = Page("customers", "Customers")
    p.header("Customer insights", "Who buys: occupation, income, age, education and gender")
    slicer_row(p)
    card_row(p, ["Customers", "Revenue per Customer", "Avg Order Value", "Total Orders"])
    p.chart("clusteredBarChart", (24, 246, 400, 222), "Customers.Occupation", ["Total Revenue"],
            "Revenue by occupation")
    p.chart("clusteredColumnChart", (440, 246, 400, 222), "Customers.IncomeBand", ["Total Revenue"],
            "Revenue by income band")
    p.add("donutChart", (856, 246, 400, 222),
          {"Category": ["Customers.Gender"], "Y": ["Total Revenue"]},
          title="Revenue by gender", sort=("Total Revenue", "Descending"),
          objects={"legend": [{"properties": {"show": lit("true"), "position": lit("'Right'")}}]})
    p.chart("clusteredColumnChart", (24, 484, 400, 220), "Customers.AgeGroup", ["Total Revenue"],
            "Revenue by age group", sort=("Customers.AgeGroup", "Ascending"))
    p.chart("clusteredBarChart", (440, 484, 400, 220), "Customers.EducationLevel", ["Customers"],
            "Customers by education level")
    p.text((856, 484, 400, 220), [
        ("What the customer data shows", 12, True, NAVY),
        ("• Professionals spend the most: $8.5M, 34% of revenue.", 10, False, "#33415C"),
        ("• Customers aged 45–54 bring the most revenue ($9.8M).", 10, False, "#33415C"),
        ("• Mid-income customers (40–80K) outspend every other band.", 10, False, "#33415C"),
        ("• Revenue is split almost evenly between women and men.", 10, False, "#33415C"),
        ("• The average order is worth $990.", 10, False, "#33415C"),
    ])
    pages.append(p)

    p = Page("returns", "Returns")
    p.header("Returns analysis", "Return rate = units returned ÷ units sold · early-2015 rates swing because "
             "monthly volumes were small, then settle near 2%")
    slicer_row(p)
    card_row(p, ["Quantity Returned", "Return Rate", "Quantity Sold"])
    p.add("lineChart", (24, 246, 816, 222),
          {"Category": ["Calendar.MonthStart"], "Y": ["Return Rate"]},
          title="Monthly return rate", sort=("Calendar.MonthStart", "Ascending"),
          objects=dict(AXES_CLEAN))
    p.chart("clusteredColumnChart", (856, 246, 400, 222), "Products.Category", ["Return Rate"],
            "Return rate by category")
    p.chart("clusteredBarChart", (24, 484, 400, 220), "Territories.Country", ["Return Rate"],
            "Return rate by country")
    p.add("tableEx", (440, 484, 816, 220),
          {"Values": ["Products.ProductName", "Products.Subcategory", "Quantity Returned",
                      "Quantity Sold", "Return Rate"]},
          title="Most returned products", sort=("Quantity Returned", "Descending"))
    pages.append(p)
    return pages


def build_report():
    shutil.rmtree(REPORT, ignore_errors=True)
    d = REPORT / "definition"
    write(REPORT / "definition.pbir", {
        "$schema": f"{SCHEMA}/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
    write(REPORT / ".platform", platform("Report"))
    theme_dir = REPORT / "StaticResources" / "SharedResources" / "BaseThemes"
    theme_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(THEME_SRC, theme_dir / "CY24SU10.json")
    write(d / "version.json", {
        "$schema": f"{SCHEMA}/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0"})
    write(d / "report.json", {
        "$schema": f"{SCHEMA}/item/report/definition/report/1.2.0/schema.json",
        "themeCollection": {"baseTheme": {"name": "CY24SU10", "reportVersionAtImport": "5.59",
                                          "type": "SharedResources"}},
        "layoutOptimization": "None",
        "resourcePackages": [{"name": "SharedResources", "type": "SharedResources",
                              "items": [{"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json",
                                         "type": "BaseTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True,
                     "defaultDrillFilterOtherVisuals": True,
                     "allowChangeFilterTypes": True,
                     "useEnhancedTooltips": True}})
    pages = build_pages()
    write(d / "pages" / "pages.json", {
        "$schema": f"{SCHEMA}/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": [p.name for p in pages], "activePageName": pages[0].name})
    for p in pages:
        pd = d / "pages" / p.name
        write(pd / "page.json", {
            "$schema": f"{SCHEMA}/item/report/definition/page/2.0.0/schema.json",
            "name": p.name, "displayName": p.display, "displayOption": "FitToPage",
            "height": 720, "width": 1280,
            "objects": {"background": [{"properties": {
                "color": {"solid": {"color": lit(f"'{GREY_BG}'")}},
                "transparency": lit("0D")}}]}})
        for v in p.visuals:
            write(pd / "visuals" / v["name"] / "visual.json", v)


def build_pbip():
    write(HERE / f"{NAME}.pbip", {
        "$schema": f"{SCHEMA}/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
        "settings": {"enableAutoRecovery": True}})
    write(HERE / ".gitignore", "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")


if __name__ == "__main__":
    if "--report-only" in sys.argv:
        sys.argv.remove("--report-only")
        build_report()
        sys.exit(print(f"Rebuilt {REPORT.name}"))
    build_model()
    build_report()
    build_pbip()
    print(f"Wrote {NAME}.pbip, {MODEL.name} and {REPORT.name} (data folder: {DATA})")
