# soffit
A simple-to-use graph grammar engine

This project is inspired by Tracery, and seeks to provide a way to get
started with graph grammars that is nearly as easy.

## Online implementation

You can play with Soffit live at http://soffit.combinatorium.com or https://mgritter.github.io/soffit-web

The code for the front end is at [mgritter/soffit-web](https://github.com/mgritter/soffit-web); it uses an AWS Lambda backend to run
Soffit, and [d3-graphviz](https://github.com/magjac/d3-graphviz) to perform client-side rendering.

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
