import pbk


def test_block_undo(chainman_regtest: pbk.ChainstateManager):
    chain_man = chainman_regtest
    for idx in pbk.block_index_generator(chain_man, start=1):
        undo = chain_man.read_block_undo_from_disk(idx)
        transactions = list(undo.iter_transactions())
        assert len(transactions) == undo.transaction_count
        for tx in transactions:
            outputs = list(tx.iter_outputs())
            assert len(outputs) == tx.output_count
            assert tx.output_count > 0
            for output in outputs:
                assert output.amount > 0
                assert len(output.script_pubkey.data) > 0
