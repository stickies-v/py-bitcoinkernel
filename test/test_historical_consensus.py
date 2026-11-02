"""
================================================================================
Historical Consensus Regression Tests for libbitcoinkernel (via py-bitcoinkernel)
================================================================================
Validates that historical Bitcoin protocol rules and edge-cases are strictly and
deterministically enforced by the C++ libbitcoinkernel engine:

1. Evolution of ScriptVerificationFlags across soft-fork eras (NONE -> ALL).
2. Construction and length validation of Satoshi-era P2PK scripts.
3. BIP-66 strict DER ECDSA signature verification (differential testing of
   canonical DER vs. non-strict BER zero-padded signatures).
4. CVE-2010-5139 integer overflow rejection (184.46 billion BTC exploit payload).
5. ChainstateManager in-memory lifecycle & Block #1 header connection.
6. Strict orphan detection and rejection on disconnected block headers.
================================================================================
"""

import struct
import pytest
import pbk
from pbk import (
    Block,
    BlockCheckFlags,
    BlockHeader,
    BlockValidationResult,
    ChainParameters,
    ChainType,
    ScriptPubkey,
    ScriptVerificationFlags,
    Transaction,
    ValidationMode,
    load_chainman,
)
try:
    from pbk.exceptions import ProcessBlockHeaderException
except ImportError:
    from pbk.util.exc import ProcessBlockHeaderException

# ------------------------------------------------------------------------------
# Test Vectors (Pure in-memory hex constants, zero external file dependencies)
# ------------------------------------------------------------------------------

# Satoshi Genesis uncompressed 65-byte public key (January 2009)
GENESIS_PUBKEY_HEX = (
    "04678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb"
    "649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5f"
)
# Script: 0x41 (OP_PUSHBYTES_65) + 65-byte pubkey + 0xac (OP_CHECKSIG) -> 67 bytes
GENESIS_P2PK_SCRIPT_HEX = "41" + GENESIS_PUBKEY_HEX + "ac"

# Canonical Satoshi-era Mainnet spend (TXID d71fd2f64c0b34465b7518d240c00e83f6a5b10138a7079d1252858fe7e6b577)
# Spending a 50 BTC P2PK coinbase output with valid DER-encoded ECDSA signature.
CANONICAL_TX_HEX = (
    "0100000001ebc18e3ca2d6e33a1ccd46ddde8c64224b2b07042b8c6f3e79e7a2c9649eff0000000000"
    "48473044022038ea59740da72eec2490a0b32fa6004139524fefba7e78c5d0aed40a5c07f39b02205b"
    "1adea529c3cc5cdbb900a8515d778b8e982d63b13386d955962a93f70cd27101ffffffff0200f90295"
    "00000000434104f36c67039006ec4ed2c885d7ab0763feb5deb9633cf63841474712e4cf0459356750"
    "185fc9d962d0f4a1e08e1a84f0c9a9f826ad067675403c19d752530492dcac00f90295000000004341"
    "048b48e109f432a490522f8d0e9e833443809f65b8aa2558b94c1c15eb0fd3e24f32d58a088a2b0e5e"
    "694d05e7b981e5c9750827646eb81debc816c3c667eea5fdac00000000"
)

# Previous output scriptPubkey (P2PK 65-byte uncompressed pubkey)
PREV_SPK_P2PK_HEX = (
    "41048b48e109f432a490522f8d0e9e833443809f65b8aa2558b94c1c15eb0fd3e24f"
    "32d58a088a2b0e5e694d05e7b981e5c9750827646eb81debc816c3c667eea5fdac"
)
PREV_OUT_VALUE_SATS = 50_0000_0000  # 50 BTC

# Canonical Mainnet Block #1 Header (80 bytes)
BLOCK1_HEADER_HEX = (
    "010000006fe28c0ab6f1b372c1a6a246ae63f74f931e8365e15a089c68d6190000000000"
    "f1426a5880630a0a1ef0cbda5eb13d1013fc9092c066f22b0f99353afd996ef08620b26a"
    "ffff001d2e67c903"
)

# Canonical Mainnet Block #1 Full Block (218 bytes: 80B header + 1 coinbase TX)
BLOCK1_FULL_HEX = (
    "010000006fe28c0ab6f1b372c1a6a246ae63f74f931e8365e15a089c68d6190000000000"
    "f1426a5880630a0a1ef0cbda5eb13d1013fc9092c066f22b0f99353afd996ef08620b26a"
    "ffff001d2e67c90301010000000100000000000000000000000000000000000000000000"
    "00000000000000000000ffffffff0a04ffff001d0427df2c72ffffffff0100f2052a0100"
    "000043410412a8c52fd14e7ad2abc43845907824a006533a8f5674e9d5aa66e0ebe599fc"
    "f46411f2622d0617559305b4c71fb5dc56c58f21c4651e196018932dc98dd0bfe7ac0000"
    "0000"
)

# Disconnected / Orphan Block Header (Block #281 header, pointing to non-existent ancestor)
BLOCK281_HEADER_HEX = (
    "0100000009e21e3143eb8950840f91072e093f9e3d8fdaf02e174dbe392607a200000000"
    "e62f11568e0383c7002a41644c1e84deca71da6387c189094c7f5bba8ef6645f2057af6a"
    "ffff001d7b4be703"
)


# ==============================================================================
# TESTS
# ==============================================================================

def test_script_verification_flags_timeline():
    """
    Validates the bitwise constants of ScriptVerificationFlags across the protocol's
    soft-fork history (Satoshi era through BIP-16, BIP-66, BIP-141, and Taproot).
    """
    # Satoshi era (v0.1, 2009): Zero script enforcement flags
    assert ScriptVerificationFlags.NONE.value == 0x0

    # BIP-16 (P2SH, 2012)
    assert (ScriptVerificationFlags.P2SH.value & 0x1) == 0x1

    # BIP-66 (Strict DER signatures, 2015)
    assert (ScriptVerificationFlags.DERSIG.value & 0x4) == 0x4
    p2sh_dersig = ScriptVerificationFlags.P2SH | ScriptVerificationFlags.DERSIG
    assert p2sh_dersig.value == 0x5

    # BIP-65 (CLTV) and BIP-112 (CSV)
    assert (ScriptVerificationFlags.CHECKLOCKTIMEVERIFY.value & 0x200) == 0x200
    assert (ScriptVerificationFlags.CHECKSEQUENCEVERIFY.value & 0x400) == 0x400

    # BIP-141 (Segregated Witness, 2017)
    assert (ScriptVerificationFlags.WITNESS.value & 0x800) == 0x800

    # Modern Core (BIP-341 Taproot / ALL)
    assert ScriptVerificationFlags.ALL.value >= 0x20e15


def test_satoshi_p2pk_script_construction():
    """
    Validates that a canonical 2009 Satoshi P2PK script is correctly recognized
    and parsed into a ScriptPubkey object of exactly 67 bytes.
    """
    spk = ScriptPubkey(bytes.fromhex(GENESIS_P2PK_SCRIPT_HEX))
    raw_spk = bytes(spk)

    assert len(raw_spk) == 67
    assert raw_spk[0] == 0x41  # OP_PUSHBYTES_65
    assert raw_spk[-1] == 0xAC  # OP_CHECKSIG
    assert raw_spk[1:66].hex() == GENESIS_PUBKEY_HEX


def test_bip66_strict_der_signature_differential():
    """
    Audits BIP-66 consensus enforcement in libbitcoinkernel:
    1. Canonical DER signature is VALID under both pre-BIP66 (P2SH) and post-BIP66 (P2SH | DERSIG).
    2. Non-strict BER signature (with redundant 0x00 zero-padding on positive R integer)
       is VALID under pre-BIP66 flags (OpenSSL compatibility mode) and deterministically
       INVALID under post-BIP66 flags (DERSIG).
    """
    spk = ScriptPubkey(bytes.fromhex(PREV_SPK_P2PK_HEX))

    # 1. Canonical DER transaction
    tx_canonical = Transaction(bytes.fromhex(CANONICAL_TX_HEX))

    # 2. Mutate signature in scriptSig: replace canonical DER "48 47 30 44 02 20 38ea"
    #    with non-strict BER "49 48 30 45 02 21 00 38ea" (redundant 0x00 pad on R)
    ber_malleated_hex = CANONICAL_TX_HEX.replace(
        "48473044022038ea", "4948304502210038ea", 1
    )
    tx_non_strict_ber = Transaction(bytes.fromhex(ber_malleated_hex))

    flags_pre_bip66 = ScriptVerificationFlags.P2SH
    flags_post_bip66 = ScriptVerificationFlags.P2SH | ScriptVerificationFlags.DERSIG

    # Canonical signature MUST be valid across all eras
    assert spk.verify(PREV_OUT_VALUE_SATS, tx_canonical, None, 0, flags_pre_bip66) == 1
    assert spk.verify(PREV_OUT_VALUE_SATS, tx_canonical, None, 0, flags_post_bip66) == 1

    # Non-strict BER signature MUST pass under pre-BIP66 and fail under post-BIP66 (DERSIG)
    assert spk.verify(PREV_OUT_VALUE_SATS, tx_non_strict_ber, None, 0, flags_pre_bip66) == 1
    assert spk.verify(PREV_OUT_VALUE_SATS, tx_non_strict_ber, None, 0, flags_post_bip66) == 0


def test_cve_2010_5139_integer_overflow_rejected():
    """
    Validates that a synthetic transaction attempting the CVE-2010-5139 signed int64
    overflow exploit (two outputs of 92.233 billion BTC overflowing the 64-bit sum)
    is rejected unconditionally by libbitcoinkernel during Block.check().
    """
    cp = ChainParameters(ChainType.MAINNET).consensus_params

    # Two outputs of 9,223,372,036,854,277,039 sats (0x7ffffffffff868af)
    out1_sats = 9_223_372_036_854_277_039
    out2_sats = 9_223_372_036_854_277_039

    tx_cve_bytes = (
        bytes.fromhex(
            "01000000"
            "01"
            "3ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a"
            "00000000"
            "0151"
            "ffffffff"
            "02"
        )
        + struct.pack("<q", out1_sats)
        + bytes.fromhex("0151")
        + struct.pack("<q", out2_sats)
        + bytes.fromhex("015100000000")
    )

    # Embed transaction into Block #1 template (header + 2 transactions: coinbase + cve_tx)
    b1_raw = bytes.fromhex(BLOCK1_FULL_HEX)
    raw_cve_block = b1_raw[:80] + b"\x02" + b1_raw[81:] + tx_cve_bytes

    blk_cve = Block(raw_cve_block)
    state = blk_cve.check(cp, BlockCheckFlags(0))

    # libbitcoinkernel MUST flag this block as INVALID due to consensus violation
    assert state.validation_mode == ValidationMode.INVALID
    assert state.block_validation_result == BlockValidationResult.CONSENSUS


def test_block_structure_and_merkle_validation():
    """
    Validates Block.check() on canonical Block #1 vs mutated block structures:
    1. Canonical Block #1 is VALID under BlockCheckFlags.ALL.
    2. Mutated Merkle root in header is flagged as INVALID with INVALID_HEADER.
    3. Block with 0 transactions is flagged as INVALID with MUTATED.
    """
    cp = ChainParameters(ChainType.MAINNET).consensus_params
    b1_raw = bytes.fromhex(BLOCK1_FULL_HEX)

    # 1. Canonical Block #1 MUST pass
    blk_canon = Block(b1_raw)
    st_canon = blk_canon.check(cp, BlockCheckFlags.ALL)
    assert st_canon.validation_mode == ValidationMode.VALID
    assert st_canon.block_validation_result == BlockValidationResult.UNSET

    # 2. Corrupt Merkle root (header bytes 36..68)
    b1_bad_merkle = b1_raw[:36] + b"\xff" * 32 + b1_raw[68:]
    blk_bad_merkle = Block(b1_bad_merkle)
    st_bad_merkle = blk_bad_merkle.check(cp, BlockCheckFlags.ALL)
    assert st_bad_merkle.validation_mode == ValidationMode.INVALID
    assert st_bad_merkle.block_validation_result == BlockValidationResult.INVALID_HEADER

    # 3. Truncated block with 0 transactions (header + 0x00 tx_count)
    b1_no_txs = b1_raw[:80] + b"\x00"
    blk_no_txs = Block(b1_no_txs)
    st_no_txs = blk_no_txs.check(cp, BlockCheckFlags.ALL)
    assert st_no_txs.validation_mode == ValidationMode.INVALID
    assert st_no_txs.block_validation_result == BlockValidationResult.MUTATED


def test_chainstate_manager_header_connection(tmp_path):
    """
    Spins up an isolated ChainstateManager in tmp_path, anchors on Mainnet Genesis,
    processes Block #1 header with valid Proof-of-Work, and verifies chain tip advancement.
    """
    chainman = load_chainman(str(tmp_path), chain_type=ChainType.MAINNET)

    h1 = BlockHeader(bytes.fromhex(BLOCK1_HEADER_HEX))
    state = chainman.process_block_header(h1)

    assert state.validation_mode.name == "VALID"
    assert chainman.best_entry.height == 1


def test_orphan_block_header_rejected(tmp_path):
    """
    Verifies that passing a disconnected block header (Block #281) whose parent hash
    does not exist in the active chain is immediately caught and rejected by
    libbitcoinkernel raising ProcessBlockHeaderException.
    """
    chainman = load_chainman(str(tmp_path), chain_type=ChainType.MAINNET)

    # Attempt to process Block #281 directly without parent blocks #1-#280
    h281 = BlockHeader(bytes.fromhex(BLOCK281_HEADER_HEX))

    with pytest.raises(ProcessBlockHeaderException):
        chainman.process_block_header(h281)
