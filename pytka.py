#!/usr/bin/env python3
#
#  Unit tests are frowned upon.
#  Here we try to maximise coverage
#  by using only end-to-end test
#  with most tricky inputs.
#
import sys
import pytest
from collections import OrderedDict

import action


@pytest.fixture
def vc():
    """ Dummy command with `verbose` and `count`
        arguments with correctly parsed signature
    """
    def vc(*, verbose, count):
        pass
    vc.arguments = OrderedDict([])
    vc.options = {
        'verbose': action.Count(short='v'),
        'count': action.Flag(short='c', type=int)
    }
    return vc


@pytest.fixture
def ctx():
    """ A fresh context to start clean
    """
    return action.context()


def test_options_parsing(vc):
    """ Known options should map to function arguments,
        unknown options should stay as the leftover
    """
    argv = [
        '-vvv',
        '-vv',
        '-v',  # all vees should be consumed by Verbose
        '-t',  # tee is unknown, and should be counted as such
        'install', 'package'  # these are also unknowns
    ]
    assert(
        action._parse_options(vc, argv) ==
        ({'verbose': 6}, ['-t', 'install', 'package'])
    )


def test_original_functions_stay_unchanged(ctx):
    """ Functions passed to the decorator
        should not acquire new attributes
    """
    def act(x, y, z):
        pass
    original_repr = repr(act)
    ctx.__call__(act)  # no capture

    assert(repr(act) == original_repr)
    assert(not hasattr(act, 'options'))
    assert(not hasattr(act, 'arguments'))
    assert(not hasattr(act, 'is_variadic'))


def test_signature_derivation_from_unannotated(ctx):
    """ Function with bare argument
        should map to eponymous action
        with `str` arguments of the same count
    """
    DefaultType = str

    def install(x, y, z):
        pass
    install = ctx.__call__(install)

    assert(
        install.arguments ==
        OrderedDict([
            ('x', DefaultType),
            ('y', DefaultType),
            ('z', DefaultType),
        ])
    )


def test_signature_derivation_from_kw_only(ctx):
    """ After splat there come options
    """
    def list(*, recur, verbose):
        pass
    list = ctx.__call__(list)

    assert(
        set(list.options) == {'recur', 'verbose'}
    )


def test_action_name_derivation(ctx):
    """ After invoking a decorator on a function,
        Action context should obtain an action
        of the same name
    """
    def yeah():
        pass
    yeah = ctx.__call__(yeah)

    assert('yeah' in ctx.actions)


def test_flag_derivation(ctx):
    """ Annotation of `bool` should resolve to `Flag`
    """
    invocations = []

    def act(quiet: bool = False):
        invocations.append(quiet)
    act = ctx.__call__(act)

    ctx.execute('act')
    ctx.execute('act -q')
    ctx.execute('act --quiet')
    assert(invocations == [
        False, True, True
    ])


@pytest.mark.skip(reason='feature needs further considerations')
def test_derivation_from_default_bool(ctx):
    """ Default values of `bool` should hint on annotaion
    """
    invocations = []

    def act(quiet=False):
        invocations.append(quiet)
    act = ctx.__call__(act)

    ctx.execute('act')
    ctx.execute('act -q')
    ctx.execute('act --quiet')
    assert(invocations == [
        False, True, True
    ])


@pytest.mark.skip(reason='feature needs further considerations')
def test_derivation_from_default_int(ctx):
    """ Default values of `int` should hint on annotaion
    """
    invocations = []

    def act(depth=3):
        invocations.append(depth)
    act = ctx.__call__(act)

    ctx.execute('act')
    ctx.execute('act -d')
    ctx.execute('act --depth=77')
    assert(invocations == [
        False, True, True
    ])


@pytest.mark.skip(reason='feature needs further considerations')
def test_derivation_from_default_str(ctx):
    """ Default values of `str` should hint on annotaion
    """
    invocations = []

    def act(type='f'):
        invocations.append(type)
    act = ctx.__call__(act)

    ctx.execute('act')
    ctx.execute('act -td')
    ctx.execute('act --type=d')
    assert(invocations == [
        'f', 'd', 'd'
    ])


def test_name_derivation_from_underscores(ctx):
    """ Underscores should get replaced with dashes
        when naming arguments automatically
    """
    invocations = []

    def act(follow_symlinks: bool = False):
        invocations.append(follow_symlinks)
    act = ctx.__call__(act)

    ctx.execute('act')
    ctx.execute('act --follow-symlinks')
    assert(invocations == [
        False, True
    ])


def test_mixed_derivation(ctx):
    """ Arguments and options
        should get on well with each other
    """
    def act(a, b, c, *, x, y, z):
        pass
    act = ctx.__call__(act)

    assert(
        set(act.options) == {'x', 'y', 'z'} and
        list(act.arguments) == ['a', 'b', 'c']
    )


def test_arguments_with_mappers(ctx):
    """ Arguments annotated with mappers should work as expected
    """
    def Just77(_):
        return 77

    invocations = []

    def act(a: int, b: Just77, c, *, x, y, z):
        invocations.append((a, b, c, x, y, z))
    act = ctx.__call__(act)

    ctx.execute('act 33 88 77 -xx -yy -zz')
    assert(invocations == [
        (33, 77, '77', 'x', 'y', 'z')
    ])


def test_representation():
    """ Any `action.Option` instance
        should be able to introduce itself
    """
    classes = (
        action.Option, action.Key, action.Count, action.Flag)
    for construct in classes:
        assert(isinstance(
            repr(construct()),
            str))
        assert(isinstance(
            repr(construct('x')),
            str))
        assert(isinstance(
            repr(construct('x', 'xyz')),
            str))
        assert(isinstance(
            repr(construct('x', type=int)),
            str))
        assert(isinstance(
            repr(construct('x', 'xyz', type=int)),
            str))


def test_flags(ctx):
    """ `-q`
    """
    invocations = []

    def act(*, quiet: ctx.Flag):
        invocations.append((quiet,))
    act = ctx.__call__(act)

    ctx.execute('act -q')
    assert(invocations == [(True,)])


def test_short_options_jointly(ctx):
    """ `-c32`
    """
    invocations = []

    def act(*, short_option: str):
        invocations.append((short_option,))
    act = ctx.__call__(act)

    ctx.execute('act -stuff')
    assert(invocations == [('tuff',)])


def test_short_options_separately(ctx):
    """ `-c 32`
    """
    invocations = []

    def act(*, short_option: str):
        invocations.append((short_option,))
    act = ctx.__call__(act)

    ctx.execute('act -s tuff')
    assert(invocations == [('tuff',)])


def test_multiple_short_options_separately(ctx):
    """ `-c 32`, one after another
    """
    invocations = []

    def act(*, x: str, y: str):
        invocations.append((x, y))
    act = ctx.__call__(act)

    ctx.execute('act -x 1 -y 3')
    assert(invocations == [('1', '3')])


def test_mixed_multiple_short_options(ctx):
    """ `-x 32 -y32`
    """
    invocations = []

    def act(*, x: str, y: str, z: str):
        invocations.append((x, y, z))
    act = ctx.__call__(act)

    ctx.execute('act -x 1 -y3 -z 13')
    assert(invocations == [('1', '3', '13')])


def test_short_options_crammed_together(ctx):
    """ `-vc32`,
        where `-v` stands for `--verbose`
        and `-c32` for `--count=32`
    """
    invocations = []

    def act(*, verbose: ctx.Count, count: int):
        invocations.append((verbose, count))
    act = ctx.__call__(act)

    ctx.execute('act -vvvvvvc32')
    assert(invocations == [(6, 32)])


def test_short_options_crammed_together_of_type_str(ctx):
    """ `-vname`,
        where `-v` stands for `--verbose`
        and `-name` for `--name=ame`
    """
    invocations = []

    def act(*, verbose: ctx.Count, name):
        invocations.append((verbose, name))
    act = ctx.__call__(act)

    ctx.execute('act -vvvvvvname')
    assert(invocations == [(6, 'ame')])


def test_short_options_where_str_takes_all(ctx):
    """ `-nvvvvvv`,
        where `-v` stands for `--verbose`
        and `-n` for `--name=...`;
        `-n` should eat it all
    """
    invocations = []

    def act(*, verbose: ctx.Count = 0, name):
        invocations.append((verbose, name))
    act = ctx.__call__(act)

    ctx.execute('act -nvvvvvv')
    assert(invocations == [(0, 'vvvvvv')])


def test_long_options_parsing(ctx):
    """ Long options should work
    """
    invocations = []

    def act(*, long: str, forgotten: str = None):
        invocations.append((long, forgotten))
    act = ctx.__call__(act)

    ctx.execute('act --long=--since=forgotten')
    assert(invocations == [('--since=forgotten', None)])


def test_long_flags_parsing(ctx):
    """ Long flags like `--verbose` should work
    """
    invocations = []

    def act(*, verbose: ctx.Count = 0):
        invocations.append((verbose,))
    act = ctx.__call__(act)

    ctx.execute('act --verbose --verbose')
    assert(invocations == [(2,)])


def test_long_options_parsing_with_space(ctx):
    """ Long options, which are written through space,
        should work as well
    """
    invocations = []

    def act(*, long: str, forgotten: str = None):
        invocations.append((long, forgotten))
    act = ctx.__call__(act)

    ctx.execute('act --long since=forgotten')
    assert(invocations == [('since=forgotten', None)])


def test_shorthand_long_notation(ctx):
    """ Long-form-only options should be understood
    """
    invocations = []

    def act(*, long: ctx.Key('long')):
        invocations.append((long,))
    act = ctx.__call__(act)

    ctx.execute('act --long=yeah')
    assert(invocations == [('yeah',)])


def test_shorthand_long_notation_suppresses_short_form(ctx):
    """ Long-form-only options
        should not fire from a deduced short form
    """
    def act(*, long: ctx.Key('long')):
        pytest.fail(
            test_shorthand_long_notation_suppresses_short_form.__doc__)
    act = ctx.__call__(act)

    with pytest.raises(TypeError):
        ctx.execute('act -lyeah')


def test_triple_annotation(ctx):
    """ Option annotation (str, str, callable) should work
    """
    invocations = []

    def act(*, depth: ('x', 'follow', int) = 0):
        invocations.append((depth,))
    act = ctx.__call__(act)

    ctx.execute('act -x3')
    ctx.execute('act --follow=7')

    assert(invocations == [(3,), (7,)])


def test_triple_annotation_suppresses_name_deduction(ctx):
    """ Option annotation (str, str, callable)
        should shadow an automatically deduced name
    """
    def act(*, depth: ('x', 'follow', int) = 0):
        pytest.fail(
            test_triple_annotation_suppresses_name_deduction.__doc__)
    act = ctx.__call__(act)

    with pytest.raises(TypeError):
        ctx.execute('act --depth=3')


def test_mixed_options_parsing(ctx):
    """ Longs and shorts should work together
    """
    invocations = []

    def act(*, long, short):
        invocations.append((long, short))
    act = ctx.__call__(act)

    ctx.execute('act --long=-long- -s-short-')
    assert(invocations == [('-long-', '-short-')])


def test_default_action(ctx):
    """ Default action should be invoked on unknown word occurrence
    """
    invocations = []

    def fake_action(arg):
        invocations.append(('fake_action', arg))
    fake_action = ctx.__call__(fake_action)

    def default_action(arg):
        invocations.append(('default_action', arg))
    default_action = ctx.default(default_action)

    ctx.execute('stuff')
    assert(invocations == [('default_action', 'stuff')])


def test_uniqueness_of_default_action(ctx):
    """ Default action could be defined at most once
    """
    invocations = []

    def fake_action(arg):
        invocations.append(('fake_action', arg))
    fake_action = ctx.__call__(fake_action)

    def default_action(arg):
        invocations.append(('default_action', arg))
    default_action = ctx.default(default_action)

    with pytest.raises(TypeError):
        default_action = ctx.default(default_action)
        pytest.fail(test_uniqueness_of_default_action.__doc__)


def test_unknown_action(ctx):
    """ With no default, an unknown action should bring up an error
    """
    def act(arg):
        pytest.fail(test_unknown_action.__doc__)
    act = ctx.__call__(act)

    with pytest.raises(RuntimeError):
        ctx.execute('no_such action')
        pytest.fail(test_unknown_action.__doc__)


def test_no_action(ctx):
    """ With no default and no action specified,
        an error should be risen
    """
    def act(arg):
        pytest.fail(test_no_action.__doc__)
    act = ctx.__call__(act)

    with pytest.raises(RuntimeError):
        ctx.execute('')
        pytest.fail(test_no_action.__doc__)


def test_mistyped_argument_list(ctx):
    """ Argv is a list, so an exception should state so
    """
    def act(arg):
        pytest.fail(test_mistyped_argument_list.__doc__)
    act = ctx.__call__(act)

    with pytest.raises(TypeError):
        ctx.execute(2.7)
        pytest.fail(test_mistyped_argument_list.__doc__)


def test_noncallable_argument_annotation(ctx):
    """ Argument annotation should be callable,
        and an error should indicate so
    """
    def act(arg: 2.7):
        pytest.fail(test_noncallable_argument_annotation.__doc__)

    with pytest.raises(TypeError):
        ctx.__call__(act)
        pytest.fail(test_noncallable_argument_annotation.__doc__)


def test_mistyped_option_annotation(ctx):
    """ An error should be risen when an option annotation
        is not something that is supported
    """
    def act(*, arg: 2.7):
        pytest.fail(test_mistyped_option_annotation.__doc__)

    with pytest.raises(TypeError):
        ctx.__call__(act)
        pytest.fail(test_mistyped_option_annotation.__doc__)


def test_mistyped_arguments_to_option_constructor(ctx):
    """ Option should not construct with wrong types
        of input args
    """
    with pytest.raises(TypeError):
        def act(arg: ctx.Key(3, 14)):
            pytest.fail(
                test_mistyped_arguments_to_option_constructor.__doc__)
        ctx.__call__(act)
        ctx.execute('act arg')
        pytest.fail(
            test_mistyped_arguments_to_option_constructor.__doc__)


def test_malformed_short_option(ctx):
    """ TypeError should arise when
        a short option is not short in fact
    """
    with pytest.raises(TypeError):
        def act(arg: ctx.Key('long', 'so-long')):
            pytest.fail(test_malformed_short_option.__doc__)
        ctx.__call__(act)
        pytest.fail(test_malformed_short_option.__doc__)


def test_lambda_as_action(ctx):
    """ Lambda should not be an action
    """
    with pytest.raises(TypeError):
        ctx.__call__(lambda _: _)


def test_bare_option_could_not_be_used(ctx):
    """ Abstract base `Option`
        should raise an error on direct invocation
    """
    with pytest.raises(NotImplementedError):
        def act(arg: ctx.Option()):
            pytest.fail(test_bare_option_could_not_be_used.__doc__)
        ctx.__call__(act)
        ctx.execute('act arg')
        pytest.fail(test_bare_option_could_not_be_used.__doc__)


def test_error_on_insufficient_arguments(ctx):
    """ There should be a descriptive Type Error
        when some args are missing
    """
    def act(arg0, arg1):
        pytest.fail(test_error_on_insufficient_arguments.__doc__)
    act = ctx.__call__(act)
    with pytest.raises(TypeError):
        ctx.execute('act xyz')


def test_error_on_insufficient_argument_to_short(ctx):
    """ There should be a descriptive Type Error
        when some args are missing
    """
    def act(*, count: ctx.Key):
        pytest.fail(
            test_error_on_insufficient_argument_to_short.__doc__)
    act = ctx.__call__(act)
    with pytest.raises(TypeError):
        ctx.execute('act -c')


def test_error_on_insufficient_argument_to_long(ctx):
    """ There should be a descriptive Type Error
        when an arg is required by a long option,
        but no arg is supplied
    """
    def act(*, opt):
        pytest.fail(
            test_error_on_insufficient_argument_to_long.__doc__)
    act = ctx.__call__(act)
    with pytest.raises(TypeError):
        ctx.execute('act --opt')


def test_error_on_superfluous_arguments(ctx):
    """ There should be a descriptive Type Error
        when there are too many args
    """
    def act():
        pytest.fail(test_error_on_superfluous_arguments.__doc__)
    act = ctx.__call__(act)
    with pytest.raises(TypeError):
        ctx.execute('act xyz')


def test_error_on_superfluous_argument_to_long(ctx):
    """ There should be a descriptive Type Error
        when there are an arg to an option
        which does not take one
    """
    def act(*, quiet: ctx.Flag):
        pytest.fail(
            test_error_on_superfluous_argument_to_long.__doc__)
    act = ctx.__call__(act)
    with pytest.raises(TypeError):
        ctx.execute('act --quiet=quiet')


def test_error_on_multiple_key(ctx):
    """ There should be a descriptive Runtime Error
        when the user specifies same key multiple times
    """
    def act(*, arg):
        pytest.fail(test_error_on_multiple_key.__doc__)
    act = ctx.__call__(act)
    with pytest.raises(RuntimeError):
        ctx.execute('act --arg=yeah --arg=yeahs')


def test_variadic(ctx):
    """ Take-all argument should take it all
    """
    invocations = []

    def act(*args):
        invocations.append(args)
    act = ctx.__call__(act)

    ctx.execute('act arg0 arg1 arg2')
    assert(invocations == [('arg0', 'arg1', 'arg2')])


if __name__ == '__main__':
    pytest.main(sys.argv)
