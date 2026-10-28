import pytest

from nukebot.core.templates import render_template, random_name


def test_render_template_basic():
    assert render_template("nuke-{i}", 3, {"guild": "G"}) == "nuke-3"


def test_render_template_random_length():
    value = render_template("x-{random}", 1)
    assert value.startswith("x-")
    assert len(value) <= 100


def test_random_name():
    name = random_name("role", 4)
    assert name.startswith("role-")
