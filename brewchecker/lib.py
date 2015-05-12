# coding: utf-8
from pip._vendor.distlib.compat import OrderedDict


# http://stackoverflow.com/questions/27912308/how-can-you-slice-with-string-keys-instead-of-integers-on-a-python-ordereddict
def _key_slice_to_index_slice(items, key_slice):
    try:
        if key_slice.start is None:
            start = None
        else:
            start = next(idx for idx, (key, value) in enumerate(items)
                         if key == key_slice.start)
        if key_slice.stop is None:
            stop = None
        else:
            stop = next(idx for idx, (key, value) in enumerate(items)
                        if key == key_slice.stop)
    except StopIteration:
        raise KeyError
    return slice(start, stop, key_slice.step)


class SlicableDict(OrderedDict):
    def __getitem__(self, key):
        if isinstance(key, slice):
            items = self.items()
            index_slice = _key_slice_to_index_slice(items, key)
            return SlicableDict(items[index_slice])
        return super(SlicableDict, self).__getitem__(key)

    def __setitem__(self, key, value, *args, **kwargs):
        if isinstance(key, slice):
            items = self.items()
            index_slice = _key_slice_to_index_slice(items, key)
            items[index_slice] = value.items()
            self.clear()
            self.update(items)
            return
        return super(SlicableDict, self).__setitem__(key, value, *args, **kwargs)

    def __delitem__(self, key, *args, **kwargs):
        if isinstance(key, slice):
            items = self.items()
            index_slice = _key_slice_to_index_slice(items, key)
            del items[index_slice]
            self.clear()
            self.update(items)
            return
        return super(SlicableDict, self).__delitem__(key, *args, **kwargs)
