import pytest

import pbk.util.sequence as seq


class MockOwner:
    def __init__(self, count):
        self.count = count
        self.count_calls = 0
        self.get_calls = []


class SimpleSequence(seq.LazySequence[str]):
    """Test sequence for LazySequence functionality."""

    def __init__(self, owner: MockOwner):
        self._owner = owner

    def __len__(self) -> int:
        self._owner.count_calls += 1
        return self._owner.count

    def _get_item(self, index: int) -> str:
        self._owner.get_calls.append(index)
        return f"item_{index}"


class TestLazySequence:
    def test_length(self):
        owner = MockOwner(3)
        seq_obj = SimpleSequence(owner)

        assert len(seq_obj) == 3
        assert owner.count_calls == 1

    def test_positive_indexing(self):
        owner = MockOwner(3)
        seq_obj = SimpleSequence(owner)

        assert seq_obj[0] == "item_0"
        assert seq_obj[2] == "item_2"
        assert owner.get_calls == [0, 2]

    def test_negative_indexing(self):
        owner = MockOwner(3)
        seq_obj = SimpleSequence(owner)

        assert seq_obj[-1] == "item_2"
        assert seq_obj[-3] == "item_0"
        assert owner.get_calls == [2, 0]

    def test_slicing(self):
        owner = MockOwner(4)
        seq_obj = SimpleSequence(owner)

        result = seq_obj[1:3]
        assert result == ["item_1", "item_2"]
        assert owner.get_calls == [1, 2]

    def test_index_out_of_bounds(self):
        owner = MockOwner(2)
        seq_obj = SimpleSequence(owner)

        with pytest.raises(IndexError):
            seq_obj[2]
        with pytest.raises(IndexError):
            seq_obj[-3]
