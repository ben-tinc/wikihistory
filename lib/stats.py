"""
def page_stats(data):
    entries = [(i["user"], i["pagename"]) for i in data]
    page_count = len({i[1] for i in entries})
    s = f"""
    Anzahl Seiten:\t {page_count}
    """
    return s


def user_stats(data):
    # Count number of entries.
    entry_count = len(data)
    anon_count = len([i["user"] for i in data if is_IP(i["user"])])
    reg_count = entry_count - anon_count
    # Count number of users.
    user_set = {i["user"] for i in data}
    all_users = len(user_set)
    anon_users = len([u for u in user_set if is_IP(u)])
    reg_users = all_users - anon_users

    s = f"""
    Anzahl revs:\t {entry_count}
    # anon. revs:\t {anon_count}
    # reg. revs:\t {reg_count}
    % of anon:\t\t {(anon_count / entry_count * 100):.3}%
    ----
    Anzahl users:\t {all_users}
    # anon. users:\t {anon_users}
    # reg. users:\t {reg_users}
     % of anon:\t\t {(anon_users / all_users * 100):.3}%
    """
    return s


def time_stats(data):
    entries = [(i['user'], parse_date(i['date'])) for i in data]
    return ""


def edit_size_stats(data):
    entries = [(i['user'], parse_size(i['change_size'])) for i in data]
    return ""


def general_stats(data):
    """Extract:
    • Number of pages
    • Number of edits
    • Number of anonymous edits
    • Proportion of anonymous edits
    • Number of unique users (non-anonymous)
    """
    if len(data) == 0:
        return  {}
    edit_count = len(data)
    page_count = len({e['pagename'] for e in data})
    user_count = len({e['user'] for e in data if not is_IP(e['user'])})
    anon_edit_count = len([e for e in data if is_IP(e['user'])])
    anon_edit_prop = anon_edit_count / edit_count
    return {
        "edit_count": edit_count,
        "page_count": page_count,
        "user_count": user_count,
        "anon_edit_count": anon_edit_count,
        "anon_edit_prop": anon_edit_prop,
    }


def stats_by_category(data):
    """
    • Number of pages per category
    • Number of edits per category
    • Number of anonymous edits
    • Proportion of anonymous edits
    • Number of unique users (non-anonymous)
    """
    cats = {e["category"] for e in data}
    return {
        cat: general_stats([e for e in data if e['category'] == cat])
        for cat in cats
    }


def stats_by_page(data):
    """Accumulate stats by page:
    • Number of pages per page
    • Number of edits per page
    • Number of anonymous edits
    • Proportion of anonymous edits
    • Number of unique users (non-anonymous)
    """
    pages = {e['pagename'] for e in data}
    return {
        page: general_stats([e for e in data if e['pagename'] == page])
        for page in pages
    }
 """
