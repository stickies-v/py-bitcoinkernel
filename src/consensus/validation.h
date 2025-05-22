// Copyright (c) 2009-2010 Satoshi Nakamoto
// Copyright (c) 2009-2022 The Bitcoin Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef BITCOIN_CONSENSUS_VALIDATION_H
#define BITCOIN_CONSENSUS_VALIDATION_H

#include <consensus/consensus.h>
#include <kernel/validation_state.h> // IWYU pragma: export
#include <primitives/block.h>
#include <primitives/transaction.h>

/** Index marker for when no witness commitment is present in a coinbase transaction. */
static constexpr int NO_WITNESS_COMMITMENT{-1};

/** Minimum size of a witness commitment structure. Defined in BIP 141. **/
static constexpr size_t MINIMUM_WITNESS_COMMITMENT{38};

/** A "reason" why a transaction was invalid, suitable for determining whether the
  * provider of the transaction should be banned/ignored/disconnected/etc.
  */
enum class TxValidationResult {
    TX_RESULT_UNSET = 0,     //!< initial value. Tx has not yet been rejected
    TX_CONSENSUS,            //!< invalid by consensus rules
    TX_INPUTS_NOT_STANDARD,   //!< inputs (covered by txid) failed policy rules
    TX_NOT_STANDARD,          //!< otherwise didn't meet our local policy rules
    TX_MISSING_INPUTS,        //!< transaction was missing some of its inputs
    TX_PREMATURE_SPEND,       //!< transaction spends a coinbase too early, or violates locktime/sequence locks
    /**
     * Transaction might have a witness prior to SegWit
     * activation, or witness may have been malleated (which includes
     * non-standard witnesses).
     */
    TX_WITNESS_MUTATED,
    /**
     * Transaction is missing a witness.
     */
    TX_WITNESS_STRIPPED,
    /**
     * Tx already in mempool or conflicts with a tx in the chain
     * (if it conflicts with another tx in mempool, we use MEMPOOL_POLICY as it failed to reach the RBF threshold)
     * Currently this is only used if the transaction already exists in the mempool or on chain.
     */
    TX_CONFLICT,
    TX_MEMPOOL_POLICY,        //!< violated mempool's fee/size/descendant/RBF/etc limits
    TX_NO_MEMPOOL,            //!< this node does not have a mempool so can't validate the transaction
    TX_RECONSIDERABLE,        //!< fails some policy, but might be acceptable if submitted in a (different) package
    TX_UNKNOWN,               //!< transaction was not validated because package failed
};

class TxValidationState : public ValidationState<TxValidationResult> {};

// These implement the weight = (stripped_size * 4) + witness_size formula,
// using only serialization with and without witness data. As witness_size
// is equal to total_size - stripped_size, this formula is identical to:
// weight = (stripped_size * 3) + total_size.
static inline int32_t GetTransactionWeight(const CTransaction& tx)
{
    return ::GetSerializeSize(TX_NO_WITNESS(tx)) * (WITNESS_SCALE_FACTOR - 1) + ::GetSerializeSize(TX_WITH_WITNESS(tx));
}
static inline int64_t GetBlockWeight(const CBlock& block)
{
    return ::GetSerializeSize(TX_NO_WITNESS(block)) * (WITNESS_SCALE_FACTOR - 1) + ::GetSerializeSize(TX_WITH_WITNESS(block));
}
static inline int64_t GetTransactionInputWeight(const CTxIn& txin)
{
    // scriptWitness size is added here because witnesses and txins are split up in segwit serialization.
    return ::GetSerializeSize(TX_NO_WITNESS(txin)) * (WITNESS_SCALE_FACTOR - 1) + ::GetSerializeSize(TX_WITH_WITNESS(txin)) + ::GetSerializeSize(txin.scriptWitness.stack);
}

/** Compute at which vout of the block's coinbase transaction the witness commitment occurs, or -1 if not found */
inline int GetWitnessCommitmentIndex(const CBlock& block)
{
    int commitpos = NO_WITNESS_COMMITMENT;
    if (!block.vtx.empty()) {
        for (size_t o = 0; o < block.vtx[0]->vout.size(); o++) {
            const CTxOut& vout = block.vtx[0]->vout[o];
            if (vout.scriptPubKey.size() >= MINIMUM_WITNESS_COMMITMENT &&
                vout.scriptPubKey[0] == OP_RETURN &&
                vout.scriptPubKey[1] == 0x24 &&
                vout.scriptPubKey[2] == 0xaa &&
                vout.scriptPubKey[3] == 0x21 &&
                vout.scriptPubKey[4] == 0xa9 &&
                vout.scriptPubKey[5] == 0xed) {
                commitpos = o;
            }
        }
    }
    return commitpos;
}

#endif // BITCOIN_CONSENSUS_VALIDATION_H
