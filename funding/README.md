# Public biomedical R&D funding and medical research output, 2024

Data behind four charts comparing government biomedical & health R&D budgets with research output in medicine.

Compiled by Siebe Rozendal, November 2026.

## Files

- `biomedical_rnd_2024.csv`: one row per country or funder, plus one aggregate row. Compiled in a
  separate session; the code that built it is not in the repo.
- `funding_interactive.html`: the interactive chart on the catalog page. `tools/build_catalog.py`
  inserts it with the CSV rows. Two cards replace three earlier React charts:
  - **Bar chart**, with a switch between **Budget** (billion PPS or % of GDP, optionally split by
    funding type, US can be hidden) and **Output per budget** (papers or citations per million PPS,
    China can be hidden).
  - **Scatter, output vs budget**: circular flags, a log-log fit (log or linear axes), US and China
    can be hidden. The fit, its slope and the countries furthest above and below it are recomputed
    for what is shown. Each card keeps its own settings.

## Results (all 19 countries with output data, Ireland excluded)

- Papers vs budget: log-log slope 0.76, R² 0.84. Citations (excl. self): slope 0.53, R² 0.72.
  Without China and the US: 0.67 (R² 0.73) and 0.49 (R² 0.54).
- Papers per million PPS: highest Portugal 54.4, Australia 32.5, Canada 25.4; lowest Japan 7.6,
  US 8.4, South Korea 8.7. China 18.0 on its guessed budget.

## Columns

| Column | Meaning |
|---|---|
| `budget_status` | `reported` = Eurostat GBARD; `estimated` = built from national sources or scaled from partial reporting; `guess` = no comparable figure exists (China); `funder` = EU institutions; `none` = output data only |
| `budget_mio_pps` | Government biomedical & health R&D budget, 2024, million PPS. Charts show this in billions. |
| `budget_lo_mio_pps`, `budget_hi_mio_pps` | Plausible range, estimates only |
| `budget_pct_gdp`, `pct_gdp_lo`, `pct_gdp_hi` | Budget as % of GDP |
| `nabs07_directed_mio_pps` | Directed / project funding (GBARD objective NABS07) |
| `nabs123_univ_funds_mio_pps` | Medical R&D from general university funds (NABS123) |
| `nabs133_other_mio_pps` | Medical R&D from other sources (NABS133) |
| `components_basis` | Whether the three-way split is reported or approximate |
| `gbard_flags` | Eurostat flags: `p` provisional, `b` series break, `e` estimated, `d` definition differs |
| `med_docs_YYYY` | Documents in the Medicine subject area (SCImago/Scopus), 1999–2024 at five-year steps |
| `med_citations_2024`, `med_self_citations_2024`, `med_citations_excl_self_2024` | Citations to 2024 medicine documents |
| `budget_method` | How each estimate was built |
| `note` | Country-specific caveats |

PPS = purchasing power standards: currency converted so one unit buys the same basket of goods in every country.

## Definitions

- **Reported budgets** are the sum NABS07 + NABS123 + NABS133 from Eurostat dataflow `GBA_NABSFIN07`, unit `MIO_PPS`; % of GDP from unit `PC_GDP`.
- **United States** reports NABS07 only. That is comprehensive for the US, because NIH grants include overhead and there is no separate university block-fund stream.
- **EU institutions** are a funder, not a country. Their money comes from the EU budget and is additional to the national figures.
- **Citations** in the charts exclude self-citations.

## Caveats

- Estimated budgets come from different statistical systems. Treat their exact position as indicative.
- China's budget is a guess; its ratio values could be half or double.
- Turkey's figure is reported, but about 95% is apportioned university block funds, first reported in 2024.
- SCImago counts a co-authored paper once per country. The aggregate row therefore overstates unique papers, and the overstatement grows over time as co-authorship rises. Scopus coverage also expanded over the period.
- 2024 citations had about a year to accrue.
- Output per unit of budget is a rough productivity signal, not an efficiency ranking.

## Sources

- Eurostat, GBARD by socioeconomic objective (`GBA_NABSFIN07`), 2024.
- SCImago Journal & Country Rank (Scopus), Medicine subject area, 1999–2024.
- UK: NIHR, UKRI/MRC, Research England accounts 2024/25.
- South Korea: MOHW and MSIT budgets. Canada: CIHR. Australia: NHMRC, MRFF.
- EU institutions: European Commission Horizon Europe budgets; ERC 2025 Starting Grant statistics.
