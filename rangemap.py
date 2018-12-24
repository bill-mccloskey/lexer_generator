import string

class Range(object):
    # Represents [a, b). These are assumed to be integers.
    def __init__(self, a, b):
        self.start = a
        self.end = b

    def __str__(self):
        if self.end == self.start + 1 and self.start < 256 and self.start >= 0 and chr(self.start) in string.printable:
            return '"%s"' % chr(self.start)
        else:
            return '[%s,%s)' % (str(self.start), str(self.end))

    def __eq__(self, other):
        return (self.start, self.end) == (other.start, other.end)

    def contains(self, point):
        return point >= self.start and point < self.end

class RangeMap(object):
    def __init__(self):
        self.entries = []

    def __str__(self):
        r = []
        for (range, value) in self.entries:
            r.append('%s->%s' % (str(range), str(value)))
        return '[' + ', '.join(r) + ']'

    def set(self, range, value):
        if range.start < range.end:
            self.entries.append((range, value))

    def get_entries(self):
        return self.entries

    def lookup(self, point):
        for (r, value) in self.entries:
            if r.contains(point):
                return value

    def clone(self):
        r = RangeMap()
        r.entries = self.entries[:]
        return r

    def add(self, other):
        self.entries += other.entries

    def canonicalize(self, min_value, max_value):
        result = RangeMap()
        result.set(Range(min_value, max_value), set())

        for (range, value) in self.entries:
            # Iterate over result. For each one that 'range' intersects, combine the two ranges into three and update the mapping.
            new_result = RangeMap()
            for (rrange, values) in result.entries:
                if rrange.start <= range.start and rrange.end >= range.end:
                    new_result.set(Range(rrange.start, range.start), values)
                    new_result.set(Range(range.start, range.end), values | set([value]))
                    new_result.set(Range(range.end, rrange.end), values)
                elif range.end > rrange.start and range.end <= rrange.end:
                    new_result.set(Range(rrange.start, range.end), values | set([value]))
                    new_result.set(Range(range.end, rrange.end), values)
                elif range.start >= rrange.start and range.start <= rrange.end:
                    new_result.set(Range(rrange.start, range.start), values)
                    new_result.set(Range(range.start, rrange.end), values | set([value]))
                else:
                    new_result.set(rrange, values)
            result = new_result

        return result

if __name__ == '__main__':
    r = RangeMap()
    r.set(Range(10, 20), 1)
    r.set(Range(15, 20), 2)
    r.set(Range(5, 15), 3)
    r.set(Range(21, 40), 4)
    r.set(Range(15, 20), 5)

    x = r.canonicalize(0, 50)
    print x
