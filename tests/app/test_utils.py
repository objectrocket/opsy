import copy
import pytest
from flask import Flask
from opsy.utils import (gwrap, rwrap, print_error, print_notice, merge_dict,
                        get_protected_routes, get_valid_permissions)
from opsy.rbac import need_permission


def test_print_utils(capsys):
    """Testing to make sure our print utils work."""
    # Make sure we can print green and red text
    assert gwrap('test') == '\033[92mtest\033[0m'
    assert rwrap('test') == '\033[91mtest\033[0m'
    # Tests for print_notice
    print_notice('test message')
    captured = capsys.readouterr()
    assert captured.out == '[\033[92mNotice\033[0m] test message\n'
    print_notice('test message', title='test')
    captured = capsys.readouterr()
    assert captured.out == '[\033[92mtest\033[0m] test message\n'
    # Tests for print_error
    with pytest.raises(SystemExit) as pytest_wrapped_e:
            print_error('error')
    captured = capsys.readouterr()
    assert captured.err == '[\033[91mSomething broke\033[0m] error\n'
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1
    with pytest.raises(SystemExit) as pytest_wrapped_e:
            print_error('error', title='uhoh')
    captured = capsys.readouterr()
    assert captured.err == '[\033[91muhoh\033[0m] error\n'
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1
    print_error('error', title='uhoh', exit_script=False)
    captured = capsys.readouterr()
    assert captured.err == '[\033[91muhoh\033[0m] error\n'
    print_error(AssertionError('test'), exit_script=False)
    captured = capsys.readouterr()
    assert captured.err == '[\033[91mAssertionError\033[0m] test\n'


def test_merge_dict():
    """Make sure merge dict is working right.

    Just stealing the tests for dictupdate from salt since that's where this
    function originally came from:
    https://github.com/saltstack/salt/blob/2019.2/tests/unit/utils/test_dictupdate.py
    """
    dict1 = {'A': 'B', 'C': {'D': 'E', 'F': {'G': 'H', 'I': 'J'}}}

    # level 1 value changes
    mdict = copy.deepcopy(dict1)
    mdict['A'] = 'Z'
    res = merge_dict(copy.deepcopy(dict1), {'A': 'Z'})
    assert res == mdict

    # level 1 value changes (list replacement)
    mdict = copy.deepcopy(dict1)
    mdict['A'] = [1, 2]
    res = merge_dict(copy.deepcopy(mdict), {'A': [2, 3]},
                     merge_lists=False)
    mdict['A'] = [2, 3]
    assert res == mdict

    # level 1 value changes (list merge)
    mdict = copy.deepcopy(dict1)
    mdict['A'] = [1, 2]
    res = merge_dict(copy.deepcopy(mdict), {'A': [3, 4]},
                     merge_lists=True)
    mdict['A'] = [1, 2, 3, 4]
    assert res == mdict

    # level 1 value changes (list merge, remove duplicates, preserve order)
    mdict = copy.deepcopy(dict1)
    mdict['A'] = [1, 2]
    res = merge_dict(copy.deepcopy(mdict), {'A': [4, 3, 2, 1]},
                     merge_lists=True)
    mdict['A'] = [1, 2, 4, 3]
    assert res == mdict

    # level 2 value changes
    mdict = copy.deepcopy(dict1)
    mdict['C']['D'] = 'Z'
    res = merge_dict(copy.deepcopy(dict1), {'C': {'D': 'Z'}})
    assert res == mdict

    # level 2 value changes (list replacement)
    mdict = copy.deepcopy(dict1)
    mdict['C']['D'] = ['a', 'b']
    res = merge_dict(copy.deepcopy(mdict), {'C': {'D': ['c', 'd']}},
                     merge_lists=False)
    mdict['C']['D'] = ['c', 'd']
    assert res == mdict

    # level 2 value changes (list merge)
    mdict = copy.deepcopy(dict1)
    mdict['C']['D'] = ['a', 'b']
    res = merge_dict(copy.deepcopy(mdict), {'C': {'D': ['c', 'd']}},
                     merge_lists=True)
    mdict['C']['D'] = ['a', 'b', 'c', 'd']
    assert res == mdict

    # level 2 value changes (list merge, remove duplicates, preserve order)
    mdict = copy.deepcopy(dict1)
    mdict['C']['D'] = ['a', 'b']
    res = merge_dict(copy.deepcopy(mdict), {'C': {'D': ['d', 'c', 'b', 'a']}},
                     merge_lists=True)
    mdict['C']['D'] = ['a', 'b', 'd', 'c']
    assert res == mdict

    # level 3 value changes
    mdict = copy.deepcopy(dict1)
    mdict['C']['F']['G'] = 'Z'
    res = merge_dict(
        copy.deepcopy(dict1),
        {'C': {'F': {'G': 'Z'}}}
    )
    assert res == mdict

    # level 3 value changes (list replacement)
    mdict = copy.deepcopy(dict1)
    mdict['C']['F']['G'] = ['a', 'b']
    res = merge_dict(copy.deepcopy(mdict), {'C': {'F': {'G': ['c', 'd']}}},
                     merge_lists=False)
    mdict['C']['F']['G'] = ['c', 'd']
    assert res == mdict

    # level 3 value changes (list merge)
    mdict = copy.deepcopy(dict1)
    mdict['C']['F']['G'] = ['a', 'b']
    res = merge_dict(copy.deepcopy(mdict), {'C': {'F': {'G': ['c', 'd']}}},
                     merge_lists=True)
    mdict['C']['F']['G'] = ['a', 'b', 'c', 'd']
    assert res == mdict

    # level 3 value changes (list merge, remove duplicates, preserve order)
    mdict = copy.deepcopy(dict1)
    mdict['C']['F']['G'] = ['a', 'b']
    res = merge_dict(copy.deepcopy(mdict),
                     {'C': {'F': {'G': ['d', 'c', 'b', 'a']}}},
                     merge_lists=True)
    mdict['C']['F']['G'] = ['a', 'b', 'd', 'c']
    assert res == mdict

    # replace a sub-dictionary
    mdict = copy.deepcopy(dict1)
    mdict['C'] = 'Z'
    res = merge_dict(copy.deepcopy(dict1), {'C': 'Z'})
    assert res == mdict

    # add a new scalar value
    mdict = copy.deepcopy(dict1)
    mdict['Z'] = 'Y'
    res = merge_dict(copy.deepcopy(dict1), {'Z': 'Y'})
    assert res == mdict

    # add a dictionary
    mdict = copy.deepcopy(dict1)
    mdict['Z'] = {'Y': 'X'}
    res = merge_dict(copy.deepcopy(dict1), {'Z': {'Y': 'X'}})
    assert res == mdict

    # add a nested dictionary
    mdict = copy.deepcopy(dict1)
    mdict['Z'] = {'Y': {'X': 'W'}}
    res = merge_dict(
        copy.deepcopy(dict1),
        {'Z': {'Y': {'X': 'W'}}}
    )
    assert res == mdict

    # Now we'll do some additional testing to get this to 100% coverage
    with pytest.raises(TypeError):
        merge_dict([], [])

    mdict = {'test': None}
    res = merge_dict({}, {'test': None})
    assert res == mdict


def test_get_protected_routes():
    """Make sure get protected routes is working right."""
    # Make an empty app with no routes
    app = Flask('test_app', static_folder=None)
    # And make sure we get an empty response
    with app.app_context():
        assert get_protected_routes() == []

    # Let's add an unprotected route and make sure it's the same output

    @app.route('/test_route')
    def test_route():
        pass

    with app.app_context():
        assert get_protected_routes() == []

    # Now let's add a protected route and make sure that's in there

    @app.route('/test_protected_route')
    @need_permission('test_protected_show')
    def test_protected_route():
        pass

    expected_output = [{
        'endpoint': '/test_protected_route',
        'method': 'GET, HEAD, OPTIONS',
        'permission_needed': 'test_protected_show'
    }]
    with app.app_context():
        assert expected_output == get_protected_routes()

    # Now with a method filter
    expected_output = [{
        'endpoint': '/test_protected_route',
        'method': 'GET',
        'permission_needed': 'test_protected_show'
    }]
    with app.app_context():
        assert expected_output == get_protected_routes(
            ignored_methods=["HEAD", "OPTIONS"])


def test_get_valid_permissions():
    """Make sure get valid permissions is working right."""
    # Make an empty app with no routes
    app = Flask('test_app', static_folder=None)
    # And make sure we get an empty response
    with app.app_context():
        assert get_valid_permissions() == []

    # Let's add an unprotected route and make sure it's the same output

    @app.route('/test_route')
    def test_route():
        pass

    with app.app_context():
        assert get_valid_permissions() == []

    # Now let's add a protected route and make sure that's in there

    @app.route('/test_protected_route')
    @need_permission('test_protected_show')
    def test_protected_route():
        pass

    expected_output = ['test_protected_show']
    with app.app_context():
        assert expected_output == get_valid_permissions()
