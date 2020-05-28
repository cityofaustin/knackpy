from collections.abc import MutableMapping
import warnings

from knackpy._fields import Field


class Record:
    def __repr__(self):
        separator = f" <Record [{self.index}]"
        fields = f"".join(f"\n\t{str(field)}" for field in self.fields)
        return f"\n{separator}{fields}\n>"

    def __init__(self, data, field_defs, index=None):
        self.index = index
        self.field_defs = field_defs
        self.fields = self._handle_data(data)

    def _handle_data(self, data):
        raw_keys = [key for key in data.keys() if "raw" in key]

        fields = []

        for key, value in data.items():

            if f"{key}_raw" in raw_keys:
                # skip a key that also has a raw key
                continue

            # proxy the raw key as the key
            key = key.replace("_raw", "")

            try:
                field_def = self.field_defs[key]
            except KeyError:
                continue
            fields.append(Field(field_def, value))

        return fields


class RecordCollection(MutableMapping):
    """
    A dict-like container for `Records`. Allows client to get record list by the Knack key
    or the Knack name of the object.

    We need to use MutableMapping, rather than just subclassing dict, if we want to override
    the `get` method.

    See: https://stackoverflow.com/questions/21361106/how-would-i-implement-a-dict-with-abstract-base-classes-in-python
    """

    def __init__(self, *args, **kwargs):
        """Use the object dict"""
        self.__dict__.update(*args, **kwargs)

    # required by ABC
    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        """
        Here's where we override default dict behavior. On accessing the dict via `get` or `[]`, the key
        is checked against our lookup for any matching knack object or view keys.
        """
        try:
            knack_key = self.lookup[key]
            return self.__dict__[knack_key]

        except AttributeError:
            # key not found, so will try returing the key from the class dict and let it
            # raise an error
            warnings.warn(
                "Warning: key lookup has not been intiatiated. Pass key props to `.generate_key_lookup()`"
            )
            return self.__dict__[key]

        except KeyError:
            raise KeyError(f"Invalid object or view key: {key}. No records found.")

        return None

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    # The final two methods aren't required, but nice for demo purposes:
    def __str__(self):
        """returns simple dict representation of the mapping"""
        return str(self.__dict__)

    def __repr__(self):
        """echoes class, id, & reproducible representation in the REPL"""
        return "{}, D({})".format(super(D, self).__repr__(), self.__dict__)
