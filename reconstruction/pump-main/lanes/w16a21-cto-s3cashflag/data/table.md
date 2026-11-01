| cell | form | spellings folded | bytes | M | Mperm | Mhc | L--- | Lrfj | 6 KB swap | curve-store cashback | joint p1 (forces) | joint p2 (forces) |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |
| m0 | main 5998913 |  | 27400 | 2251 | 2295 | 2302 | 2257 | 3006 | no | 2 loads + and + and 1 (main) | 2329 (7) | 2339 (9) |
| S3n | S3n (w16a08): hf out-param, curve store from hf, event holder.unwrap_or(false) |  | 27416 | 1990 | 2289 | 2296 | 2121 | 3009 | no | 2 loads + and + and 1 (main) | 2308 (7) | 2347 (13) |
| c1 | cf:&mut bool per arm (false / st.cashback), head cashback removed, curve store from cf, event re-reads curve | c7, t1, t3, c11 | 27184 | 1979 | 2140 | 2141 | 2055 | 2994 | 1 outlier | load at store, no mask |  |  |
| c2 | c1 + event reads cf | c8, t2, t4, c12 | 27184 | 1981 | 2141 | 2142 | 2057 | 2989 | 1 outlier | load at store, no mask | 2210 (6) | 2272 (14) |
| c3 | c1 + fee check (330) reads *cf |  | 27200 | 1707 | 1981 | 1990 | 1955 | 2957 | 1 outlier | load at store, no mask |  |  |
| c4 | c3 + event reads cf |  | 27200 | 1709 | 1982 | 1991 | 1957 | 2952 | 1 outlier | load at store, no mask |  |  |
| c5 | cf written once at the end of validate (after the fee checks) |  | 27168 | 1971 | 2150 | 2150 | 2069 | 2995 | 1 outlier | 1 load + and 1 (orig) | 2270 (8) | 2289 (14) |
| c6 | c5 + event reads cf |  | 27176 | 1965 | 2141 | 2142 | 2063 | 2990 | 1 outlier | 1 load + and 1 (orig) |  |  |
| c9 | no cf: execute derives !hf&&st.cashback after validate | c13 | 27216 | 1890 | 2131 | 2139 | 1995 | 3002 | 1 outlier | 2 loads + and + and 1 (main) |  |  |
| c10 | c9 + event reads it | c13e | 27240 | 1897 | 2135 | 2140 | 2000 | 2996 | 1 outlier | 2 loads + and + and 1 (main) |  |  |
| c14 | per-arm cashback in execute's shared/holder arms (pa1 tuple) on S3 |  | 27368 | 1890 | 2138 | 2141 | 2011 | 3004 | no | 1 load + and 1 (orig) | 2234 (5) | 2248 (10) |
| c14e | c14 + event reads it |  | 27376 | 1883 | 2131 | 2135 | 2004 | 2999 | no | 1 load + and 1 (orig) |  |  |
| c15 | holder arm clears st.cashback (&mut CtoState); fee check + curve store read st.cashback |  | 27176 | 1815 | 2005 | 2005 | 2007 | 2947 | 1 outlier | load at store, no mask |  |  |
| c15e | c15 + event reads it |  | 27336 | 1757 | 1909 | 1913 | 1938 | 2856 | 1 outlier | ? |  |  |
| c16 | validate -> Result<(Pubkey,bool)> carries cashback (i1 SSA) |  | 27184 | 1186 | 1406 | 1433 | 1451 | 2994 | 1 outlier | load at store, no mask |  |  |
| c16e | c16 + event reads it |  | 27184 | 1193 | 1409 | 1438 | 1458 | 2989 | 1 outlier | load at store, no mask |  |  |
| c18 | cf written right after validate's cashback local (before fee checks) |  | 27344 | 1646 | 1754 | 1761 | 1777 | 2848 | 1 outlier | ? |  |  |
| c18e | c18 + event reads it |  | 27256 | 1724 | 1831 | 1837 | 1880 | 2960 | 1 outlier | load at store, no mask |  |  |
| c19 | four arms in execute's block (non-shared split on holder) |  | 27544 | 1964 | 2121 | 2131 | 2051 | 3002 | no | 1 load + and 1 (orig) |  |  |
| c19e | c19 + event reads it |  | 27552 | 1958 | 2112 | 2122 | 2044 | 2996 | no | 1 load + and 1 (orig) |  |  |
| c20 | per-arm cashback in execute's arms, non-shared arm reuses the head cashback (head kept) |  | 27304 | 1973 | 2139 | 2157 | 2025 | 3004 | 1 outlier | 1 load + and 1 (orig) | 2257 (12) | 2291 (18) |
| c20e | c20 + event reads it |  | 27312 | 1968 | 2134 | 2152 | 2020 | 2999 | 1 outlier | 1 load + and 1 (orig) |  |  |
| c5m | LOO control: main (no S3) + c5's flag |  | 27176 | 1854 | 2126 | 2138 | 1982 | 2995 | no | 1 load + and 1 (orig) |  |  |
| c5g | c5 + g1 (creator copy before validate) |  | 27192 | 1969 | 2126 | 2136 |  |  |  | 1 load + and 1 (orig) |  |  |
| c5F | c5 + Fa (validate reads args.0) |  | 27528 | 1754 | 1971 | 1975 |  |  |  | ? |  |  |
| c5gF | c5 + g1 + Fa |  | 27648 | 1751 | 1973 | 1976 |  |  |  | ? |  |  |
| c20g | c20 + g1 |  | 27368 | 1956 | 2139 | 2156 |  |  |  | 1 load + and 1 (orig) |  |  |
| c20F | c20 + Fa |  | 27672 | 1513 | 1613 | 1620 |  |  |  | ? |  |  |
| c20gF | c20 + g1 + Fa |  | 27768 | 1512 | 1611 | 1617 |  |  |  | ? |  |  |
