## Usage
### Classes & decorators
<!-- TODO: put documentation about UsageExecNode -->
In [Tawazi](https://pypi.org/project/tawazi/), there 3 Classes that will be maniuplated by the user:

1. `ExecNode`: a wrapper around a function. `ExecNode` can be executed inside a `DAG`. `ExecNode` can take arguments and return values to be used as arguments in other `ExecNode`s.
2. `DAG`: a wrapper around a function that defines a dag dependency. This function should only contain calls to `ExecNode`s (you can not call normal Python functions inside a `DAG`!)
3. `DAGExecution`: an instance related to `DAG` for advanced usage. It can execute a `DAG` and keeps information about the last execution. It allows checking all `ExecNode`s results, running subgraphs, caching `DAG` executions and more (c.f. section below for usage documentation).

Decorators are provided to create the previous classes:

1. `@xn`: creates `ExecNode` from a function.
2. `@dag`: creates `DAG` from a function.

### basic usage
```python
from tawazi import xn, dag
@xn
def incr(x):
  return x + 1

# incr is no longer a function
# incr became a `LazyExecNode` which is a subclass of `ExecNode`.
print(type(incr))

@xn
def decr(x):
  return x - 1

@xn
def display(x):
  print(x)

@dag
def pipeline(x):
  x_lo = decr(x)
  x_hi = incr(x)
  display(x_hi)
  display(x_lo)

# pipeline is no longer a function
# pipeline became a `DAG`
print(type(pipeline))

# `DAG` can be executed, they behave the same as the original function without decorators.
pipeline(0)
```


### Parallelism
You can use Tawazi to make your non CPU-Bound code Faster

<!--pytest-codeblocks:cont-->

```python
# type: ignore
from time import sleep, time

@xn
def a():
    print("Function 'a' is running", flush=True)
    sleep(1)
    return "A"

@xn
def b():
    print("Function 'b' is running", flush=True)
    sleep(1)
    return "B"

@xn
def c(a, b):
    print("Function 'c' is running", flush=True)
    print(f"Function 'c' received {a} from 'a' & {b} from 'b'", flush=True)
    return f"{a} + {b} = C"

@dag(max_concurrency=2)
def pipeline():
  res_a = a()
  res_b = b()
  res_c = c(res_a, res_b)
  return res_c

t0 = time()
# executing the dag takes a single line of code
res = pipeline()
execution_time = time() - t0
assert execution_time < 1.5  # a() and b() are executed in parallel
print(f"Graph execution took {execution_time:.2f} seconds")
print(f"res = {res}")

```
As you can see, the execution time of pipeline takes less than 2 seconds, which means that some part of the code ran in parallel to the other

### `DAG` is like a normal function

You can pass in arguments to the pipeline and get returned results back like normal functions:

<!--pytest-codeblocks:cont-->

```python
from tawazi import xn, dag
@xn
def xn1(i):
  return i+1

@xn
def xn2(i, j=1):
  return i + j + 1

@dag
def pipeline(i=0):
  res1 = xn1(i)
  res2 = xn2(res1)
  return res2

# run pipeline with default parameters
assert pipeline() == 3
# run pipeline with passed parameters
assert pipeline(1) == 4
```
Currently you can not pass in named parameters to the `DAG` (will be supported in future releases). (This should not be confused with passing keyworded arguments to `ExecNode`s which is possible)

You can return multiple values from a pipeline via tuples, lists or dicts.

<!--pytest-codeblocks:cont-->

```python
@dag
def pipeline_tuple():
  return xn1(1), xn2(1)

assert pipeline_tuple() == (2, 3)

@dag
def pipeline_list():
  return [xn1(1), xn2(2)]

assert pipeline_list() == [2, 4]

@dag
def pipeline_dict():
  return {"foo": xn1(1), "bar": xn2(3)}

assert pipeline_dict() == {"foo": 2, "bar": 5}
```

You can return multiple values from `ExecNode`s:

1. Either via Python `Tuple`s and `List`s but you will have to specify the unpacking number
<!--pytest-codeblocks:cont-->

```python
@xn(unpack_to=4)
def replicate_tuple(val):
  return (val, val + 1, val + 2, val + 3)


@xn(unpack_to=4)
def replicate_list(val):
  return [val, val + 1, val + 2, val + 3]


@dag
def pipeline():
  v1, v2, v3, v4 = replicate_tuple(1)
  v5, v6, v7, v8 = replicate_list(v4)
  return v1, v2, v3, v4, v5, v6, v7, v8


assert pipeline() == (1, 2, 3, 4, 4, 5, 6, 7)
```
2. Or via indexing (`Dict` or `List` etc.):
<!--pytest-codeblocks:cont-->

```python
@xn
def gen_dict(val):
  return {"k1": val, "k2": "2", "nested_list": [1 ,11, 3]}

@xn
def gen_list(val):
  return [val, val + 1, val + 2, val + 3]

@xn
def incr(val):
  return val + 1

@dag
def pipeline(val):
  d = gen_dict(val)
  l = gen_list(d["k1"])
  inc_val = incr(l[0])
  inc_val_2 = incr(d["nested_list"][1])
  return d, l, inc_val, inc_val_2

d, l, inc_val, inc_val_2 = pipeline(123)
assert d == {"k1": 123, "k2": "2", "nested_list": [1 ,11, 3]}
assert l == [123, 124, 125, 126]
assert inc_val == 124
assert inc_val_2 == 12
```
This makes the `DAG` usage as close to using the original __pipeline__ function as possible.

### Setup `ExecNode`s

Setup `ExecNode`s have their results cached in the `DAG` instance. This means that they run once per `DAG` instance. These can be used to load large constant data from Disk (Machine Learning Models, Large CSV files, initialization of a resource, prewarming etc.)

<!--pytest-codeblocks:cont-->

```python
LARGE_DATA = "Long algorithm to generate Constant Data"
@xn(setup=True)
def setop():
  global setop_counter
  setop_counter += 1
  return LARGE_DATA
@xn
def my_print(arg):
  print(arg)
  return arg

@dag
def pipeline():
  cst_data = setop()
  large_data = my_print(cst_data)
  return large_data

setop_counter = 0
# create another instance because setup ExecNode result is cached inside the instance
assert LARGE_DATA == pipeline()
assert setop_counter == 1
assert LARGE_DATA == pipeline()
assert setop_counter == 1 # setop_counter is skipped the second time pipe1 is invoked
```
if you want to re-run the setup `ExecNode`, you have to redeclare the `DAG` or deepcopy the original `DAG` instance before executing it.
<!--pytest-codeblocks:cont-->

```python
@dag
def pipeline():
  cst_data = setop()
  large_data = my_print(cst_data)
  return large_data

assert LARGE_DATA == pipeline()
assert setop_counter == 2
assert LARGE_DATA == pipeline()
assert setop_counter == 2
```
You can run the setup `ExecNode`s alone:
<!--pytest-codeblocks:cont-->

```python
@dag
def pipeline():
  cst_data = setop()
  large_data = my_print(cst_data)
  return large_data

pipeline.setup()
```
The goal of having setup `ExecNode` is to load only the necessary resources when a subgraph is executed. Here is an example demonstrating it:
<!--pytest-codeblocks:cont-->

```python
from pprint import PrettyPrinter
@xn(setup=True)
def setop1():
  return "large data 1"

@xn(setup=True)
def setop2():
  return "large data 2"

@xn
def print_xn(val):
  print(val)

@xn
def pprint_xn(val):
  PrettyPrinter(indent=4).pprint(val)

@dag
def pipeline():
  data1 = setop1()
  data2 = setop2()
  print_xn(data1)
  pprint_xn(data2)
  return data1, data2

exec_ = pipeline.executor(target_nodes=["print_xn"])
# Notice how the execution of the subgraph doesn't make the setop1 `ExecNode`. This makes development of your complex pipeline faster by reducing the time needed to load all resources
assert ("large data 1", None) == exec_()
```

### Debug `ExecNode`

You can Make Debug `ExecNode`s that will only run if `RUN_DEBUG_NODES` env variable is set. These can be visualization `ExecNode`s for example... or some complicated Assertions that helps you debug problems when needed that are hostile to the production environment (they consume too much computation time):
<!--pytest-codeblocks:cont-->

```python
@xn
def a(i):
  return i + 1

@xn(debug=True)
def print_debug(i):
  global debug_has_run
  debug_has_run = True
  print("DEBUG: ", i)

@dag
def pipe():
  i = a(0)
  print_debug(i)
  return i

debug_has_run = False
pipe()
assert debug_has_run == False
```

## Advanced Usage

### `DAGExecution`
`DAGExecution` is a class related to `DAG`. <!-- TODO: complete it-->


### Tag
you can tag an ExecNode  <!-- TODO:!!! continue when tag behavior are clearly defined for tuple and List! I prefer to use List for defining multiple tags because tuple can be used as dictionary key we can disallow using tuple for the moment ?-->
<!--pytest-codeblocks:cont-->

```python
@xn(tag="twinkle toes")
def a():
  print("I am tough")

@xn
def b():
  print("I am normal")

@dag
def pipeline():
  a()
  b()

pipeline()
xn_a, = pipeline.get_nodes_by_tag("twinkle toes")
```
You can do whatever you want with this ExecNode:

1. like checking its arguments
1. setting its priority
1. changing it to become a debug `ExecNode`

> **WARNING**: This is an advanced usage. Your methods might break more often with Tawazi releases because `ExecNode` is an internal Object. Please use with care}

You can have multiple `Tag`s for the same `ExecNode` and the same `Tag` for multiple `ExecNode`s:
<!--pytest-codeblocks:cont-->

```python
@xn(tag=("twinkle", "toes"))
def a():
    print("I am tough")
@xn(tag="twinkle")
def b():
    print("I am light")
@dag
def pipeline():
    a()
    b()

xn_a, xn_b = pipeline.get_nodes_by_tag("twinkle")
```

You can even tag a specific call of an ExecNode:
<!--pytest-codeblocks:cont-->

```python
@xn
def stub_xn(i):
  return i

@xn(tag="c_node")
def print_xn(i):
  print(i)

@dag
def pipeline():
  b()
  hello = stub_xn("hello")
  print_xn(hello)
  goodbye = stub_xn("goodbye")
  print_xn(goodbye, twz_tag="byebye")

pipeline()
# multiple nodes can have the same tag!
xns_bye = pipeline.get_nodes_by_tag("byebye")
```
> This will be useful if you want to run a subgraph (cf. the next paragraph). It will also be useful if you want to access result of a specific ExecNode after an Execution

You can run a subgraph of your pipeline: Make a `DAGExecution` from your `DAG` and pass in the `ExecNode`s you want to run: <!-- TODO: complete these two parts!!-->
<!--pytest-codeblocks:cont-->

```python
# You can use the original __qual__name of the decorated function as an Identifier
pipe_exec = pipeline.executor(target_nodes=["b"])
pipe_exec()
# You can use the tag of an ExecNode
pipe_exec = pipeline.executor(target_nodes=["c_node"])
pipe_exec()
# You can use the calling tag to distinguish the 1st call of g from the 2nd call!
pipe_exec = pipeline.executor(target_nodes=["byebye"])
pipe_exec()
# You can even pass in the ExecNodes to run and mix identifiers types
pipe_exec = pipeline.executor(target_nodes=["b", xns_bye[0]])
pipe_exec()

```
> Because `DAGExecution` instances are mutable, they are non thread-safe. This is unlike `DAG` which is ThreadSafe

More functionalities will be introduced in the future...


### Fine Control of Parallel Execution

1. You can control which node is preferred to run 1st when mutliple `ExecNode`s are available for execution. This can be achieved through modifications of `priority` of the `ExecNode`.
1. You can even make an `ExecNode` run alone (i.e. without allowing other ExecNodes to execute in parallel to it). This can be helpful if you write code that is not thread-safe or use a library that is not thread-safe in a certain `ExecNode`.
This is achieved by setting the `is_sequential` parameter to `True` for the `ExecNode` in question. The default value is set via the environment variable `TAWAZI_IS_SEQUENTIAL` (c.f. `tawazi.config`).
1. You can control the behavior of the `DAG` in case an `ExecNode` fails:
  a. `"strict"`: stop execution of the DAG
  b. `"all-children"`:  stop the execution of the all successors
  c. `"permissive"`: continue the execution of the whole DAG
<!--pytest-codeblocks:cont-->

```python

# type: ignore
from time import sleep, time
from tawazi import xn, dag

@xn
def a():
    print("Function 'a' is running", flush=True)
    sleep(1)
    return "A"

# optionally configure each ExecNode using the decorator:
# is_sequential = True to prevent ExecNode from running in parallel with other ExecNodes
# priority to choose the ExecNode in the next execution phase
@xn(is_sequential=True, priority=10)
def b():
    print("Function 'b' is running", flush=True)
    sleep(1)
    return "B"

@xn
def c(a, arg_b):
    print("Function 'c' is running", flush=True)
    print(f"Function 'c' received {a} from 'a' & {arg_b} from 'b'", flush=True)
    return f"{a} + {arg_b} = C"

# optionally customize the DAG
@dag(max_concurrency=2, behavior="strict")
def deps_describer():
  res_a = a()
  res_b = b()
  res_c = c(res_a, res_b)
  return res_a, res_b, res_c


t0 = time()
# the dag instance is reusable.
# This is recommended if you want to do the same computation multiple times
res_a, res_b, res_c = deps_describer()
execution_time = time() - t0
print(f"Graph execution took {execution_time:.2f} seconds")
assert res_a == "A"
assert res_b == "B"
assert res_c == "A + B = C"
```

## Limitations
Currently there are some limitations in the usage of tawazi that will be overcome in the future.

1. A DAG can not reuse the same function twice inside the calculation sequence (Will be resolved in the future)
2. All code inside a dag descriptor function must be either an @op decorated functions calls and arguments passed arguments. Otherwise the behavior of the DAG might be unpredictable
3. Because the main function serves only for the purpose of describing the dependencies, the code that it executes should only describe dependencies. Hence when debugging your code, it will be impossible to view the data movement inside this function. However, you can debug code inside of a node.