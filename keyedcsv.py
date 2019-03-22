import sys
import re
import typing


# Experiment CSV records specification
FIELD_DELIMITER = ','
SENTENCE_DELIMITER = '. '
FK_OPEN_QUOTE = '<'
FK_CLOSE_QUOTE = '>'


FK_PATTERN = re.compile('{0}([^{1}]+){1}'
                        .format(FK_OPEN_QUOTE, FK_CLOSE_QUOTE))


def procline(string: str) -> str:
    return string.rstrip('\n')


class EmptyDocument(BaseException):
    """
    Used to signify that the underlying document is empty, thus unable to
    tell certain properties about it.
    """
    pass


class InvalidDocumentError(BaseException):
    """
    Raised if the document is malformed.
    """

    def __init__(self, msg: str = None, lineno: int = None):
        if msg is None and lineno is None:
            super().__init__()
        elif msg is None:
            super().__init__('Invalid document at line {}'.format(lineno))
        elif lineno is None:
            super().__init__('Invalid document: {}'.format(msg))
        else:
            super().__init__('Invalid document at line {}: {}'
                             .format(lineno, msg))


class BadForeignKeyError(InvalidDocumentError):
    """
    Raised if a <KEY> is referencing a non-existent <KEY>.
    """

    def __init__(self, fk: str = None, lineno: int = None):
        if fk is not None:
            fk = 'bad foreign key `{}\''.format(fk)
        super().__init__(msg=fk, lineno=lineno)


class BadPrimaryKeyError(InvalidDocumentError):
    """
    Raised if a primary key is not unique.
    """

    def __init__(self, pk: str = None, lineno: int = None):
        if pk is not None:
            pk = 'bad primary key `{}\''.format(pk)
        super().__init__(msg=pk, lineno=lineno)


class Fk:
    def __init__(self, refpk: str):
        self.refpk = refpk

    def __str__(self):
        return ''.join((FK_OPEN_QUOTE, self.refpk, FK_CLOSE_QUOTE))

    def __repr__(self):
        return 'ForeignKey({})'.format(self.refpk)

    def __eq__(self, other):
        if not isinstance(other, Fk):
            return NotImplemented
        return self.refpk == other.refpk

    def __hash__(self):
        return hash(self.refpk)

    def __lt__(self, other):
        if not isinstance(other, Fk):
            return NotImplemented
        return self.refpk < self.other


class Field:
    """
    A string-like object that's foreign-key-aware.

    >>> Field('hello')
    Field('hello',)
    >>> Field('hello<h>')
    Field('hello', ForeignKey(h))
    >>> Field('hello<h> ')
    Field('hello', ForeignKey(h), ' ')
    >>> Field('hello<h>. world <o>')
    Field('hello', ForeignKey(h), '. world ', ForeignKey(o))
    >>> Field('<h>')
    Field(ForeignKey(h),)
    >>> Field('')
    Field()

    The foreign keys embedded can be changed in-place. All foreign keys
    referencing the same primary key are in fact the same instance.

    >>> field = Field('hello<h>. world <o> again<o>')
    >>> str(field)
    'hello<h>. world <o> again<o>'
    >>> fkview = field.fkeys
    >>> fkview
    [ForeignKey(h), ForeignKey(o)]
    >>> fkview[1].refpk = 'ggg'
    >>> fkview
    [ForeignKey(h), ForeignKey(ggg)]
    >>> str(field)
    'hello<h>. world <ggg> again<ggg>'
    """

    def __init__(self, string: str):
        components = []
        occured_fks: typing.Dict[str, Fk] = {}
        matched = FK_PATTERN.search(string)
        while matched:
            beg, end = matched.span()
            if string[:beg]:
                components.append(string[:beg])
            refpk = matched.group(1)
            try:
                components.append(occured_fks[refpk])
            except KeyError:
                fk = Fk(refpk)
                components.append(fk)
                occured_fks[refpk] = fk
            string = string[end:]
            matched = FK_PATTERN.search(string)
        if string:
            components.append(string)
        self.components = tuple(components)

    def __str__(self):
        return ''.join(map(str, self.components))

    def __repr__(self):
        return ''.join(('Field', repr(self.components)))

    def __eq__(self, other):
        if not isinstance(other, Sentence):
            return NotImplemented
        return str(self) == str(other)

    def __len__(self):
        return len(str(self))

    def __iter__(self):
        return iter(str(self))

    def __lt__(self, other):
        return NotImplemented

    @property
    def fkeys(self) -> typing.FrozenSet[Fk]:
        """
        Gives a **view** (so not a copy) of all different foreign keys.
        """
        fks = []
        for x in self.components:
            if isinstance(x, Fk) and x not in fks:
                fks.append(x)
        return fks


class RecordRow:
    """
    A list of length at least 1. The first element is a string primary key,
    and the rest elements are ``Field`` instances that may contain
    one or more ``Fk`` components.

    >>> RecordRow(' ')
    (' ',)
    >>> str(RecordRow(' '))
    ' '
    >>> RecordRow('mm, hello<h>. world <o> ,again')
    ('mm', Field(' hello', ForeignKey(h), '. world ', ForeignKey(o), ' '), Field('again',))
    >>> str(RecordRow('mm, hello<h>. world <o> ,again'))
    'mm, hello<h>. world <o> ,again'
    """

    def __init__(self, row: str):
        assert row, str(row)
        raw_fields = row.split(FIELD_DELIMITER)
        fields = [raw_fields[0]]
        fields.extend(map(Field, raw_fields[1:]))
        self.fields = tuple(fields)

    @property
    def key(self):
        return self.fields[0]

    @key.setter
    def key(self, value: str):
        if not value:
            raise ValueError('primary key must be non-empty')
        new_fields = [value]
        new_fields.extend(self.fields[1:])
        self.fields = tuple(new_fields)

    def __repr__(self):
        return repr(self.fields)

    def __str__(self):
        return FIELD_DELIMITER.join(map(str, self.fields))

    def __len__(self):
        return len(self.fields)

    def __getitem__(self, index):
        return self.fields[index]

    def __iter__(self):
        return iter(self.fields)

    def __bool__(self):
        return bool(self.fields)

    def __hash__(self):
        return hash(self.fields[0])

    def __eq__(self, other):
        if not isinstance(other, RecordRow):
            return NotImplemented
        if len(self) != len(other):
            return NotImplemented
        return tuple((f == g) for f, g in zip(self, other))

    def __lt__(self, other):
        return NotImplemented


class ExprRecord:
    def __init__(self, filename: str):
        self.header: typing.List[str]
        rows: typing.List[RecordRow] = []
        uids: typing.Set[str] = set()
        bl = 1  # base lineno
        with open(filename) as infile:
            lines = filter(None, map(procline, infile))
            try:
                self.header = next(lines).split(FIELD_DELIMITER)
            except StopIteration:
                raise EmptyDocument
            for i, _r in enumerate(map(RecordRow, lines)):
                if len(_r) != len(self.header):
                    raise InvalidDocumentError(
                        msg=('expecting NF={} but got {}'
                             .format(len(self.header), len(_r))),
                        lineno=bl + i)
                assert _r.key, str(_r)
                if _r.key in uids:
                    raise BadPrimaryKeyError(pk=fields[0], lineno=bl + i)
                uids.add(_r.key)
                rows.append(_r)

        for _r in rows:
            for _f in _r[1:]:
                for _k in _f.fkeys:
                    if _k.refpk not in uids:
                        raise BadForeignKeyError(fk=_k.refpk)

        self.rows = rows

    def __repr__(self):
        return ('{}(header={}, rows={})'
                .format(type(self).__name__,
                        self.header,
                        repr(self.rows)))

    def __str__(self):
        lines = [FIELD_DELIMITER.join(self.header)]
        lines.extend(map(str, self.rows))
        return ''.join(('\n'.join(lines), '\n'))

    def rename_pk(self, src: str, dst: str) -> None:
        """
        :raise KeyError: if primary key ``src`` is not found
        """
        pks = set(_r.key for _r in self.rows)
        for _r in self.rows:
            if _r.key == src:
                if dst != src:
                    if dst in pks:
                        raise ValueError('cannot rename to existing key {}'
                                         .format(dst))
                    _r.key = dst
                    for __r in self.rows:
                        for __f in __r[1:]:
                            for __k in __f.fkeys:
                                if __k.refpk == src:
                                    __k.refpk = dst
                break
        else:
            raise KeyError(src)
