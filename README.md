# pyconf

A Python DSL for generating JSON or Protobuf configuration


## Basic Idea

- Confiugration is pure data, that can be easily serialized to JSON or Protobuf.
- Pyconf is a Python-based DSL, which is also a valid Python program, running
  it results in configuration in pure data form.
- `Node` holds configuration data, node is immutable.
- If node holds dict data, it can be "extended" passing in passing key-value
  pairs, extension results in new node with copy of original data updated with
  key-value pairs.

## Syntax

Quite similar to [Bazel](https://bazel.io):

    # Basic configuration
    user = conf(
      name = 'yuheng',
      etc = conf(
        lang = 'en',
        editor = 'vi',
      ),
    )
    user.execute() # {'name': 'yuheng', 'etc': {'lang': 'en', 'editor': 'vi'}}

    # Invoking a node to extend it, note extension is shallow.
    ann = user(
      name = 'ann',
      home = '/local/home/ann',
      # user.etc returns a node containg data of 'etc' subfield
      etc = user.etc(
        editor = 'emacs',
      ),
    )
    ann.execute() # {'name': 'ann', 'home': '/local/home/ann' 'etc': {'lang': 'en', 'editor': 'emacs'}}

    # Mixin: extend by patching another node
    use_emacs = conf(editor = 'emacs')
    ann = user(
      name = 'ann',
      etc = (user.etc << use_emacs)(
        lang = 'fr',
      ),
    )

    # Appends to repeated field
    ls = conf(cmd = 'ls')
    ls_detailed = ls(flags =  conf.flags + ['-l'])

    # Ordered tuple is also useful, you can individually extend or replace node
    # in an ordered list
    layout = box(
      type = 'hflow',
      children = conf['title body action_button'](
        title = 'Hello',
      ),
    )
    my = layout(children = layout.children(body = 'World'))
    my.execute() # {'type': 'hflow', children: ['Hello', 'World', None]}

    # Load annother conf
    common = load('path/to/conf/common.pyconf')

# Extension

All valid Python code can be valid pyconf code (you can configure restricted
environment if you want). It quite easy to define something like:

    def my_complex_rule(name=None, deps=[], **kwargs):
      # Returns a Node

then use it like extending a normal node.

You can also define a post converter that converts node data when outputing,
ordered tupple introduced above uses this technique:

    def order_handler(order):
      return lambda meta, data: [data.get(k) for k in order]

    # conf['title body'] is a shortcut of
    conf('__post__': order_handler(['title', 'body']))

# API

See code.

You can tailor Python runtime to build a secure restricted environment for just the configuration stuff. Do note that there's no such thing as secured sandbox in Python, use a container solution instead.
