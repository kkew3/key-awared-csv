# Key-awared CSV

This repo defines a CSV dialect with primary and foreign key.

The field delimiter is `,`.
The row delimiter is `\n`.
The first row is the CSV header.
All other rows must have the same number of fields as that of the first row.
The first row must not be empty.
There's no field quote, so `,` within a field should be replaced by other symbols.
Moreover, pairs of `<` and `>` are reserved words and should not be used as literal words.
The trailing whitespace won't be truncated.

From the second row, the first column contains the primary keys.
Primary keys must be non-empty.
The primary key of each row must be unique.
Any primary key can be referenced from anywhere among the rest columns from the second row.
Denote a particular primary key as `KEY`.
To reference `KEY`, one may write `<KEY>`.

An example key-awared CSV:

```csv
ID,title 1,title2 
 ,abc,<1> 
2,hello, world
1,hello<2>,again
```

This CSV have three columns named `ID`, `title 1` and `title2 `.
It has three rows with primary keys ` `, `2` and `1`.
The first row consists of three fields: ` `, `abc`, `<1> `
The second row consists of three fields: `2`, `hello`, ` world`.
The third row consists of three fields: `1`, `hello<2>`.
There's one foreign key in the third field of the first row, and there's another one in the second field of the third row.

## keyedcsv-rename

After

```bash
#python3 -m virtualenv rt
#. rt/bin/activate
#pip install -r requirements-dev.txt
make
make install
```

`keyedcsv-rename` appears under `./bin/`.
It can be used to renamed primary keys in a key-awared CSV file.
Denote the above mentioned example CSV as `a.csv`.
After running

```bash
bin/keyedcsv-rename a.csv b.csv 2 lol
```

The output `b.csv` appears as:

```csv
ID,title 1,title2 
 ,abc,<1> 
lol,hello, world
1,hello<lol>,again
```

## keyedcsv module

`keyedcsv.py` defines the format of the key-awared CSV, and how the CSV is parsed and handled.
It can used by standard `import` statement.
