"""
Pyconf DSL for generating JSON or Protobuf configuration.
"""

class Node(object):
  def __init__(self, value):
    self._value = value

  def execute(self):
    def _unwrap(item):
      if isinstance(item, Node):
        return item.execute()
      else:
        return item

    if isinstance(self._value, dict):
      meta = {}
      data = {}
      for k, v in self._value.iteritems():
        if k.startswith('__') and k.endswith('__'):
          meta[k] = v
        else:
          data[k] = _unwrap(v)
      if '__post__' in meta:
        return meta['__post__'](meta, data)
      else:
        return data
    elif isinstance(self._value, (list, tuple)):
      return map(_unwrap, self._value)
    else:
      return self._value

  def __call__(self, **kwargs):
    output = {}
    if self._value is not None:
      if not isinstance(self._value, dict):
        raise TypeError('Cannot extend non-dict node %s' % (type(self._value),))
      output.update(self._value)
    for k, v in kwargs.iteritems():
      output[k] = v
    return Node(output)

  def __getattr__(self, attr):
    if attr.startswith('_'):
      raise AttributeError('Private or meta attr %s' % (attr,))
    if self._value is None:
      return self
    if not isinstance(self._value, dict):
      raise TypeError('Cannot get attr of non-dict node %s' % (type(self._value),))
    output = self._value.get(attr)
    if not isinstance(output, Node):
      output = Node(output)
    return output

  def __getitem__(self, fn):
    if callable(fn):
      return self(__post__ = fn)
    order = fn
    if isinstance(order, (str, unicode)):
      order = order.strip().split()
    return self(__post__ = lambda meta, value: [value.get(key) for key in order])

  def __add__(self, ls):
    if isinstance(ls, Node):
      ls = ls._value
    if not isinstance(ls, (list, tuple)):
      raise TypeError('Cannot append node with non-array data %s' % (type(ls),))
    orig = self._value
    if orig is None:
      orig = ()
    if not isinstance(orig, (list, tuple)):
      raise TypeError('Cannot append non-array node %s' % (type(self._value),))
    return Node(tuple(orig) + tuple(ls))

  def __lshift__(self, right):
    if isinstance(right, Node):
      right = right._value
    if not isinstance(right, dict):
      raise TypeError('Cannot extend node with non-dict data %s' % (type(right),))
    return self(**right)

  def __rlshift__(self, left):
    right = self._value
    if right is None:
      right = {}
    if not isinstance(right, dict):
      raise TypeError('Cannot extend node with non-dict data %s' % (type(right),))
    return left(**right)

conf = Node(None)

def array(*args):
  return Node(args)

def run(path, builtins=None):
  import imp
  import runpy
  import os.path
  conf_builtins = {
    'conf': conf,
    'array': array,
  }
  if builtins is not None:
    conf_builtins.update(builtins)

  def conf_load(dirty_path):
    path = os.path.normpath(dirty_path)
    if path.startswith('.') or path.startswith('/'):
      raise ValueError('Invalid conf_load path %s' % (dirty_path,))
    result_dict = runpy.run_path(path, init_globals=conf_builtins)
    mod = imp.new_module(path)
    for k, v in result_dict.iteritems():
      if k.startswith('_'):
        continue
      setattr(mod, k, v)
    return mod
  conf_builtins['load'] = conf_load

  result = runpy.run_path(path, init_globals=conf_builtins)
  output = {}
  for k, v in result.iteritems():
    if isinstance(v, Node):
      output[k] = v.execute()
  return output

if __name__ == '__main__':
  import json
  import sys
  ret = run(sys.argv[1])['CONFIG']
  print json.dumps(ret)
