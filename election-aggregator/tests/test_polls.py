from aggregator import compare, polls

# A miniature stand-in for the Wikipedia poll table layout: a header row with a
# date + pollster + party-seat columns, then a few poll rows (plus footnote
# markers and a non-poll table that must be ignored).
SAMPLE_HTML = """
<table class="wikitable">
  <caption>navbox to ignore</caption>
  <tr><th>Links</th><th>More</th></tr>
  <tr><td>a</td><td>b</td></tr>
</table>
<table class="wikitable">
  <tr>
    <th>Date</th><th>Polling firm</th><th>Sample</th>
    <th>Likud</th><th>Yesh Atid</th><th>Shas</th><th>Meretz</th>
  </tr>
  <tr><td>1 Jun 2022</td><td>Midgam</td><td>500</td><td>34</td><td>22</td><td>9</td><td>5</td></tr>
  <tr><td>2 Jun 2022</td><td>Panels[1]</td><td>600</td><td>33</td><td>24</td><td>10</td><td>4</td></tr>
  <tr><td>3 Jun 2022</td><td>Midgam</td><td>550</td><td>35</td><td>21</td><td>9</td><td>6</td></tr>
</table>
"""


def test_extract_polls_picks_poll_table_and_cleans_headers():
    table = polls.extract_polls(2022, html=SAMPLE_HTML)
    assert len(table) == 3
    assert "Polling firm" in table.columns
    assert "Likud" in table.columns
    # footnote marker stripped from header (none here) and from values preserved
    assert "Midgam" in table["Polling firm"].values


def test_pollster_accuracy_ranks_by_error():
    table = polls.extract_polls(2022, html=SAMPLE_HTML)
    actual = {"Likud": 32, "Yesh Atid": 24, "Shas": 11, "Meretz": 0}
    ranking = compare.pollster_accuracy(
        table, actual, party_columns=["Likud", "Yesh Atid", "Shas", "Meretz"]
    )
    assert set(ranking["pollster"]) == {"Midgam", "Panels"}
    # ranking sorted ascending by MAE (most accurate first)
    assert ranking["mae"].is_monotonic_increasing
