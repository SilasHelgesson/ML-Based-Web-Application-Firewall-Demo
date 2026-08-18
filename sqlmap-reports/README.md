# sqlmap results

Each endpoint was run through `sqlmap` twice: directly against the web server
(`report_normal_*`) and through the filtering proxy (`report_protected_*`).
Run on 2026-06-15 against SQLite.

Proxy threshold was **0.9** for every run except
`report_protected_extreme_product_catalog.txt`, which used **0.75**.

| endpoint | direct | through proxy |
|---|---|---|
| login (`POST /login`) | injectable — boolean-based blind, time-based blind | **not injectable**, 141 × 403 |
| product (`GET /product?id=`) | injectable | **not injectable**, 60 × 403 |
| comment form (`POST /product`) | injectable | **not injectable**, 1191 × 403 |
| product catalog (`GET /products?category=`) | injectable | 163 × 403, but **one payload got through** |

Against the proxy, sqlmap's heuristics flag the target as WAF-protected in
every run.

## The catalog bypass

On `/products?category=`, one boolean-based blind payload survived at both
thresholds:

```
category=-1844 OR CASE WHEN 4830=4830 THEN 4830 ELSE JSON(CHAR(77,116,86,65)) END
```

It carries no quotes, no comment markers and no obvious tautology string — the
`4830=4830` equality is the only strong signal, and the `CHAR(...)` wrapper
looks numeric. Lowering the threshold to 0.75 didn't help; a near-identical
payload got through on that run too.

> [!NOTE]
> Re-scoring that exact payload against the shipped `ml/sqli_model.joblib`
> returns P(malicious) = 0.996 in every encoding, i.e. it *would* be blocked
> now. The recorded runs therefore probably used a different or earlier model
> than the one in the repository. Worth re-running before citing the bypass as
> a limitation of the current detector.

## Reproducing

```bash
sqlmap -u "http://127.0.0.1:8080/products?category=peripherals" --batch
sqlmap -u "http://127.0.0.1:8080/login" --data="username=test&password=test" --batch
sqlmap -u "http://127.0.0.1:8080/product?id=1" --batch
```

Swap port 8080 for 5000 to attack the unprotected backend.
