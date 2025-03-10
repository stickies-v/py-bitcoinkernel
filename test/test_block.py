import pbk

GENESIS_BLOCK_BYTES = b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;\xa3\xed\xfdz{\x12\xb2z\xc7,>gv\x8fa\x7f\xc8\x1b\xc3\x88\x8aQ2:\x9f\xb8\xaaK\x1e^J\xda\xe5IM\xff\xff\x7f \x02\x00\x00\x00\x01\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xffM\x04\xff\xff\x00\x1d\x01\x04EThe Times 03/Jan/2009 Chancellor on brink of second bailout for banks\xff\xff\xff\xff\x01\x00\xf2\x05*\x01\x00\x00\x00CA\x04g\x8a\xfd\xb0\xfeUH'\x19g\xf1\xa6q0\xb7\x10\\\xd6\xa8(\xe09\t\xa6yb\xe0\xea\x1fa\xde\xb6I\xf6\xbc?L\xef8\xc4\xf3U\x04\xe5\x1e\xc1\x12\xde\\8M\xf7\xba\x0b\x8dW\x8aLp+k\xf1\x1d_\xac\x00\x00\x00\x00"
GENESIS_BLOCK_HASH_BYTES = b'\x06"nF\x11\x1a\x0bY\xca\xaf\x12`C\xeb[\xbf(\xc3O:^3*\x1f\xc7\xb2\xb7<\xf1\x88\x91\x0f'
GENESIS_BLOCK_HASH_HEX = (
    "06226e46111a0b59caaf126043eb5bbf28c34f3a5e332a1fc7b2b73cf188910f"
)


def test_block_index(chainman_regtest: pbk.ChainstateManager):
    chain_man = chainman_regtest

    block_0 = chain_man.get_block_index_from_height(0)
    assert block_0.height == 0
    block_1 = chain_man.get_block_index_from_height(1)
    assert block_1.height == 1
    assert block_0 != block_1
    assert isinstance(block_0, pbk.BlockIndex)

    # Comparisons are only valid with other BlockIndex objects
    assert block_0 != 0
    assert block_0 != GENESIS_BLOCK_HASH_BYTES


def test_block_hash(chainman_regtest: pbk.ChainstateManager):
    chain_man = chainman_regtest
    genesis_hash = chain_man.get_block_index_from_height(0).block_hash
    assert genesis_hash.bytes == GENESIS_BLOCK_HASH_BYTES
    assert genesis_hash.hex == GENESIS_BLOCK_HASH_HEX
    assert genesis_hash == chain_man.get_block_index_from_genesis().block_hash
    assert genesis_hash != chain_man.get_block_index_from_height(1).block_hash

    # Comparisons are only valid with other BlockHash objects
    assert genesis_hash != 0
    assert genesis_hash != GENESIS_BLOCK_HASH_BYTES


def test_block():
    block = pbk.Block(GENESIS_BLOCK_BYTES)
    assert block.hash.bytes == GENESIS_BLOCK_HASH_BYTES
    assert block.data == GENESIS_BLOCK_BYTES


def test_block_undo(chainman_regtest: pbk.ChainstateManager):
    chain_man = chainman_regtest
    idx = chain_man.get_block_index_from_height(202)
    undo = chain_man.read_block_undo_from_disk(idx)
    transactions = list(undo.iter_transactions())
    assert undo.transaction_count == 20
    assert len(transactions) == 20
    for tx in transactions:
        assert isinstance(tx, pbk.TransactionUndo)
