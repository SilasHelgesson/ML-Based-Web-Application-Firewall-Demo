# Datasets

Two files, both taken from the [`nidnogg/sqliv5-dataset`](https://github.com/nidnogg/sqliv5-dataset)
repository.

| file | rows | what it is |
|---|---|---|
| `SQLiV3.csv` | 30,863 usable | Training set. Headerless, `payload,label` by position — pass `--text-col 0 --label-col 1`. |
| `fuzzed_data.csv` | 9,627 | Adversarial evaluation set, all attacks (`label` = 1). Has a header row, so the defaults work. |

**SQLiV3** is by Syed Saqlain Hussain, originally published
[on Kaggle](https://www.kaggle.com/datasets/syedsaqlainhussain/sql-injection-dataset).
Benign rows are realistic field values (usernames, numbers, addresses);
malicious rows are real injection payloads. 54 rows have unrecognised labels
and 1 is empty — `load_csv` drops and reports them.

**fuzzed_data.csv** holds adversarial variants generated with
[WAF-A-MoLE](https://github.com/AvalZ/WAF-A-MoLE) by Andrea Valenza and Luca
Demetrio: octal/binary/hex literals, exotic whitespace, case mangling. None of
it was used in training, so the detection rate on it is an honest measure of
generalisation to obfuscation.

The upstream repo also ships SQLiV4/V5 and several intermediate JSON exports;
they aren't used here and were left out to keep the repository small.

## Licensing

These two files are MIT-licensed by
[Henrique Vermelho de Toledo](https://github.com/nidnogg) (`nidnogg`), copyright
2022 — full terms in [`LICENSE.upstream`](LICENSE.upstream). Attribution is
required if you redistribute them. They are **not** covered by the GPL that
applies to the rest of this repository.

One caveat: the MIT license is on the
[`nidnogg/sqliv5-dataset`](https://github.com/nidnogg/sqliv5-dataset) mirror.
The terms of the original
[Kaggle listing](https://www.kaggle.com/datasets/syedsaqlainhussain/sql-injection-dataset)
are a separate question and worth checking directly if redistribution matters
to you.
