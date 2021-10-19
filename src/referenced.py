
# this class stores an attribute, provides getter
# and setter and invokes the member function 
# with the name (string) callback_name on every
# change of value
class CallOnSet:
    def __init__(self, callback_name):
        self.callback = callback_name

    def __set_name__(self, owner, name):
        self.name = "_cos_" + name

    def __get__(self, instance, owner=None):
        try:
            return instance.__dict__[self.name]
        except KeyError:
            raise AttributeError("Attribute {} not set".format(self.name[5:]))

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value
        type(instance).__getattribute__(instance, self.callback)()

    def __delete__(self, instance):
        del instance.__dict__[self.name]

# represents a descriptor with an instance
# and gets/sets this descriptor
class ReferencedDescriptor:
    def __init__(self, descriptor, instance):
        self.descriptor = descriptor
        self.instance = instance

    def get(self):
        return self.descriptor.__get__(self.instance, type(self.instance))

    def set(self, v):
        self.descriptor.__set__(self.instance, v)

class ReferencedProperty:
    def __init__(self, prop, instance):
        self._descriptor = ReferencedDescriptor(prop, instance)

    def __get__(self, instance, owner=None):
        return self._descriptor.get()

    def __set__(self, instance, v):
        self._descriptor.set(v)
