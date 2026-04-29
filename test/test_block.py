import pbk

import pytest

# A height-1 regtest block built on the regtest genesis. Identical to
# the first entry in test/data/regtest/blocks.txt with the nonce bumped
# from 0 to 2 — both nonces produce a hash below the regtest target, so
# this is a valid competing block at height 1 suitable for exercising
# fork-aware code paths.
FORK_BLOCK_HEX = "0000002006226e46111a0b59caaf126043eb5bbf28c34f3a5e332a1fc7b2b73cf188910f295badc0bdd9a2bc0955d12f337491eae4c87ba4660078c0156310284d47c6ff9a242d66ffff7f200200000001020000000001010000000000000000000000000000000000000000000000000000000000000000ffffffff025100ffffffff0200f2052a010000001600141409745405c4e8310a875bcd602db6b9b3dc0cf90000000000000000266a24aa21a9ede2f61c3f71d1defd3fa999dfa36953755c690689799962b48bebd836974e8cf90120000000000000000000000000000000000000000000000000000000000000000000000000"

GENESIS_BLOCK_BYTES = b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;\xa3\xed\xfdz{\x12\xb2z\xc7,>gv\x8fa\x7f\xc8\x1b\xc3\x88\x8aQ2:\x9f\xb8\xaaK\x1e^J\xda\xe5IM\xff\xff\x7f \x02\x00\x00\x00\x01\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xffM\x04\xff\xff\x00\x1d\x01\x04EThe Times 03/Jan/2009 Chancellor on brink of second bailout for banks\xff\xff\xff\xff\x01\x00\xf2\x05*\x01\x00\x00\x00CA\x04g\x8a\xfd\xb0\xfeUH'\x19g\xf1\xa6q0\xb7\x10\\\xd6\xa8(\xe09\t\xa6yb\xe0\xea\x1fa\xde\xb6I\xf6\xbc?L\xef8\xc4\xf3U\x04\xe5\x1e\xc1\x12\xde\\8M\xf7\xba\x0b\x8dW\x8aLp+k\xf1\x1d_\xac\x00\x00\x00\x00"
GENESIS_BLOCK_HASH_BYTES = b'\x06"nF\x11\x1a\x0bY\xca\xaf\x12`C\xeb[\xbf(\xc3O:^3*\x1f\xc7\xb2\xb7<\xf1\x88\x91\x0f'
# Display format (big-endian)
GENESIS_BLOCK_HASH_HEX = (
    "0f9188f13cb7b2c71f2a335e3a4fc328bf5beb436012afca590b1a11466e2206"
)


def test_block_tree_entry(chainman_regtest: pbk.ChainstateManager) -> None:
    chain = chainman_regtest.get_active_chain()

    block_0 = chain.block_tree_entries[0]
    assert block_0.height == 0
    block_1 = chain.block_tree_entries[1]
    assert block_1.height == 1
    assert block_0 != block_1
    assert isinstance(block_0, pbk.BlockTreeEntry)
    assert block_1.previous == block_0
    assert block_1.block_header.block_hash == block_1.block_hash

    # Comparisons are only valid with other BlockTreeEntry objects
    assert block_0 != 0
    assert block_0 != GENESIS_BLOCK_HASH_BYTES

    assert repr(block_0) == f"<BlockTreeEntry height=0 hash={GENESIS_BLOCK_HASH_HEX}>"


def test_block_tree_entry_get_ancestor(chainman_regtest: pbk.ChainstateManager) -> None:
    chain = chainman_regtest.get_active_chain()
    tip = chain.block_tree_entries[chain.height]

    assert tip.get_ancestor(0) == chain.block_tree_entries[0]
    assert tip.get_ancestor(tip.height) == tip
    assert tip.get_ancestor(tip.height - 1) == chain.block_tree_entries[tip.height - 1]

    with pytest.raises(ValueError, match="out of range"):
        tip.get_ancestor(tip.height + 1)
    with pytest.raises(ValueError, match="out of range"):
        tip.get_ancestor(-1)


def test_block_tree_entry_get_ancestor_fork(
    chainman_regtest: pbk.ChainstateManager,
) -> None:
    # Submit a competing block at height 1 and verify get_ancestor on
    # the fork entry walks the fork's own lineage, distinct from the
    # active chain at the same height.
    chain = chainman_regtest.get_active_chain()
    fork_block = pbk.Block(bytes.fromhex(FORK_BLOCK_HEX))
    chainman_regtest.process_block(fork_block)

    fork_entry = chainman_regtest.block_tree_entries[fork_block.block_hash]
    assert fork_entry.height == 1
    assert fork_entry != chain.block_tree_entries[1]
    assert fork_entry.get_ancestor(0) == chain.block_tree_entries[0]
    # get_ancestor at the fork entry's own height returns the fork entry
    # itself — not the active chain entry at the same height. This is
    # the meaningful difference from `chain.block_tree_entries[h]`.
    assert fork_entry.get_ancestor(1) == fork_entry


def test_block_hash(chainman_regtest: pbk.ChainstateManager) -> None:
    hash_zero = pbk.BlockHash(b"0" * 32)

    assert hash_zero == hash_zero
    assert hash_zero == pbk.BlockHash(b"0" * 32)
    assert hash_zero != pbk.BlockHash(b"1" * 32)

    assert bytes(hash_zero) == b"0" * 32
    assert (
        str(hash_zero)
        == "3030303030303030303030303030303030303030303030303030303030303030"
    )

    # Comparisons are only valid with other BlockHash objects
    assert hash_zero != b"0" * 32

    with pytest.raises(ValueError, match="must be bytes of length 32"):
        pbk.BlockHash(b"2" * 31)

    # Test __repr__ - should be evaluable
    assert repr(hash_zero) == "BlockHash(b'00000000000000000000000000000000')"
    # Verify it's evaluable
    hash_recreated = eval(repr(hash_zero), {"BlockHash": pbk.BlockHash})
    assert hash_recreated == hash_zero


def test_block_header() -> None:
    header_hex = "00c06a24d2ff376fa4cab6d28ac75ea4a38a675ac1cafa668cb601000000000000000000755926c6aa5c931b0b054c370746824f8935b35bd27172f1a36c07749b5cd60b9aa77869a1fc01171794522b"
    header = pbk.BlockHeader(bytes.fromhex(header_hex))

    assert (
        str(header.block_hash)
        == "00000000000000000000b1a3614f5b43589011f52dcf2c67c9e66554823ed233"
    )
    assert (
        str(header.prev_hash)
        == "00000000000000000001b68c66facac15a678aa3a45ec78ad2b6caa46f37ffd2"
    )
    assert header.timestamp.timestamp() == 1769514906
    assert header.bits == 386006177
    assert header.version == 610975744
    assert header.nonce == 726832151

    assert bytes(header) == bytes.fromhex(header_hex)

    assert (
        repr(header)
        == "<Block header hash=00000000000000000000b1a3614f5b43589011f52dcf2c67c9e66554823ed233>"
    )

    # Test invalid input lengths
    with pytest.raises(ValueError):
        pbk.BlockHeader(b"\x00" * 79)
    with pytest.raises(ValueError):
        pbk.BlockHeader(b"\x00" * 81)
    with pytest.raises(ValueError):
        pbk.BlockHeader(b"")


def test_block() -> None:
    block = pbk.Block(GENESIS_BLOCK_BYTES)
    assert bytes(block.block_hash) == GENESIS_BLOCK_HASH_BYTES
    assert bytes(block) == GENESIS_BLOCK_BYTES

    assert len(block.transactions) == 1
    assert block.block_header.block_hash == block.block_hash

    # Test __repr__
    assert repr(block) == f"<Block hash={GENESIS_BLOCK_HASH_HEX} txs=1>"


def test_block_check() -> None:
    block = pbk.Block(GENESIS_BLOCK_BYTES)
    consensus_params = pbk.ChainParameters(pbk.ChainType.REGTEST).consensus_params

    # Default flags is ALL.
    state = block.check(consensus_params)
    assert state.validation_mode == pbk.ValidationMode.VALID

    assert pbk.BlockCheckFlags.ALL == (
        pbk.BlockCheckFlags.POW | pbk.BlockCheckFlags.MERKLE
    )


def test_block_check_invalid_merkle() -> None:
    # Mutate the merkle root in the serialized block. With merkle
    # checking enabled the block must fail; with it disabled the block
    # passes the (remaining) checks. This proves the `flags` argument
    # actually toggles checks, beyond just being accepted by the C call.
    consensus_params = pbk.ChainParameters(pbk.ChainType.REGTEST).consensus_params
    raw = bytearray(GENESIS_BLOCK_BYTES)
    raw[36] ^= 0xFF  # flip a byte in the merkle root field (bytes 36..68)
    bad_block = pbk.Block(bytes(raw))

    state = bad_block.check(consensus_params, pbk.BlockCheckFlags.MERKLE)
    assert state.validation_mode == pbk.ValidationMode.INVALID
    assert state.block_validation_result == pbk.BlockValidationResult.MUTATED

    state = bad_block.check(consensus_params, pbk.BlockCheckFlags.BASE)
    assert state.validation_mode == pbk.ValidationMode.VALID


def test_block_undo(chainman_regtest: pbk.ChainstateManager) -> None:
    chain_man = chainman_regtest
    idx = chain_man.get_active_chain().block_tree_entries[202]
    undo = chain_man.block_spent_outputs[idx]
    transactions = undo.transactions
    assert len(transactions) == 20
    for tx in transactions:
        assert isinstance(tx, pbk.TransactionSpentOutputs)

    # Test __repr__
    assert repr(undo) == "<BlockSpentOutputs txs=20>"
