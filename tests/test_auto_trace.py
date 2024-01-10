import ast
import asyncio
import sys
from importlib.machinery import SourceFileLoader

import pytest
from dirty_equals import IsJson

from logfire import AutoTraceModule, install_auto_tracing
from logfire._auto_trace import LogfireFinder
from logfire._auto_trace.import_hook import LogfireLoader
from logfire._auto_trace.rewrite_ast import rewrite_ast
from logfire.testing import TestExporter


def test_auto_trace_sample(exporter: TestExporter) -> None:
    meta_path = sys.meta_path.copy()

    install_auto_tracing('tests.auto_trace_samples')
    # Check that having multiple LogfireFinders doesn't break things
    install_auto_tracing('tests.blablabla')

    assert sys.meta_path[2:] == meta_path
    finder = sys.meta_path[1]
    assert isinstance(finder, LogfireFinder)

    assert finder.modules_filter(AutoTraceModule('tests.auto_trace_samples', '<filename>'))
    assert finder.modules_filter(AutoTraceModule('tests.auto_trace_samples.foo', '<filename>'))
    assert finder.modules_filter(AutoTraceModule('tests.auto_trace_samples.bar.baz', '<filename>'))
    assert not finder.modules_filter(AutoTraceModule('tests', '<filename>'))
    assert not finder.modules_filter(AutoTraceModule('tests_auto_trace_samples', '<filename>'))
    assert not finder.modules_filter(AutoTraceModule('tests.auto_trace_samples_foo', '<filename>'))

    from tests.auto_trace_samples import foo

    loader = foo.__loader__
    assert isinstance(loader, LogfireLoader)
    # The exact plain loader here isn't that essential.
    assert isinstance(loader.plain_spec.loader, SourceFileLoader)
    assert loader.plain_spec.name == foo.__name__ == foo.__spec__.name == 'tests.auto_trace_samples.foo'

    with pytest.raises(IndexError):  # foo.bar intentionally raises an error to test that it's recorded below
        asyncio.run(foo.bar())

    # insert_assert(exporter.exported_spans_as_dict(_include_pending_spans=True))
    assert exporter.exported_spans_as_dict(_include_pending_spans=True) == [
        {
            'name': 'Calling tests.auto_trace_samples.foo.bar (pending)',
            'context': {'trace_id': 1, 'span_id': 2, 'is_remote': False},
            'parent': {'trace_id': 1, 'span_id': 1, 'is_remote': False},
            'start_time': 1000000000,
            'end_time': 1000000000,
            'attributes': {
                'code.filepath': 'foo.py',
                'code.lineno': 123,
                'code.function': 'bar',
                'logfire.msg_template': 'Calling tests.auto_trace_samples.foo.bar',
                'logfire.msg': 'Calling tests.auto_trace_samples.foo.bar',
                'logfire.span_type': 'pending_span',
                'logfire.pending_parent_id': '0000000000000000',
            },
        },
        {
            'name': 'Calling tests.auto_trace_samples.foo.async_gen (pending)',
            'context': {'trace_id': 1, 'span_id': 4, 'is_remote': False},
            'parent': {'trace_id': 1, 'span_id': 3, 'is_remote': False},
            'start_time': 2000000000,
            'end_time': 2000000000,
            'attributes': {
                'code.filepath': 'foo.py',
                'code.lineno': 123,
                'code.function': 'async_gen',
                'logfire.msg_template': 'Calling tests.auto_trace_samples.foo.async_gen',
                'logfire.msg': 'Calling tests.auto_trace_samples.foo.async_gen',
                'logfire.span_type': 'pending_span',
                'logfire.pending_parent_id': '0000000000000001',
            },
        },
        {
            'name': 'Calling tests.auto_trace_samples.foo.gen (pending)',
            'context': {'trace_id': 1, 'span_id': 6, 'is_remote': False},
            'parent': {'trace_id': 1, 'span_id': 5, 'is_remote': False},
            'start_time': 3000000000,
            'end_time': 3000000000,
            'attributes': {
                'code.filepath': 'foo.py',
                'code.lineno': 123,
                'code.function': 'gen',
                'logfire.msg_template': 'Calling tests.auto_trace_samples.foo.gen',
                'logfire.msg': 'Calling tests.auto_trace_samples.foo.gen',
                'logfire.span_type': 'pending_span',
                'logfire.pending_parent_id': '0000000000000003',
            },
        },
        {
            'name': 'Calling tests.auto_trace_samples.foo.gen',
            'context': {'trace_id': 1, 'span_id': 5, 'is_remote': False},
            'parent': {'trace_id': 1, 'span_id': 3, 'is_remote': False},
            'start_time': 3000000000,
            'end_time': 4000000000,
            'attributes': {
                'code.filepath': 'foo.py',
                'code.lineno': 123,
                'code.function': 'gen',
                'logfire.msg_template': 'Calling tests.auto_trace_samples.foo.gen',
                'logfire.span_type': 'span',
                'logfire.msg': 'Calling tests.auto_trace_samples.foo.gen',
            },
        },
        {
            'name': 'Calling tests.auto_trace_samples.foo.async_gen',
            'context': {'trace_id': 1, 'span_id': 3, 'is_remote': False},
            'parent': {'trace_id': 1, 'span_id': 1, 'is_remote': False},
            'start_time': 2000000000,
            'end_time': 5000000000,
            'attributes': {
                'code.filepath': 'foo.py',
                'code.lineno': 123,
                'code.function': 'async_gen',
                'logfire.msg_template': 'Calling tests.auto_trace_samples.foo.async_gen',
                'logfire.span_type': 'span',
                'logfire.msg': 'Calling tests.auto_trace_samples.foo.async_gen',
            },
        },
        {
            'name': 'Calling tests.auto_trace_samples.foo.bar',
            'context': {'trace_id': 1, 'span_id': 1, 'is_remote': False},
            'parent': None,
            'start_time': 1000000000,
            'end_time': 7000000000,
            'attributes': {
                'code.filepath': 'foo.py',
                'code.lineno': 123,
                'code.function': 'bar',
                'logfire.msg_template': 'Calling tests.auto_trace_samples.foo.bar',
                'logfire.span_type': 'span',
                'logfire.msg': 'Calling tests.auto_trace_samples.foo.bar',
            },
            'events': [
                {
                    'name': 'exception',
                    'timestamp': 6000000000,
                    'attributes': {
                        'exception.type': 'IndexError',
                        'exception.message': 'list index out of range',
                        'exception.stacktrace': 'IndexError: list index out of range',
                        'exception.escaped': 'True',
                        'exception.logfire.trace': IsJson(
                            stacks=[
                                {
                                    'exc_type': 'IndexError',
                                    'exc_value': 'list index out of range',
                                    'syntax_error': None,
                                    'is_cause': False,
                                    'frames': [
                                        {
                                            'filename': 'foo.py',
                                            'lineno': 123,
                                            'name': 'bar',
                                            'line': '',
                                            'locals': None,
                                        }
                                    ],
                                }
                            ]
                        ),
                    },
                }
            ],
        },
    ]


def test_default_modules() -> None:
    # Test the default module filter argument of install_auto_tracing.
    # This should match anything in the `tests` package, so remove the finder at the end of the test.
    meta_path = sys.meta_path.copy()
    install_auto_tracing()
    assert sys.meta_path[1:] == meta_path
    finder = sys.meta_path[0]

    try:
        assert isinstance(finder, LogfireFinder)
        assert finder.modules_filter(AutoTraceModule('tests', '<filename>'))
        assert finder.modules_filter(AutoTraceModule('tests.foo', '<filename>'))
        assert finder.modules_filter(AutoTraceModule('tests.bar.baz', '<filename>'))
        assert not finder.modules_filter(AutoTraceModule('test', '<filename>'))
        assert not finder.modules_filter(AutoTraceModule('tests_foo', '<filename>'))
        assert not finder.modules_filter(AutoTraceModule('foo.bar.baz', '<filename>'))
    finally:
        assert sys.meta_path.pop(0) == finder
        assert sys.meta_path == meta_path


# language=Python
nested_sample = """
def func():
    x = 1

    class Class:
        x = 2

        def method(self):
            y = 3
            return y

        async def method2(self):
            class Class2:
                z = 4

                async def method3(self):
                    a = 5
                    return a
            return Class2().method3()

    return (x, Class)

class Class3:
    x = 6

    def method4(self):
        b = 7
        return b
"""


def test_rewrite_ast():
    tree = rewrite_ast(nested_sample, 'logfire_span', 'module.name')
    result = """
def func():
    with logfire_span('Calling module.name.func'):
        x = 1

        class Class:
            x = 2

            def method(self):
                with logfire_span('Calling module.name.func.<locals>.Class.method'):
                    y = 3
                    return y

            async def method2(self):
                with logfire_span('Calling module.name.func.<locals>.Class.method2'):

                    class Class2:
                        z = 4

                        async def method3(self):
                            with logfire_span('Calling module.name.func.<locals>.Class.method2.<locals>.Class2.method3'):
                                a = 5
                                return a
                    return Class2().method3()
        return (x, Class)

class Class3:
    x = 6

    def method4(self):
        with logfire_span('Calling module.name.Class3.method4'):
            b = 7
            return b
"""

    if sys.version_info >= (3, 9):
        assert ast.unparse(tree).strip() == result.strip()

    # Python 3.8 doesn't have ast.unparse, and testing that the AST is equivalent is a bit tricky.
    assert (
        compile(tree, '<filename>', 'exec').co_code == compile(result, '<filename>', 'exec').co_code
        or ast.dump(tree, annotate_fields=False) == ast.dump(ast.parse(result), annotate_fields=False)
        or ast.dump(tree) == ast.dump(ast.parse(result))
    )


def test_parts_start_with():
    for mod in [
        'foo',
        'foo.spam',
        'bar',
        'bar.spam',
        'xxx',
        'xxx.spam',
    ]:
        assert AutoTraceModule(mod, None).parts_start_with(['foo', 'bar', 'x+'])

    for mod in [
        'spam',
        'spam.foo',
        'spam.bar',
        'spam.bar.foo',
        'spam.foo.bar',
        'spam.xxx',
    ]:
        assert not AutoTraceModule(mod, None).parts_start_with(['foo', 'bar', 'x+'])
