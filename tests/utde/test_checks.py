import pytest
from utde.checks import check
from utde.errors import TypeCheckError


# TEST TYPE CHECKING
def test_type_check_succeds_on_correct_types():
    @check
    def foo(x: int):
        pass

    foo(1)


def test_type_check_fails_on_wrong_types():
    @check
    def foo(x: int):
        pass

    with pytest.raises(TypeCheckError):
        foo(1.0)


def test_type_check_succeds_without_type_annotation():
    @check
    def foo(x):
        pass

    foo(1.0)


def test_type_check_for_correct_union_type():
    @check
    def foo(x: int | float):
        pass

    foo(42.0)


def test_type_check_succeeds_for_correct_nested_type():
    @check
    def foo(x: list[int]):
        pass

    foo([42])


def test_type_check_fails_for_wrong_nested_type():
    @check
    def foo(x: list[int]):
        pass

    with pytest.raises(TypeCheckError):
        foo([1.33])


def test_type_check_succeeds_for_subclass():
    class Animal:
        pass

    class Dog(Animal):
        pass

    @check
    def foo(x: Animal):
        pass

    foo(Dog())


def test_type_check_fails_for_superclass():
    class Animal:
        pass

    class Dog(Animal):
        pass

    @check
    def foo(x: Dog):
        pass

    # fail because foo explicitly requires a dog
    # and we just provide an animal (like cat)
    with pytest.raises(TypeCheckError):
        foo(Animal())


def test_disabled_type_check_with_wrong_call_types_succeeds():
    @check(enable_type_checks=False)
    def foo(x: int):
        pass

    foo("wrong type")


def test_type_check_succeds_on_correct_return_type():
    @check
    def foo(x: int) -> int:
        return x

    foo(42)


def test_type_check_fails_on_correct_wrong_type():
    @check
    def foo(x: int) -> float:
        return x

    with pytest.raises(TypeCheckError):
        foo(42)
