import pbk


def test_transaction():
    ser_tx = bytes.fromhex(
        "010000000320ad43984a790ca5a964904686b8e17732ccf9d0d5f679f7675623e971890385010000006b483045022100ad4777681f360e7791d3f866006415b6511723abbd75a318c5a91c951122c03602202a5eadc8054dbf1d269a6b17c116bac42b4c110da693f2226a0ef7fcd659395f0121026de67c5ce81b6adf330ac6201a7339efa5503a49f1bf95a88c89e214a62dcac8feffffffcbe2144e8fad7e1e1cc270f7dbc75f64f961a5279696160e4a108bd84ebe5ca0ba0200006a47304402204eeb81c63817e960e7854393f64b212480d2dfc0be583601b0702251e5a63de002200b2f37228768a0547ea037ac47e2d948c411c4fdd2ab74f6f21d6805a5a380fb01210364492cd3a5a9365dcb46bb509381ec002052ee8df5a89d6192747c6eb15fe32dfeffffff08ef4370f8930e28110fc172475e42adf9bb0c11cf764e2c61b536a314946f76010000006a47304402203455335b54e31b0dcb82340e8ad7a4ef583da1923e0d2a9628d5728f5258c058022030d0134897a2f8d7303d3abfdd6a08c593acbb0b91d43287af4ac909e7ebf7bd01210267a46854fe5c0ac26049eb48b95cbfce7cc1e3f6baf540f3c8d3b80fda65bc53feffffff0240420f00000000001976a9140542e43d197f1a2e525d02e95ab70a2517e625a888acf9430f00000000001976a914b6bc75e3a6e8be9a86caab8cbeebb640d7468d4388ac9f680600"
    )
    tx = pbk.Transaction(ser_tx)

    # Txid tests
    # kernel displays txids in reverse byte order (little-endian)
    txid = tx.txid
    assert (
        txid.to_bytes()[::-1].hex()
        == "9ababd66265528586981359efbf6b4c303430503e90d811c24d431cfd3994c55"
    )

    assert txid == txid
    assert txid != 0

    # TransactionInput & TransactionOutPoint
    inputs_expected_results = [
        [1, "85038971e9235667f779f6d5d0f9cc3277e1b886469064a9a50c794a9843ad20"],
        [698, "a05cbe4ed88b104a0e16969627a561f9645fc7dbf770c21c1e7ead8f4e14e2cb"],
        [1, "766f9414a336b5612c4e76cf110cbbf9ad425e4772c10f11280e93f87043ef08"],
    ]
    assert tx.input_count == len(inputs_expected_results)

    for i in range(tx.input_count):
        input = tx.get_input_at(i)
        exp_idx, exp_txid = inputs_expected_results[i]
        assert input.out_point.index == exp_idx
        assert input.out_point.txid.to_bytes()[::-1].hex() == exp_txid

    # TransactionOutput
    assert tx.output_count == 2
    output_1 = tx.get_output_at(0)
    assert output_1.amount == 1000000
    assert (
        output_1.script_pubkey.data.hex()
        == "76a9140542e43d197f1a2e525d02e95ab70a2517e625a888ac"
    )
    output_2 = tx.get_output_at(1)
    assert output_2.amount == 1000441
    assert (
        output_2.script_pubkey.data.hex()
        == "76a914b6bc75e3a6e8be9a86caab8cbeebb640d7468d4388ac"
    )


def test_block_undo(chainman_regtest: pbk.ChainstateManager):
    chain_man = chainman_regtest
    for idx in pbk.block_index_generator(chain_man.get_active_chain(), start=1):
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
