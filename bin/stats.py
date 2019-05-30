from collections import OrderedDict
from datetime import datetime
import json
import re

import numpy as np
import pandas as pd
from pandas import DataFrame, Index, Series


DATE_PATTERN = re.compile(r'(\d{2}):(\d{2}), (\d{1,2})\. (\S{3})\.? (\d{4})')

MONTHS = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun',
          'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']


def load(fn="results/rechtsextremismus.json"):
    data = None
    with open(fn) as f:
        data = json.load(f)
    return data


def is_IPv4(string):
    # e.g. "23.123.0.42"
    pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    return re.match(pattern, string) is not None


def is_IPv6(string):
    # e.g. '2001:628:404:31:58c0:f621:1aea:e7f5'
    elem = r"[0-9a-f]{0,4}"
    pattern = r"{}:{}:{}:{}:{}:{}:{}:{}".format(elem, elem, elem, elem,
                                                elem, elem, elem, elem)
    return re.match(pattern, string) is not None


def is_IP(string):
    return is_IPv4(string) or is_IPv6(string)


def parse_size(string):
    """Given a string like `"(-48)"`, return an `int`
    of the edit size. It can be null.
    """
    if string == "null":
        return 0
    try:
        return int(string[1:-1])
    except ValueError:
        return 0


def parse_date(string):
    """Given a string like `"12:02, 28. M\u00e4r. 2018"`, or
    "`18:33, 1. Apr. 2019`",
    create a proper python datetime object.
    """
    match = re.match(DATE_PATTERN, string)
    try:
        hour, minute, day, mon, year = match.groups()
        mon = MONTHS.index(mon) + 1
        return datetime(int(year), mon, int(day), int(hour), int(minute))
    except Exception as e:
        # Whatever, we return None anyway..
        print(e)
        pass
    return None


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


def filter_irrelevant(data):
    """Filter out edits which are very small or instantly reverted."""


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


""" def order_by_anon_prop(data):
    data = OrderedDict(data)
    data = sorted(data.items(), key=lambda x: x[1]['anon_edit_prop'])
    return data """


def combine_dfs(d1, d2):
    return d1.append(d2)


def to_dataframe(data):
    return DataFrame(data)


def add_is_IP(data):
    """Compute and add a new column to the `DataFrame` which contains info
    about wether the user name is just an IP address.
    """
    data['is_IP'] = data['user'].map(is_IP)
    return data



def add_revert_heuristic(data):
    """This is much better than my previous try, but it still depends on the
    data frame being sorted by date and the edits of each page being grouped
    together.
    """
    orig = data[['pagename', 'change_size', 'revert']]
    prev_ = orig.shift(-1).add_prefix('prev_')
    next_ = orig.shift(1).add_prefix('next_')

    for_is_revert = pd.concat([orig, prev_], axis=1)
    for_got_reverted = pd.concat([orig, next_], axis=1)

    def heuristic(name, change, cmp_name, cmp_change, later_revert):
        """Do the actual work. `name` and `change` always refers to the current
        row, the cmp parameters belong to the previous (in case of a revert
        check) or to the next (for a got-reverted check) row. The `later_revert`
        parameter is the revert column of the later edit.
        """
        if later_revert:
            return True
        return name == cmp_name and change + cmp_change == 0

    probably_revert = for_is_revert.apply(
        lambda x: heuristic(x.pagename, x.change_size,
                            x.prev_pagename, x.prev_change_size,
                            x.revert),
        axis=1)
    probably_reverted = for_got_reverted.apply(
        lambda x: heuristic(x.pagename, x.change_size,
                            x.next_pagename, x.next_change_size,
                            x.next_revert),
        axis=1)
    data['probably_revert'] = probably_revert
    data['probably_reverted'] = probably_reverted
    return data


def normalize_change_size(data):
    data['change_size'].fillna(value=0, inplace=True)
    return data


def main():
    # Load most recent data.
    d1 = load("results/Geschichte_der_Malerei.json")
    d2 = load("results/Rest.json")
    data = combine_dfs(to_dataframe(d1), to_dataframe(d2))

    # Add derivative data columns.
    data['datetime'] = data['date'].map(parse_date)
    data['change_size'] = data['change_size'].map(int)
    data['is_IP'] = data['user'].map(is_IP)
    # Maybe modify the API to return the new column(s) instead?
    data = add_revert_heuristic(data)

    return data
