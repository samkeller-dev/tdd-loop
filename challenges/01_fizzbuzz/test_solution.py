import pytest

from solution import fizzbuzz


def test_n_equals_1():
    assert fizzbuzz(1) == ["1"]


def test_n_equals_3():
    assert fizzbuzz(3) == ["1", "2", "Fizz"]


def test_n_equals_5():
    assert fizzbuzz(5) == ["1", "2", "Fizz", "4", "Buzz"]


def test_first_fizzbuzz_at_15():
    result = fizzbuzz(15)
    assert len(result) == 15
    assert result[14] == "FizzBuzz"
    assert result[2] == "Fizz"
    assert result[4] == "Buzz"


@pytest.mark.parametrize("i, expected", [
    (1, "1"),
    (2, "2"),
    (3, "Fizz"),
    (5, "Buzz"),
    (9, "Fizz"),
    (10, "Buzz"),
    (14, "14"),
    (15, "FizzBuzz"),
    (30, "FizzBuzz"),
])
def test_individual_positions(i, expected):
    assert fizzbuzz(i)[-1] == expected


def test_length_matches_n():
    assert len(fizzbuzz(100)) == 100
