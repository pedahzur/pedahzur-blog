# אגרגטור סקרי בחירות מול תוצאות אמת | Israel Election Poll Aggregator

צינור נתונים ב-Python שמושך **תוצאות בחירות רשמיות ברמת קלפי** מ-data.gov.il
ו**סקרי דעת קהל מצטברים** מוויקיפדיה, מצרף אותם, ומשווה בין תחזית הסקרים
למספרי המנדטים בפועל.

A Python pipeline that pulls **official per-polling-station ("קלפי") Knesset
results** from data.gov.il and **aggregated opinion polls** from Wikipedia,
aggregates them, and compares projected vs. actual Knesset seats.

## מקורות הנתונים | Data sources

| מקור | מה יש בו | גישה |
|------|----------|------|
| [data.gov.il — `votes-knesset`](https://data.gov.il/dataset/votes-knesset) | תוצאות אמת לכל כנסת, **שורה לכל קלפי** (שם יישוב, סמל יישוב, מספר קלפי, בזב, מצביעים, פסולים, כשרים, וקולות לכל רשימה לפי אות) | CKAN API + הורדת CSV |
| [ועדת הבחירות המרכזית](https://votes25.bechirot.gov.il/) | אותם נתונים, עם ממשק [לפי קלפיות](https://votes25.bechirot.gov.il/ballotresults) ו[לפי יישוב](https://votes25.bechirot.gov.il/cityresults) וייצוא ל-Excel | אתר לכל כנסת (votes21…votes25) |
| [Wikipedia — Opinion polling](https://en.wikipedia.org/wiki/Opinion_polling_for_the_2026_Israeli_legislative_election) | טבלה מובנית לכל סקר: תאריך, מכון סוקר, מדגם, מנדטים לכל מפלגה | MediaWiki API |

> **חלוקה גאוגרפית:** תוצאות האמת זמינות עד רמת **קלפי בודדת** (וממנה אפשר לצבור
> ליישוב/מחוז/ארצי). **סקרים הם ארציים בלבד** — אין סקרים ברמת קלפי/יישוב, ולכן
> ההשוואה סקר-מול-תוצאה היא ברמה הארצית במנדטים.

## התקנה | Install

```bash
pip install -r requirements.txt
```

## שימוש | Usage

> ⚠️ פקודות הרשת דורשות גישה ל-`data.gov.il` ול-`en.wikipedia.org`. בסביבות
> מוגבלות (כולל חלק מסביבות ההרצה המנוהלות) ההורדה תיכשל בשגיאת חיבור — הריצו
> ממכונה עם גישה לאינטרנט.

```bash
# רשימת קובצי התוצאות הזמינים ב-data.gov.il
python -m aggregator.cli list-results

# צבירת קובץ תוצאות לרמת יישוב + חלוקת מנדטים (בדר-עופר)
python -m aggregator.cli results --url <csv-url> --year 2022 --out data/

# אותו דבר מקובץ מקומי שכבר הורד
python -m aggregator.cli results --local data/knesset25.csv --year 2022 --out data/

# הורדת טבלת הסקרים מוויקיפדיה
python -m aggregator.cli polls --year 2022 --out data/
```

## API פנימי | Library API

```python
from aggregator import results, aggregate, parties, polls, compare

df = results.fetch_results_csv(url)            # קלפיות גולמיות
settlements = aggregate.aggregate_by_settlement(df)   # צבירה ליישוב
votes = aggregate.national_totals(df)          # סך קולות ארצי לפי אות
seats = aggregate.bader_ofer(votes)            # מנדטים (אחוז חסימה + ד'הונדט)
seats = parties.rename_to_party_names(seats, 2022)    # אות -> שם מפלגה

poll_table = polls.extract_polls(2022)         # סקרים מוויקיפדיה
ranking = compare.pollster_accuracy(poll_table, seats, party_columns=[...])
diff = compare.compare_seats(projected_seats, seats)  # שגיאה לכל מפלגה + MAE
```

## מבנה | Layout

```
aggregator/
  config.py      קבועים: כתובות API, כינויי עמודות עבריות, אחוז חסימה
  results.py     הורדת/קריאת קובצי קלפיות מ-data.gov.il (CKAN)
  normalize.py   זיהוי עמודות מפלגה והאחדת שמות עמודות המטא-דאטה
  parties.py     מיפוי אות-רשימה -> שם מפלגה, לכל מערכת בחירות
  aggregate.py   צבירה קלפי->יישוב->ארצי + חלוקת מנדטים בדר-עופר
  polls.py       גריפת טבלאות הסקרים מוויקיפדיה
  compare.py     השוואת תחזית-מול-תוצאה ודירוג דיוק סוקרים
  cli.py         ממשק שורת פקודה
tests/           בדיקות יחידה (רצות לא-מקוונות מול fixtures)
```

## בדיקות | Tests

```bash
python -m pytest -q
```

הבדיקות רצות **ללא רשת** מול נתוני דוגמה ב-`tests/fixtures/`, כך שלוגיקת הצבירה,
חישוב המנדטים, פרסור הסקרים וההשוואה מאומתת גם בלי גישה למקורות.

## הערות מתודולוגיות | Notes

- **בדר-עופר**: ממומש כשיטת ד'הונדט (הממוצעים הגדולים), עם תמיכה אופציונלית
  ב**הסכמי עודפים** (`surplus_agreements`) המאחדים זוג רשימות. ללא ההסכמים
  התוצאה מדויקת כל עוד אף זוג אינו חוצה גבול הקצאה.
- **נרמול מפלגות בין שנים**: אותיות הרשימה יציבות יותר משמות; ההשוואה בין סקרים
  (שמות) לתוצאות (אותיות) נשענת על `parties.py`, שיש להרחיב לכל מערכת בחירות.
- פרסור הסקרים הוא **best-effort** — מבנה הדף בוויקיפדיה משתנה מדי פעם; בדקו את
  הפלט לפני שמסתמכים על יישור העמודות במערכת בחירות חדשה.
