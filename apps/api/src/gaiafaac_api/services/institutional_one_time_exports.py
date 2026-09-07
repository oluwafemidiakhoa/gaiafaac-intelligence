from __future__ import annotations

import io
import math
from typing import Any

from openpyxl import load_workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.data_source import AxDataSource, NumData, NumVal, StrData, StrRef, StrVal

from gaiafaac_api.services.branded_one_time_exports import (
    build_one_time_excel as _build_branded_excel,
)
from gaiafaac_api.services.branded_one_time_exports import (
    build_one_time_pdf as build_one_time_pdf,
)

_AMBER = "F7C948"
_TEAL = "07594F"


def _published_series_bounds(sheet) -> tuple[int, int] | None:
    header_row = next(
        (
            row
            for row in range(1, sheet.max_row + 1)
            if sheet.cell(row=row, column=1).value == "Published period"
        ),
        None,
    )
    if header_row is None:
        return None
    last_row = header_row
    for row in range(header_row + 1, sheet.max_row + 1):
        if sheet.cell(row=row, column=1).value in (None, ""):
            break
        last_row = row
    return (header_row, last_row) if last_row > header_row else None


def _cache_series(series, sheet, column: int, header: int, last: int) -> None:
    """Populate OOXML caches from the same visible cells, preserving blank gaps.

    References remain authoritative/editable in Excel; caches permit readers that
    do not recalculate chart references on first open to display the same data.
    """
    count = last - header
    labels = [str(sheet.cell(row=row, column=1).value) for row in range(header + 1, last + 1)]
    series.cat = AxDataSource(
        strRef=StrRef(
            f=str(Reference(sheet, min_col=1, min_row=header + 1, max_row=last)),
            strCache=StrData(
                ptCount=count,
                pt=[StrVal(idx=index, v=label) for index, label in enumerate(labels)],
            ),
        )
    )
    points = []
    for index, row in enumerate(range(header + 1, last + 1)):
        value = sheet.cell(row=row, column=column).value
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if math.isfinite(value):
                points.append(NumVal(idx=index, v=value))
    series.val.numRef.numCache = NumData(formatCode="General", ptCount=count, pt=points)
    if series.tx is not None and series.tx.strRef is not None:
        series.tx.strRef.strCache = StrData(
            ptCount=1,
            pt=[StrVal(idx=0, v=str(sheet.cell(row=header, column=column).value))],
        )


def _rebuild_visible_analytics_charts(body: bytes) -> bytes:
    workbook = load_workbook(io.BytesIO(body))
    if "Fiscal Analytics" not in workbook.sheetnames:
        return body
    sheet = workbook["Fiscal Analytics"]
    bounds = _published_series_bounds(sheet)
    if bounds is None:
        return body
    header_row, last_row = bounds
    sheet._charts = []

    trend = LineChart()
    trend.title = "Monthly gross vs net allocation"
    trend.style = 13
    trend.height = 7.4
    trend.width = 13.2
    trend.y_axis.title = "NGN billions"
    trend.y_axis.numFmt = "0.0,,,"
    trend.x_axis.title = "Published period"
    trend.visible_cells_only = False
    trend.display_blanks = "gap"
    for column in (2, 4):
        trend.add_data(
            Reference(sheet, min_col=column, min_row=header_row, max_row=last_row),
            titles_from_data=True,
        )
        _cache_series(trend.series[-1], sheet, column, header_row, last_row)
    trend.series[0].graphicalProperties.line.solidFill = _AMBER
    trend.series[1].graphicalProperties.line.solidFill = _TEAL
    trend.legend.position = "b"
    sheet.add_chart(trend, "J5")

    burden = BarChart()
    burden.type = "col"
    burden.title = "Deduction burden by published period"
    burden.style = 10
    burden.height = 7.4
    burden.width = 13.2
    burden.y_axis.title = "% of gross"
    burden.y_axis.numFmt = "0%"
    burden.x_axis.title = "Published period"
    burden.visible_cells_only = False
    burden.display_blanks = "gap"
    burden.add_data(
        Reference(sheet, min_col=5, min_row=header_row, max_row=last_row),
        titles_from_data=True,
    )
    _cache_series(burden.series[0], sheet, 5, header_row, last_row)
    burden.series[0].graphicalProperties.solidFill = _TEAL
    burden.series[0].graphicalProperties.line.solidFill = _TEAL
    burden.legend = None
    sheet.add_chart(burden, "J21")
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def build_one_time_excel(**kwargs: Any) -> tuple[str, str, bytes]:
    filename, media_type, body = _build_branded_excel(**kwargs)
    if kwargs.get("product_code") == "decision_pack":
        body = _rebuild_visible_analytics_charts(body)
    return filename, media_type, body
