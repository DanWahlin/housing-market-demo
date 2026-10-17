"""Add a real PivotTable (with a calculated field) and turn the Pivot sheet chart into a PivotChart.

XlsxWriter cannot write PivotTables, so this module adds the Office Open XML parts to the saved file.
"""
import re
import zipfile
from xml.sax.saxutils import quoteattr

NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" ' \
     'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT = "application/vnd.openxmlformats-officedocument.spreadsheetml"
PT_NAME = "ptRegionYear"
REGION, YEAR, LOANS = 2, 4, 11
CALC_NAME, CALC_FORMULA = "Weighted loan size", "'Total dollar volume'/'Total loans'"


def _num_items(vals):
    ints = ' containsInteger="1"' if all(float(v).is_integer() for v in vals) else ""
    return (f'containsSemiMixedTypes="0" containsString="0" containsNumber="1"{ints} '
            f'minValue="{min(vals)}" maxValue="{max(vals)}"')


def _cache(headers, rows, regions, years):
    fields = []
    for i, h in enumerate(headers):
        col = [r[i] for r in rows]
        if i == REGION:
            items = "".join(f"<s v={quoteattr(v)}/>" for v in regions)
            fields.append(f'<cacheField name={quoteattr(h)} numFmtId="0"><sharedItems count="{len(regions)}">{items}</sharedItems></cacheField>')
        elif i == YEAR:
            items = "".join(f'<n v="{y}"/>' for y in years)
            fields.append(f'<cacheField name={quoteattr(h)} numFmtId="0"><sharedItems {_num_items(years)} count="{len(years)}">{items}</sharedItems></cacheField>')
        elif isinstance(col[0], str):
            fields.append(f'<cacheField name={quoteattr(h)} numFmtId="0"><sharedItems/></cacheField>')
        else:
            fields.append(f'<cacheField name={quoteattr(h)} numFmtId="0"><sharedItems {_num_items(col)}/></cacheField>')
    fields.append(f'<cacheField name={quoteattr(CALC_NAME)} numFmtId="0" formula={quoteattr(CALC_FORMULA)} databaseField="0"/>')
    definition = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<pivotCacheDefinition {NS} r:id="rId1" refreshOnLoad="1" '
        f'refreshedBy="build_workbook.py" refreshedDate="46312.5" createdVersion="6" refreshedVersion="6" minRefreshableVersion="3" '
        f'recordCount="{len(rows)}"><cacheSource type="worksheet"><worksheetSource name="tblData"/></cacheSource>'
        f'<cacheFields count="{len(fields)}">{"".join(fields)}</cacheFields></pivotCacheDefinition>')
    recs = []
    for r in rows:
        cells = []
        for i, v in enumerate(r):
            if i == REGION:
                cells.append(f'<x v="{regions.index(v)}"/>')
            elif i == YEAR:
                cells.append(f'<x v="{years.index(v)}"/>')
            elif isinstance(v, str):
                cells.append(f"<s v={quoteattr(v)}/>")
            else:
                cells.append(f'<n v="{v}"/>')
        recs.append("<r>" + "".join(cells) + "</r>")
    records = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<pivotCacheRecords {NS} count="{len(rows)}">'
               + "".join(recs) + "</pivotCacheRecords>")
    return definition, records


def _table(n_fields, regions, years, usd_fmt):
    nr, ny = len(regions), len(years)
    pf = []
    for i in range(n_fields + 1):
        if i == REGION:
            items = "".join(f'<item x="{k}"/>' for k in range(nr))
            pf.append(f'<pivotField axis="axisRow" showAll="0"><items count="{nr + 1}">{items}<item t="default"/></items></pivotField>')
        elif i == YEAR:
            items = "".join(f'<item x="{k}"/>' for k in range(ny))
            pf.append(f'<pivotField axis="axisCol" showAll="0"><items count="{ny + 1}">{items}<item t="default"/></items></pivotField>')
        elif i == LOANS:
            pf.append('<pivotField dataField="1" showAll="0"/>')
        elif i == n_fields:
            pf.append('<pivotField dataField="1" dragToRow="0" dragToCol="0" dragToPage="0" showAll="0" defaultSubtotal="0"/>')
        else:
            pf.append('<pivotField showAll="0"/>')
    row_items = "<i><x/></i>" + "".join(f'<i><x v="{k}"/></i>' for k in range(1, nr)) + '<i t="grand"><x/></i>'
    col_items = ""
    for d in range(2):
        di = f' i="{d}"' if d else ""
        dv = f' v="{d}"' if d else ""
        col_items += f'<i{di}><x{dv}/><x/></i>'
        col_items += "".join(f'<i r="1"{di}><x v="{k}"/></i>' for k in range(1, ny))
    col_items += '<i t="grand"><x/></i><i t="grand" i="1"><x/></i>'
    n_cols = 1 + 2 * ny + 2
    last_col = chr(ord("A") + n_cols - 1)
    ref = f"A3:{last_col}{3 + 3 + nr}"
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<pivotTableDefinition {NS} name="{PT_NAME}" cacheId="1" '
        'applyNumberFormats="0" applyBorderFormats="0" applyFontFormats="0" applyPatternFormats="0" applyAlignmentFormats="0" '
        'applyWidthHeightFormats="1" dataCaption="Values" updatedVersion="6" minRefreshableVersion="3" useAutoFormatting="1" '
        'itemPrintTitles="1" createdVersion="6" indent="0" outline="1" outlineData="1" multipleFieldFilters="0" chartFormat="1" '
        'rowHeaderCaption="Region" colHeaderCaption="Year">'
        f'<location ref="{ref}" firstHeaderRow="1" firstDataRow="3" firstDataCol="1"/>'
        f'<pivotFields count="{len(pf)}">{"".join(pf)}</pivotFields>'
        f'<rowFields count="1"><field x="{REGION}"/></rowFields><rowItems count="{nr + 1}">{row_items}</rowItems>'
        f'<colFields count="2"><field x="-2"/><field x="{YEAR}"/></colFields><colItems count="{2 * ny + 2}">{col_items}</colItems>'
        f'<dataFields count="2"><dataField name="Loans (count)" fld="{LOANS}" baseField="0" baseItem="0" numFmtId="3"/>'
        f'<dataField name="Average loan size" fld="{n_fields}" baseField="0" baseItem="0" numFmtId="{usd_fmt}"/></dataFields>'
        '<pivotTableStyleInfo name="PivotStyleMedium2" showRowHeaders="1" showColHeaders="1" showRowStripes="0" '
        'showColStripes="0" showLastColumn="1"/></pivotTableDefinition>')


def add_pivot(path, headers, rows, regions, years):
    with zipfile.ZipFile(path) as z:
        files = {n: z.read(n) for n in z.namelist()}
    text = lambda n: files[n].decode("utf-8")

    usd_fmt = re.search(r'<numFmt numFmtId="(\d+)" formatCode="\$#,##0"/>', text("xl/styles.xml")).group(1)
    definition, records = _cache(headers, rows, regions, years)
    files["xl/pivotCache/pivotCacheDefinition1.xml"] = definition.encode()
    files["xl/pivotCache/pivotCacheRecords1.xml"] = records.encode()
    files["xl/pivotCache/_rels/pivotCacheDefinition1.xml.rels"] = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f'<Relationship Id="rId1" Type="{REL}/pivotCacheRecords" Target="pivotCacheRecords1.xml"/></Relationships>').encode()
    files["xl/pivotTables/pivotTable1.xml"] = _table(len(headers), regions, years, usd_fmt).encode()
    files["xl/pivotTables/_rels/pivotTable1.xml.rels"] = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f'<Relationship Id="rId1" Type="{REL}/pivotCacheDefinition" Target="../pivotCache/pivotCacheDefinition1.xml"/></Relationships>').encode()

    wb = text("xl/workbook.xml")
    wb = re.sub(r"(<calcPr[^>]*/>)", r'\1<pivotCaches><pivotCache cacheId="1" r:id="rIdPivotCache1"/></pivotCaches>', wb)
    files["xl/workbook.xml"] = wb.encode()
    files["xl/_rels/workbook.xml.rels"] = text("xl/_rels/workbook.xml.rels").replace(
        "</Relationships>", f'<Relationship Id="rIdPivotCache1" Type="{REL}/pivotCacheDefinition" Target="pivotCache/pivotCacheDefinition1.xml"/></Relationships>').encode()

    # Find the Pivot sheet file and its chart.
    sheets = re.findall(r'<sheet name="([^"]+)" sheetId="\d+" r:id="(rId\d+)"/>', wb)
    rid = dict(sheets)["Pivot"]
    sheet_file = re.search(rf'Id="{rid}" Type="[^"]+" Target="(worksheets/[^"]+)"', text("xl/_rels/workbook.xml.rels")).group(1)
    sheet_rels = f"xl/worksheets/_rels/{sheet_file.split('/')[-1]}.rels"
    drawing = re.search(r'Target="\.\./drawings/([^"]+)"', text(sheet_rels)).group(1)
    chart = re.search(r'Target="\.\./charts/([^"]+)"', text(f"xl/drawings/_rels/{drawing}.rels")).group(1)
    files[sheet_rels] = text(sheet_rels).replace(
        "</Relationships>", f'<Relationship Id="rIdPivotTable1" Type="{REL}/pivotTable" Target="../pivotTables/pivotTable1.xml"/></Relationships>').encode()

    cx = text(f"xl/charts/{chart}")
    src = f"<c:pivotSource><c:name>[{path.name}]Pivot!{PT_NAME}</c:name><c:fmtId val=\"0\"/></c:pivotSource>"
    cx = cx.replace("<c:chart>", src + "<c:chart>", 1)
    files[f"xl/charts/{chart}"] = cx.encode()

    files["[Content_Types].xml"] = text("[Content_Types].xml").replace("</Types>", (
        f'<Override PartName="/xl/pivotCache/pivotCacheDefinition1.xml" ContentType="{CT}.pivotCacheDefinition+xml"/>'
        f'<Override PartName="/xl/pivotCache/pivotCacheRecords1.xml" ContentType="{CT}.pivotCacheRecords+xml"/>'
        f'<Override PartName="/xl/pivotTables/pivotTable1.xml" ContentType="{CT}.pivotTable+xml"/></Types>')).encode()

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in files.items():
            z.writestr(n, b)
