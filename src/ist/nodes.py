# encoding: utf-8
# author:   Jan Hybs
from ist.globals import Globals
from ist.utils.utils import Field, TypedList


class ISTNode (object):
    _fields = []

    def parse (self, o={ }):
        for field in self._fields:
            # parse list
            if issubclass (field.type, TypedList):
                value = field.value.copy ().parse (o.get (field.name, []))
            # parse more complex objects
            elif issubclass (field.type, ISTNode):
                value = field.value.copy ().parse (o.get (field.name, { }))
            # simple values
            else:
                value = o.get (field.name)

            # create attribute on class instance
            self.__setattr__ (field.name, value)
            if field.name == 'id' and value is not None:
                Globals.items[value] = self

        return self

    def include_in_format (self):
        return True

    def get (self, *args):
        for arg in args:
            value = getattr (self, arg, None)
            if value is not None:
                return value

        raise Exception ('no valid attribute within {} found on {}'.format (args, self.__class__.__name__))


    def copy (self):
        '''
        Return copy of this instance
        :return:
        '''
        return self.__class__ ()

    def __repr__ (self):
        return '<{self.__class__.__name__} {self._fields}>'.format (self=self)


class Reference (ISTNode):
    def parse (self, o=''):
        self.ref_id = o
        return self

    def get_reference (self):
        return Globals.items.get (str (self.ref_id), None)

    def copy (self):
        return Reference ()

    def __repr__ (self):
        return "<Reference ({self.ref_id}) -> {ref}>".format (self=self, ref=self.get_reference ())

    def __nonzero__ (self):
        return self.get_reference () is not None


class NumberRange (ISTNode):
    def __init__ (self, always_visible=True):
        super (NumberRange, self).__init__ ()
        self.min = self.max = ''
        self.always_visible = always_visible

    replacements = {
        '2147483647': '',
        '4294967295': '',
        '-2147483647': '',
        '1.79769e+308': '',
        '-1.79769e+308': '',
        '': 'unknown range'
    }


    def parse (self, o=[]):
        self.min = o[0] if len (o) > 0 else ''
        self.max = o[1] if len (o) > 1 else ''

        return self

    def is_pointless (self):
        '''
        Wheather is information within this instance beneficial
        '''
        return self._format () in ('[0, ]', '[, ]')

    def _format (self):
        '''
        Method will will return string representation of this instance
        :return:
        '''
        return '[{}, {}]'.format (
            self.replacements.get (str (self.min), self.min),
            self.replacements.get (str (self.max), self.max)
        )

    def copy (self):
        return NumberRange (self.always_visible)

    def __repr__ (self):
        '''
        method will return string representation if is meaningful or flag always visible
        is True
        :return:
        '''
        return self._format () if self.always_visible or not self.is_pointless () else ''


class DoubleRange (NumberRange):
    def __init__ (self, always_visible=False):
        super (DoubleRange, self).__init__ (always_visible)

    def is_pointless (self):
        return self._format () == '[, ]'

    def copy (self):
        return DoubleRange (self.always_visible)


class AbstractNode (ISTNode):
    _fields = ISTNode._fields + [
        Field ('id'),
        Field ('input_type')
    ]


class DescriptionNode (AbstractNode):
    _fields = AbstractNode._fields + [
        Field ('description')
    ]


class RecordKeyDefault (AbstractNode):
    _fields = AbstractNode._fields + [
        Field ('type'),
        Field ('value')
    ]


class RecordKey (DescriptionNode):
    _fields = DescriptionNode._fields + [
        Field ('key'),
        Field ('type', Reference ()),
        Field ('default', RecordKeyDefault ())
    ]

    def include_in_format (self):
        return self.key.find ('TYPE') == -1


class Record (DescriptionNode):
    _fields = DescriptionNode._fields + [
        Field ('type_name'),
        Field ('input_type'),
        Field ('type_full_name'),
        Field ('keys', TypedList (RecordKey)),
        Field ('implements', TypedList (Reference)),
        Field ('reducible_to_key')
    ]


class AbstractRecord (Record):
    _fields = Record._fields + [
        Field ('implementations', TypedList (Reference)),
        Field ('default_descendant', Reference ()),
        Field ('full_name'),
        Field ('name')
    ]


class SelectionValue (DescriptionNode):
    _fields = DescriptionNode._fields + [
        Field ('name')
    ]


class Selection (DescriptionNode):
    _fields = DescriptionNode._fields + [
        Field ('values', TypedList (SelectionValue)),
        Field ('name'),
        Field ('full_name')
    ]

    def include_in_format (self):
        return self.name.find ('TYPE') == -1


class String (AbstractNode):
    _fields = AbstractNode._fields + [
        Field ('name'),
        Field ('full_name')
    ]


class Double (AbstractNode):
    _fields = AbstractNode._fields + [
        Field ('name'),
        Field ('full_name'),
        Field ('range', DoubleRange ())
    ]


class Integer (AbstractNode):
    _fields = AbstractNode._fields + [
        Field ('name'),
        Field ('full_name'),
        Field ('range', NumberRange ())
    ]


class FileName (AbstractNode):
    _fields = AbstractNode._fields + [
        Field ('name'),
        Field ('full_name'),
        Field ('file_mode')
    ]


class Bool (AbstractNode):
    _fields = AbstractNode._fields + [
        Field ('name'),
        Field ('full_name')
    ]


class Array (AbstractNode):
    _fields = AbstractNode._fields + [
        Field ('range', NumberRange (False)),
        Field ('subtype', Reference ())
    ]


# all acceptable input_type
registered_nodes = {
    'Record': Record,
    'AbstractRecord': AbstractRecord,
    'Selection': Selection,
    'String': String,
    'Double': Double,
    'Integer': Integer,
    'FileName': FileName,
    'Bool': Bool,
    'Array': Array
}
