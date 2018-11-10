# soffit
A simple-to-use graph grammar engine

This project is inspired by Tracery, and seeks to provide a way to get
started with graph grammars that is nearly as easy.

## Getting started

Tutorial coming soon.

Currently you must have graphviz installed.  On Ubuntu:

```
apt-get install graphviz graphviz-dev
```

To run Soffit: clone or download, and run

```
pipenv sync
pipenv shell
```

to get the dependent packages, then run

```
python -m soffit.application doc/examples/tree.json --output tree.svg --iterations 100
```

## Documentation ##

  * [The graph grammar format](doc/InputFormat.md)
  * [Rule semantics](doc/RuleSemantics.md)
  * [Examples](doc/examples).
