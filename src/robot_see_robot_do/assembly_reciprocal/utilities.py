from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import json
import compas

try:
    basestring
except NameError:
    basestring = str


__all__ = [
    'FromToData',
    'FromToJson',
    'FromToPickle',
]


class FromToData(object):

    __module__ = 'assembly_information_model.assembly.utilities'

    @classmethod
    def from_data(cls, data):
        """Construct a datastructure from structured data.

        Parameters
        ----------
        data : dict
            The data dictionary.

        Returns
        -------
        object
            An object of the type of ``cls``.

        Note
        ----
        This constructor method is meant to be used in conjuction with the
        corresponding *to_data* method.

        """
        graph = cls()
        graph.data = data
        return graph

    def to_data(self):
        """Returns a dictionary of structured data representing the data structure.

        Returns
        -------
        dict
            The structured data.

        Note
        ----
        This method produces the data that can be used in conjuction with the
        corresponding *from_data* class method.

        """
        return self.data


class FromToJson(object):

    __module__ = 'compas.datastructures._mixins'

    @classmethod
    def from_json(cls, filepath):
        """Construct a datastructure from structured data contained in a json file.

        Parameters
        ----------
        filepath : str
            The path to the json file.

        Returns
        -------
        object
            An object of the type of ``cls``.

        Note
        ----
        This constructor method is meant to be used in conjuction with the
        corresponding *to_json* method.

        """
        with open(filepath, 'r') as fp:
            data = json.load(fp)
        graph = cls()
        graph.data = data
        return graph

    def to_json(self, filepath, pretty=False):
        """Serialise the structured data representing the data structure to json.

        Parameters
        ----------
        filepath : str
            The path to the json file.

        """
        with open(filepath, 'w+') as fp:
            if pretty:
                #json.dump(self.data, fp, sort_keys=True, indent=4) # old
                compas.json_dump(self.data, fp, pretty=True)
            else:
                #json.dump(self.data, fp) # old:
                compas.json_dump(self.data, fp)



class FromToPickle(object):

    __module__ = 'compas.datastructures._mixins'

    @classmethod
    def from_pickle(cls, filepath):
        """Construct a datastructure from serialised data contained in a pickle file.

        Parameters
        ----------
        filepath : str
            The path to the pickle file.

        Returns
        -------
        object
            An object of type ``cls``.

        Note
        ----
        This constructor method is meant to be used in conjuction with the
        corresponding *to_pickle* method.

        """
        o = cls()
        o.load(filepath)
        return o

    def to_pickle(self, filepath):
        """Serialised the structured data representing the data structure to a pickle file.

        Parameters
        ----------
        filepath : str
            The path to the pickle file.

        """
        self.dump(filepath)


def _serialize_to_data(obj):
    return dict(
        dtype='{}/{}'.format(obj.__class__.__module__, obj.__class__.__name__),
        data=obj.to_data()
    )


def _deserialize_from_data(data):
    module, attr = data['dtype'].split('/')
    cls = globals().get(attr)

    if cls is None:
        cls = getattr(__import__(module, fromlist=[attr]), attr)

    return cls.from_data(data['data'])


# ==============================================================================
# Main
# ==============================================================================
if __name__ == "__main__":
    pass
