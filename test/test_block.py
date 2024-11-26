import pbk


def test_block_index(chainman_regtest: pbk.ChainstateManager):
    chain_man = chainman_regtest
    
    genesis = chain_man.get_block_index_from_genesis()
    chain_tip = chain_man.get_block_index_from_tip()
    assert chain_tip.height > 0
    assert chain_man.get_block_index_from_height(0) == genesis
    assert chain_man.get_block_index_from_hash(chain_tip.block_hash) == chain_tip

    block_1 = chain_man.get_next_block_index(genesis)
    assert block_1 and block_1.height == 1
    assert chain_man.get_previous_block_index(block_1) == genesis

    tip_minus_5 = chain_man.get_block_index_from_height(chain_tip.height - 5)
    for idx in pbk.block_index_generator(chain_man, tip_minus_5):
        pass
    for idx in pbk.block_index_generator(chain_man, chain_tip, tip_minus_5):
        pass

def test_read_block(chainman_regtest: pbk.ChainstateManager):
    chain_man = chainman_regtest
    chain_tip = chain_man.get_block_index_from_tip()

    block_tip = chain_man.read_block_from_disk(chain_tip)
    assert block_tip.hash == chain_tip.block_hash
    copied_block = pbk.Block(block_tip.data)
    assert copied_block.hash == block_tip.hash
