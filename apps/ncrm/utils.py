# coding=UTF-8

def pagination_tool(page, record, page_count = 20):
    import math

    PAGE_COUNT = page_count
    HALF_SHOW_PAGE = 3 # 分页显示数量的一半
    SHOW_PAGE = HALF_SHOW_PAGE * 2 + 1

    page = int(page)
    if isinstance(record, list):
        record_count = len(record)
    else:
        record_count = record.count()

    page_count = int(math.ceil(record_count * 1.0 / PAGE_COUNT))
    if page > page_count:
        page = 1

    start_page = (page - 1) * PAGE_COUNT
    end_page = page * PAGE_COUNT

    if end_page >= record_count:
        end_page = record_count
    if start_page < 0:
        start_page = 0


    record = record[start_page:end_page]

    if page_count <= SHOW_PAGE or page <= HALF_SHOW_PAGE + 1:
        page_range = xrange(1, page_count <= SHOW_PAGE and page_count + 1 or SHOW_PAGE + 1)
    else:
        page_range = xrange(page - HALF_SHOW_PAGE, page + HALF_SHOW_PAGE > page_count and page_count or page + HALF_SHOW_PAGE + 1)
    if (page + 3) > page_count and page_count > SHOW_PAGE:
        page_range = xrange(page_count - SHOW_PAGE + 1, page_count + 1)

    page_info = {
               'start_page':start_page,
               'end_page':end_page,
               'page':page,
               'page_xrange':list(page_range),
               'page_count':page_count,
               'record_count':record_count
               }
    return page_info, record
