""" Constitution checks on feature code: no blocking sleeps (I), no hard-coded coordinates (II), no bare except (VI) """
import ast
import glob
from unittest import TestCase


FEATURE_FILES = sorted(glob.glob('modules/*.py'))


def parse(path):
    with open(path, encoding='utf-8') as file:
        return ast.parse(file.read(), path)


def is_number(node):
    return isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool)


class TestPrinciples(TestCase):

    def test_no_time_sleep(self):
        for path in FEATURE_FILES:
            for node in ast.walk(parse(path)):
                if isinstance(node, ast.Attribute) and node.attr == 'sleep' and \
                        isinstance(node.value, ast.Name) and node.value.id == 'time':
                    self.fail(f"{path}:{node.lineno} uses time.sleep; await ctx.sleep instead")

    def test_no_coordinate_literals(self):
        for path in FEATURE_FILES:
            for node in ast.walk(parse(path)):
                if isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) in (2, 4) and \
                        all(is_number(e) for e in node.elts):
                    values = [e.value for e in node.elts]
                    self.fail(f"{path}:{node.lineno} has a coordinate-like literal {values}; "
                              f"positions must come from the layout")

    def test_no_bare_except(self):
        for path in FEATURE_FILES:
            for node in ast.walk(parse(path)):
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    self.fail(f"{path}:{node.lineno} has a bare except")
