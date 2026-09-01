# Copyright 2026 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


class PeekableIterator:
    """Wraps a generator to provide hasNext()/next() peek semantics."""

    def __init__(self, iterable):
        self._iter = iter(iterable)
        self._exhausted = False
        self._peeked = None
        self._advance()

    def _advance(self):
        try:
            self._peeked = next(self._iter)
        except StopIteration:
            self._exhausted = True

    def hasNext(self):
        return not self._exhausted

    def next(self):
        value = self._peeked
        self._advance()
        return value
