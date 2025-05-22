// Copyright (c) 2024-present The Bitcoin Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef BITCOIN_KERNEL_BITCOINKERNEL_HPP
#define BITCOIN_KERNEL_BITCOINKERNEL_HPP

#include <consensus/amount.h>
#include <kernel/logging_types.h>    // IWYU pragma: keep
#include <kernel/script_flags.h>     // IWYU pragma: keep
#include <kernel/types.h>            // IWYU pragma: keep
#include <kernel/validation_state.h> // IWYU pragma: keep
#include <kernel/warning.h>          // IWYU pragma: keep
#include <util/chaintype.h>          // IWYU pragma: keep

#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

#ifndef BITCOINKERNEL_API
#if defined(_WIN32)
#ifdef BITCOINKERNEL_BUILD
#define BITCOINKERNEL_API __declspec(dllexport)
#else
#define BITCOINKERNEL_API
#endif
#elif defined(__GNUC__) && (__GNUC__ >= 4) && defined(BITCOINKERNEL_BUILD)
#define BITCOINKERNEL_API __attribute__((visibility("default")))
#else
#define BITCOINKERNEL_API
#endif
#endif

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4251) // Suppress C4251 for STL members (e.g. std::unique_ptr) in exported classes
#endif

namespace kernel_header {

class TransactionOutput;

class BITCOINKERNEL_API Transaction
{
private:
    struct TransactionImpl;
    std::unique_ptr<TransactionImpl> m_impl;

public:
    explicit Transaction(std::span<const unsigned char> raw_transaction) noexcept;
    ~Transaction();

    /** Check whether this Transaction object is valid. */
    explicit operator bool() const noexcept { return bool{m_impl}; }

    friend class ScriptPubkey;
};

class BITCOINKERNEL_API ScriptPubkey
{
private:
    struct ScriptPubkeyImpl;
    std::unique_ptr<ScriptPubkeyImpl> m_impl;

public:
    explicit ScriptPubkey(std::span<const unsigned char> script_pubkey) noexcept;
    explicit ScriptPubkey(std::unique_ptr<ScriptPubkeyImpl> impl) noexcept;
    ~ScriptPubkey();

    ScriptPubkey(ScriptPubkey&& other) noexcept;

    /** Check whether this ScriptPubkey object is valid. */
    explicit operator bool() const noexcept { return bool{m_impl}; }

    std::vector<unsigned char> GetScriptPubkeyData() const noexcept;

    int VerifyScript(
        const CAmount amount,
        const Transaction& tx_to,
        std::span<const TransactionOutput> spent_outputs,
        const unsigned int input_index,
        const unsigned int flags) const noexcept;

    friend class TransactionOutput;
};

class BITCOINKERNEL_API TransactionOutput
{
private:
    struct TransactionOutputImpl;
    std::unique_ptr<TransactionOutputImpl> m_impl;

public:
    explicit TransactionOutput(const ScriptPubkey& script_pubkey, int64_t amount) noexcept;
    explicit TransactionOutput(std::unique_ptr<TransactionOutputImpl> impl) noexcept;
    ~TransactionOutput();

    TransactionOutput(TransactionOutput&& other) noexcept;
    TransactionOutput& operator=(TransactionOutput&& other) noexcept;

    ScriptPubkey GetScriptPubkey() const noexcept;

    int64_t GetOutputAmount() const noexcept;

    /** Check whether this TransactionOutput object is valid. */
    explicit operator bool() const noexcept { return bool{m_impl}; }

    friend class ScriptPubkey;
    friend class BlockUndo;
};

BITCOINKERNEL_API void AddLogLevelCategory(const BCLog::LogFlags category, const BCLog::Level level);

BITCOINKERNEL_API void EnableLogCategory(const BCLog::LogFlags category);

BITCOINKERNEL_API void DisableLogCategory(const BCLog::LogFlags category);

BITCOINKERNEL_API void DisableLogging();

BITCOINKERNEL_API void SetLogAlwaysPrintCategoryLevel(bool log_always_print_category_level);

BITCOINKERNEL_API void SetLogTimestamps(bool log_timestamps);

BITCOINKERNEL_API void SetLogTimeMicros(bool log_time_micros);

BITCOINKERNEL_API void SetLogThreadnames(bool log_threadnames);

BITCOINKERNEL_API void SetLogSourcelocations(bool log_sourcelocations);

class BITCOINKERNEL_API Logger
{
private:
    struct LoggerImpl;
    std::unique_ptr<LoggerImpl> m_impl;

public:
    explicit Logger(std::function<void(std::string_view)> callback) noexcept;
    ~Logger();

    /** Check whether this Logger object is valid. */
    explicit operator bool() const noexcept { return bool{m_impl}; }
};

struct BITCOINKERNEL_API BlockHash {
    std::array<unsigned char, 32> hash;
};

class BITCOINKERNEL_API BlockIndex
{
private:
    struct BlockIndexImpl;
    std::unique_ptr<BlockIndexImpl> m_impl;

public:
    BlockIndex(std::unique_ptr<BlockIndexImpl>&& impl) noexcept;
    ~BlockIndex() noexcept;

    // It is permitted to copy a BlockIndex. Its data is always valid for as long as the object it was retrieved is valid.
    BlockIndex(const BlockIndex& other) noexcept;
    BlockIndex& operator=(const BlockIndex& other) noexcept;

    std::optional<BlockIndex> GetPreviousBlockIndex() const noexcept;

    int32_t GetHeight() const noexcept;

    BlockHash GetHash() const noexcept;

    /** Check whether this BlockIndex object is valid. */
    explicit operator bool() const noexcept { return bool{m_impl}; }

    friend class KernelNotifications;
    friend class ChainstateManager;
};

class BITCOINKERNEL_API KernelNotifications
{
private:
    struct KernelNotificationsImpl;
    std::unique_ptr<KernelNotificationsImpl> m_impl;

public:
    KernelNotifications() noexcept;
    virtual ~KernelNotifications() noexcept;

    virtual void BlockTipHandler(SynchronizationState state, BlockIndex index) {}

    virtual void HeaderTipHandler(SynchronizationState state, int64_t height, int64_t timestamp, bool presync) {}

    virtual void ProgressHandler(std::string_view title, int progress_percent, bool resume_possible) {}

    virtual void WarningSetHandler(kernel::Warning warning, std::string_view message) {}

    virtual void WarningUnsetHandler(kernel::Warning warning) {}

    virtual void FlushErrorHandler(std::string_view error) {}

    virtual void FatalErrorHandler(std::string_view error) {}

    friend class ContextOptions;
    friend class ChainstateManagerOptions;
};

class BITCOINKERNEL_API ChainParameters
{
private:
    struct ChainParametersImpl;
    std::unique_ptr<ChainParametersImpl> m_impl;

public:
    explicit ChainParameters(const ChainType chain_type) noexcept;
    ~ChainParameters() noexcept;

    friend class ContextOptions;
};

class BITCOINKERNEL_API UnownedBlock
{
private:
    struct UnownedBlockImpl;
    std::unique_ptr<UnownedBlockImpl> m_impl;

public:
    explicit UnownedBlock(std::unique_ptr<UnownedBlockImpl> impl) noexcept;
    ~UnownedBlock() noexcept;

    friend class ValidationInterface;

    std::vector<std::byte> GetBlockData() const noexcept;

    BlockHash GetHash() const noexcept;
};

class BITCOINKERNEL_API ValidationInterface
{
private:
    struct ValidationInterfaceImpl;
    std::unique_ptr<ValidationInterfaceImpl> m_impl;

public:
    explicit ValidationInterface() noexcept;
    virtual ~ValidationInterface() noexcept;

    virtual void BlockCheckedHandler(const UnownedBlock block, const BlockValidationState stateIn) {}

    friend class Context;
};

class BITCOINKERNEL_API ContextOptions
{
private:
    struct ContextOptionsImpl;
    std::unique_ptr<ContextOptionsImpl> m_impl;

public:
    explicit ContextOptions() noexcept;
    ~ContextOptions() noexcept;

    void SetChainParameters(const ChainParameters& chain_parameters) noexcept;

    void SetNotifications(std::shared_ptr<KernelNotifications> notifications) noexcept;

    void SetValidationInterface(std::shared_ptr<ValidationInterface> validation_interface) noexcept;

    friend class Context;
};

class BITCOINKERNEL_API Context
{
private:
    struct ContextImpl;
    std::unique_ptr<ContextImpl> m_impl;

public:
    explicit Context(const ContextOptions& opts) noexcept;
    Context() noexcept;
    ~Context() noexcept;

    /** Check whether this Context object is valid. */
    explicit operator bool() const noexcept { return bool{m_impl}; }

    bool Interrupt() noexcept;

    friend class ChainstateManagerOptions;
    friend class ChainstateManager;
};

class BITCOINKERNEL_API ChainstateManagerOptions
{
private:
    struct ChainstateManagerOptionsImpl;
    std::unique_ptr<ChainstateManagerOptionsImpl> m_impl;

public:
    explicit ChainstateManagerOptions(const Context& context, const std::string& data_dir, const std::string& blocks_dir) noexcept;
    ~ChainstateManagerOptions() noexcept;

    /** Check whether this ChainstateManagerOptions object is valid. */
    explicit operator bool() const noexcept { return bool{m_impl}; }

    void SetWorkerThreads(int worker_threads) const noexcept;

    bool SetWipeDbs(bool wipe_block_tree, bool wipe_chainstate) const noexcept;

    void SetBlockTreeDbInMemory(bool block_tree_db_in_memory) const noexcept;

    void SetChainstateDbInMemory(bool chainstate_db_in_memory) const noexcept;

    friend class ChainstateManager;
};

class BITCOINKERNEL_API Block
{
private:
    struct BlockImpl;
    std::unique_ptr<BlockImpl> m_impl;

public:
    explicit Block(const std::span<const unsigned char> raw_block) noexcept;
    explicit Block(std::unique_ptr<BlockImpl> impl) noexcept;
    ~Block() noexcept;

    Block(Block&& other) noexcept;

    std::vector<std::byte> GetBlockData() const noexcept;

    BlockHash GetHash() const noexcept;

    /** Check whether this Block object is valid. */
    explicit operator bool() const noexcept { return bool{m_impl}; }

    friend class ChainstateManager;
};

class BITCOINKERNEL_API BlockUndo
{
private:
    struct BlockUndoImpl;
    std::unique_ptr<BlockUndoImpl> m_impl;

public:
    const uint64_t m_size;

    explicit BlockUndo(std::unique_ptr<BlockUndoImpl> impl) noexcept;
    ~BlockUndo() noexcept;

    BlockUndo(BlockUndo&& other) noexcept;

    uint64_t GetTxOutSize(uint64_t index) const noexcept;

    TransactionOutput GetTxUndoPrevoutByIndex(uint64_t tx_undo_index, uint64_t tx_prevout_index) const noexcept;

    friend class ChainstateManager;
};

class BITCOINKERNEL_API ChainstateManager
{
private:
    struct ChainstateManagerImpl;
    std::unique_ptr<ChainstateManagerImpl> m_impl;
    const Context& m_context;

public:
    explicit ChainstateManager(const Context& context, const ChainstateManagerOptions& chainstatemanager_options) noexcept;
    ~ChainstateManager() noexcept;

    bool ImportBlocks(const std::span<const std::string> paths) const noexcept;

    bool ProcessBlock(const Block& block, bool& new_block) const noexcept;

    BlockIndex GetBlockIndexFromTip() const noexcept;

    BlockIndex GetBlockIndexFromGenesis() const noexcept;

    std::optional<BlockIndex> GetBlockIndexByHash(const BlockHash& block_hash) const noexcept;

    std::optional<BlockIndex> GetBlockIndexByHeight(int height) const noexcept;

    std::optional<BlockIndex> GetNextBlockIndex(const BlockIndex& block_index) const noexcept;

    std::optional<Block> ReadBlock(const BlockIndex& block_index) const noexcept;

    std::optional<BlockUndo> ReadBlockUndo(const BlockIndex& block_index) const noexcept;

    /** Check whether this ChainMan object is valid. */
    explicit operator bool() const noexcept { return m_impl != nullptr; }
};

} // namespace kernel_header

#ifdef _MSC_VER
#pragma warning(pop)
#endif

#endif // BITCOIN_KERNEL_BITCOINKERNEL_HPP
