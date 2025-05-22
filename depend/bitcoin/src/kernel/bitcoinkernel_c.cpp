// Copyright (c) 2024 The Bitcoin Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <kernel/bitcoinkernel.h>

#include <kernel/bitcoinkernel.hpp>
#include <kernel/logging_types.h>
#include <kernel/types.h>
#include <kernel/validation_state.h>
#include <kernel/warning.h>
#include <util/chaintype.h>

#include <algorithm>
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <exception>
#include <functional>
#include <memory>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

using kernel_header::Block;
using kernel_header::BlockHash;
using kernel_header::BlockIndex;
using kernel_header::BlockUndo;
using kernel_header::ChainParameters;
using kernel_header::ChainstateManager;
using kernel_header::ChainstateManagerOptions;
using kernel_header::Context;
using kernel_header::ContextOptions;
using kernel_header::KernelNotifications;
using kernel_header::Logger;
using kernel_header::ScriptPubkey;
using kernel_header::Transaction;
using kernel_header::TransactionOutput;
using kernel_header::UnownedBlock;
using kernel_header::ValidationInterface;

using kernel_header::AddLogLevelCategory;
using kernel_header::DisableLogCategory;
using kernel_header::DisableLogging;
using kernel_header::EnableLogCategory;
using kernel_header::SetLogAlwaysPrintCategoryLevel;
using kernel_header::SetLogSourcelocations;
using kernel_header::SetLogThreadnames;
using kernel_header::SetLogTimeMicros;
using kernel_header::SetLogTimestamps;

namespace {

BCLog::Level get_bclog_level(const kernel_LogLevel level)
{
    switch (level) {
    case kernel_LogLevel::kernel_LOG_INFO: {
        return BCLog::Level::Info;
    }
    case kernel_LogLevel::kernel_LOG_DEBUG: {
        return BCLog::Level::Debug;
    }
    case kernel_LogLevel::kernel_LOG_TRACE: {
        return BCLog::Level::Trace;
    }
    } // no default case, so the compiler can warn about missing cases
    assert(false);
}

BCLog::LogFlags get_bclog_flag(const kernel_LogCategory category)
{
    switch (category) {
    case kernel_LogCategory::kernel_LOG_BENCH: {
        return BCLog::LogFlags::BENCH;
    }
    case kernel_LogCategory::kernel_LOG_BLOCKSTORAGE: {
        return BCLog::LogFlags::BLOCKSTORAGE;
    }
    case kernel_LogCategory::kernel_LOG_COINDB: {
        return BCLog::LogFlags::COINDB;
    }
    case kernel_LogCategory::kernel_LOG_LEVELDB: {
        return BCLog::LogFlags::LEVELDB;
    }
    case kernel_LogCategory::kernel_LOG_MEMPOOL: {
        return BCLog::LogFlags::MEMPOOL;
    }
    case kernel_LogCategory::kernel_LOG_PRUNE: {
        return BCLog::LogFlags::PRUNE;
    }
    case kernel_LogCategory::kernel_LOG_RAND: {
        return BCLog::LogFlags::RAND;
    }
    case kernel_LogCategory::kernel_LOG_REINDEX: {
        return BCLog::LogFlags::REINDEX;
    }
    case kernel_LogCategory::kernel_LOG_VALIDATION: {
        return BCLog::LogFlags::VALIDATION;
    }
    case kernel_LogCategory::kernel_LOG_KERNEL: {
        return BCLog::LogFlags::KERNEL;
    }
    case kernel_LogCategory::kernel_LOG_ALL: {
        return BCLog::LogFlags::ALL;
    }
    } // no default case, so the compiler can warn about missing cases
    assert(false);
}

ChainType get_chain_type(kernel_ChainType chain_type)


{
    switch (chain_type) {
    case kernel_ChainType::kernel_CHAIN_TYPE_MAINNET: {
        return ChainType::MAIN;
    }
    case kernel_ChainType::kernel_CHAIN_TYPE_TESTNET: {
        return ChainType::TESTNET;
    }
    case kernel_ChainType::kernel_CHAIN_TYPE_TESTNET_4: {
        return ChainType::TESTNET4;
    }
    case kernel_ChainType::kernel_CHAIN_TYPE_SIGNET: {
        return ChainType::SIGNET;
    }
    case kernel_ChainType::kernel_CHAIN_TYPE_REGTEST: {
        return ChainType::REGTEST;
    }
    } // no default case, so the compiler can warn about missing cases
    assert(false);
}

kernel_SynchronizationState cast_state(SynchronizationState state)
{
    switch (state) {
    case SynchronizationState::INIT_REINDEX:
        return kernel_SynchronizationState::kernel_INIT_REINDEX;
    case SynchronizationState::INIT_DOWNLOAD:
        return kernel_SynchronizationState::kernel_INIT_DOWNLOAD;
    case SynchronizationState::POST_INIT:
        return kernel_SynchronizationState::kernel_POST_INIT;
    } // no default case, so the compiler can warn about missing cases
    assert(false);
}

kernel_Warning cast_kernel_warning(kernel::Warning warning)
{
    switch (warning) {
    case kernel::Warning::UNKNOWN_NEW_RULES_ACTIVATED:
        return kernel_Warning::kernel_LARGE_WORK_INVALID_CHAIN;
    case kernel::Warning::LARGE_WORK_INVALID_CHAIN:
        return kernel_Warning::kernel_LARGE_WORK_INVALID_CHAIN;
    } // no default case, so the compiler can warn about missing cases
    assert(false);
}

const Transaction* cast_transaction(const kernel_Transaction* transaction)
{
    assert(transaction);
    return reinterpret_cast<const Transaction*>(transaction);
}

const ScriptPubkey* cast_script_pubkey(const kernel_ScriptPubkey* script_pubkey)
{
    assert(script_pubkey);
    return reinterpret_cast<const ScriptPubkey*>(script_pubkey);
}

const TransactionOutput* cast_transaction_output(const kernel_TransactionOutput* transaction_output)
{
    assert(transaction_output);
    return reinterpret_cast<const TransactionOutput*>(transaction_output);
}

Logger* cast_logger(kernel_LoggingConnection* logging_connection)
{
    assert(logging_connection);
    return reinterpret_cast<Logger*>(logging_connection);
}

const ContextOptions* cast_const_context_options(const kernel_ContextOptions* options)
{
    assert(options);
    return reinterpret_cast<const ContextOptions*>(options);
}

ContextOptions* cast_context_options(kernel_ContextOptions* options)
{
    assert(options);
    return reinterpret_cast<ContextOptions*>(options);
}

const ChainParameters* cast_const_chain_params(const kernel_ChainParameters* chain_params)
{
    assert(chain_params);
    return reinterpret_cast<const ChainParameters*>(chain_params);
}

ChainParameters* cast_chain_params(kernel_ChainParameters* chain_params)
{
    assert(chain_params);
    return reinterpret_cast<ChainParameters*>(chain_params);
}

Context* cast_context(kernel_Context* context)
{
    assert(context);
    return reinterpret_cast<Context*>(context);
}

const Context* cast_const_context(const kernel_Context* context)
{
    assert(context);
    return reinterpret_cast<const Context*>(context);
}

const ChainstateManagerOptions* cast_const_chainstate_manager_options(const kernel_ChainstateManagerOptions* options)
{
    assert(options);
    return reinterpret_cast<const ChainstateManagerOptions*>(options);
}

ChainstateManagerOptions* cast_chainstate_manager_options(kernel_ChainstateManagerOptions* options)
{
    assert(options);
    return reinterpret_cast<ChainstateManagerOptions*>(options);
}

ChainstateManager* cast_chainstate_manager(kernel_ChainstateManager* chainman)
{
    assert(chainman);
    return reinterpret_cast<ChainstateManager*>(chainman);
}

Block* cast_block(kernel_Block* block)
{
    assert(block);
    return reinterpret_cast<Block*>(block);
}

const BlockValidationState* cast_block_validation_state(const kernel_BlockValidationState* block_validation_state)
{
    assert(block_validation_state);
    return reinterpret_cast<const BlockValidationState*>(block_validation_state);
}

const UnownedBlock* cast_const_block(const kernel_BlockPointer* block)
{
    assert(block);
    return reinterpret_cast<const UnownedBlock*>(block);
}

const BlockIndex* cast_const_block_index(const kernel_BlockIndex* index)
{
    assert(index);
    return reinterpret_cast<const BlockIndex*>(index);
}

const BlockUndo* cast_const_block_undo(const kernel_BlockUndo* undo)
{
    assert(undo);
    return reinterpret_cast<const BlockUndo*>(undo);
}

BlockUndo* cast_block_undo(kernel_BlockUndo* undo)
{
    assert(undo);
    return reinterpret_cast<BlockUndo*>(undo);
}

class CallbackKernelNotifications : public KernelNotifications
{
private:
    kernel_NotificationInterfaceCallbacks m_cbs;

public:
    CallbackKernelNotifications(kernel_NotificationInterfaceCallbacks cbs)
        : m_cbs{cbs}
    {
    }

    void BlockTipHandler(SynchronizationState state, BlockIndex index) override
    {
        if (m_cbs.block_tip) m_cbs.block_tip((void*)m_cbs.user_data, cast_state(state), reinterpret_cast<const kernel_BlockIndex*>(&index));
    }
    void HeaderTipHandler(SynchronizationState state, int64_t height, int64_t timestamp, bool presync) override
    {
        if (m_cbs.header_tip) m_cbs.header_tip((void*)m_cbs.user_data, cast_state(state), height, timestamp, presync);
    }
    void ProgressHandler(std::string_view title, int progress_percent, bool resume_possible) override
    {
        if (m_cbs.progress) m_cbs.progress((void*)m_cbs.user_data, title.data(), title.length(), progress_percent, resume_possible);
    }
    void WarningSetHandler(kernel::Warning id, const std::string_view message) override
    {
        if (m_cbs.warning_set) m_cbs.warning_set((void*)m_cbs.user_data, cast_kernel_warning(id), message.data(), message.length());
    }
    void WarningUnsetHandler(kernel::Warning id) override
    {
        if (m_cbs.warning_unset) m_cbs.warning_unset((void*)m_cbs.user_data, cast_kernel_warning(id));
    }
    void FlushErrorHandler(std::string_view message) override
    {
        if (m_cbs.flush_error) m_cbs.flush_error((void*)m_cbs.user_data, message.data(), message.length());
    }
    void FatalErrorHandler(std::string_view message) override
    {
        if (m_cbs.fatal_error) m_cbs.fatal_error((void*)m_cbs.user_data, message.data(), message.length());
    }
};

class KernelValidationInterface : public ValidationInterface
{
public:
    const kernel_ValidationInterfaceCallbacks m_cbs;

    explicit KernelValidationInterface(const kernel_ValidationInterfaceCallbacks vi_cbs) : m_cbs{vi_cbs} {}

protected:
    void BlockCheckedHandler(const UnownedBlock block, const BlockValidationState stateIn) override
    {
        if (m_cbs.block_checked) {
            m_cbs.block_checked((void*)m_cbs.user_data,
                                reinterpret_cast<const kernel_BlockPointer*>(&block),
                                reinterpret_cast<const kernel_BlockValidationState*>(&stateIn));
        }
    }
};

} // namespace

kernel_Transaction* kernel_transaction_create(const unsigned char* raw_transaction, size_t raw_transaction_len)
{
    try {
        return reinterpret_cast<kernel_Transaction*>(new Transaction(std::span{raw_transaction, raw_transaction_len}));
    } catch (const std::exception&) {
        return nullptr;
    }
}

void kernel_transaction_destroy(kernel_Transaction* transaction)
{
    if (transaction) {
        delete cast_transaction(transaction);
    }
}

kernel_ScriptPubkey* kernel_script_pubkey_create(const unsigned char* script_pubkey, size_t script_pubkey_len)
{
    return reinterpret_cast<kernel_ScriptPubkey*>(new ScriptPubkey(std::span{script_pubkey, script_pubkey_len}));
}

kernel_ByteArray* kernel_copy_script_pubkey_data(const kernel_ScriptPubkey* script_pubkey_)
{
    auto script_pubkey{cast_script_pubkey(script_pubkey_)};

    auto data{script_pubkey->GetScriptPubkeyData()};

    auto byte_array{new kernel_ByteArray{
        .data = new unsigned char[data.size()],
        .size = data.size(),
    }};

    std::memcpy(byte_array->data, data.data(), byte_array->size);
    return byte_array;
}

void kernel_script_pubkey_destroy(kernel_ScriptPubkey* script_pubkey)
{
    if (script_pubkey) {
        delete cast_script_pubkey(script_pubkey);
    }
}

kernel_TransactionOutput* kernel_transaction_output_create(const kernel_ScriptPubkey* script_pubkey_, int64_t amount)
{
    const auto& script_pubkey{*cast_script_pubkey(script_pubkey_)};
    return reinterpret_cast<kernel_TransactionOutput*>(new TransactionOutput{script_pubkey, amount});
}

void kernel_transaction_output_destroy(kernel_TransactionOutput* output)
{
    if (output) {
        delete cast_transaction_output(output);
    }
}

bool kernel_verify_script(const kernel_ScriptPubkey* script_pubkey_,
                          const int64_t amount,
                          const kernel_Transaction* tx_to,
                          const kernel_TransactionOutput** spent_outputs_, size_t spent_outputs_len,
                          const unsigned int input_index,
                          const unsigned int flags)
{
    const auto& script_pubkey{*cast_script_pubkey(script_pubkey_)};
    const auto& tx{*cast_transaction(tx_to)};

    std::span<const TransactionOutput> spent_outputs;
    if (spent_outputs_ != nullptr) {
        const TransactionOutput* first_output{reinterpret_cast<const TransactionOutput*>(*spent_outputs_)};
        spent_outputs = {first_output, spent_outputs_len};
    }

    return script_pubkey.VerifyScript(
        amount,
        tx,
        spent_outputs,
        input_index,
        flags);
}

void kernel_add_log_level_category(const kernel_LogCategory category, const kernel_LogLevel level)
{
    AddLogLevelCategory(get_bclog_flag(category), get_bclog_level(level));
}

void kernel_enable_log_category(const kernel_LogCategory category)
{
    EnableLogCategory(get_bclog_flag(category));
}

void kernel_disable_log_category(const kernel_LogCategory category)
{
    DisableLogCategory(get_bclog_flag(category));
}

void kernel_disable_logging()
{
    DisableLogging();
}

void kernel_set_log_always_print_category_level(bool log_always_print_category_level)
{
    SetLogAlwaysPrintCategoryLevel(log_always_print_category_level);
}

void kernel_set_log_timestamps(bool log_timestamps)
{
    SetLogTimestamps(log_timestamps);
}

void kernel_set_log_time_micros(bool log_time_micros)
{
    SetLogTimeMicros(log_time_micros);
}

void kerenl_set_log_threadname(bool log_threadnames)
{
    SetLogThreadnames(log_threadnames);
}

void kernel_set_log_sourcelocations(bool log_sourcelocations)
{
    SetLogSourcelocations(log_sourcelocations);
}

kernel_LoggingConnection* kernel_logging_connection_create(kernel_LogCallback callback, void* user_data)
{
    auto logger = new Logger([callback, user_data](std::string_view message) { callback(user_data, message.data(), message.length()); });
    return reinterpret_cast<kernel_LoggingConnection*>(logger);
}

void kernel_logging_connection_destroy(kernel_LoggingConnection* logging_connection)
{
    if (logging_connection) {
        delete cast_logger(logging_connection);
    }
}

kernel_ChainParameters* kernel_chain_parameters_create(const kernel_ChainType chain_type)
{
    return reinterpret_cast<kernel_ChainParameters*>(new ChainParameters(get_chain_type(chain_type)));
}

void kernel_chain_parameters_destroy(kernel_ChainParameters* chain_parameters)
{
    if (chain_parameters) {
        delete cast_chain_params(chain_parameters);
    }
}

kernel_ContextOptions* kernel_context_options_create()
{
    return reinterpret_cast<kernel_ContextOptions*>(new ContextOptions{});
}

void kernel_context_options_set_chainparams(kernel_ContextOptions* options_, const kernel_ChainParameters* chain_parameters)
{
    auto options{cast_context_options(options_)};
    auto chain_params{cast_const_chain_params(chain_parameters)};
    options->SetChainParameters(*chain_params);
}

void kernel_context_options_set_notifications(kernel_ContextOptions* options_, kernel_NotificationInterfaceCallbacks notifications)
{
    auto options{cast_context_options(options_)};
    options->SetNotifications(std::make_shared<CallbackKernelNotifications>(notifications));
}

void kernel_context_options_set_validation_interface(kernel_ContextOptions* options_, kernel_ValidationInterfaceCallbacks vi_cbs)
{
    auto options{cast_context_options(options_)};
    options->SetValidationInterface(std::make_shared<KernelValidationInterface>(vi_cbs));
}

void kernel_context_options_destroy(kernel_ContextOptions* options)
{
    if (options) {
        delete cast_context_options(options);
    }
}

kernel_Context* kernel_context_create(const kernel_ContextOptions* options_)
{
    auto options{cast_const_context_options(options_)};
    Context* context{nullptr};
    if (!options) {
        context = new Context{};
    } else {
        context = new Context{*options};
    }
    return reinterpret_cast<kernel_Context*>(context);
}

bool kernel_context_interrupt(kernel_Context* context_)
{
    auto& context{*cast_context(context_)};
    return context.Interrupt();
}

void kernel_context_destroy(kernel_Context* context_)
{
    delete cast_context(context_);
}

kernel_ValidationMode kernel_get_validation_mode_from_block_validation_state(const kernel_BlockValidationState* block_validation_state_)
{
    auto& block_validation_state = *cast_block_validation_state(block_validation_state_);
    if (block_validation_state.IsValid()) return kernel_ValidationMode::kernel_VALIDATION_STATE_VALID;
    if (block_validation_state.IsInvalid()) return kernel_ValidationMode::kernel_VALIDATION_STATE_INVALID;
    return kernel_ValidationMode::kernel_VALIDATION_STATE_ERROR;
}

kernel_BlockValidationResult kernel_get_block_validation_result_from_block_validation_state(const kernel_BlockValidationState* block_validation_state_)
{
    auto& block_validation_state = *cast_block_validation_state(block_validation_state_);

    switch (block_validation_state.GetResult()) {
    case BlockValidationResult::BLOCK_RESULT_UNSET:
        return kernel_BlockValidationResult::kernel_BLOCK_RESULT_UNSET;
    case BlockValidationResult::BLOCK_CONSENSUS:
        return kernel_BlockValidationResult::kernel_BLOCK_CONSENSUS;
    case BlockValidationResult::BLOCK_CACHED_INVALID:
        return kernel_BlockValidationResult::kernel_BLOCK_CACHED_INVALID;
    case BlockValidationResult::BLOCK_INVALID_HEADER:
        return kernel_BlockValidationResult::kernel_BLOCK_INVALID_HEADER;
    case BlockValidationResult::BLOCK_MUTATED:
        return kernel_BlockValidationResult::kernel_BLOCK_MUTATED;
    case BlockValidationResult::BLOCK_MISSING_PREV:
        return kernel_BlockValidationResult::kernel_BLOCK_MISSING_PREV;
    case BlockValidationResult::BLOCK_INVALID_PREV:
        return kernel_BlockValidationResult::kernel_BLOCK_INVALID_PREV;
    case BlockValidationResult::BLOCK_TIME_FUTURE:
        return kernel_BlockValidationResult::kernel_BLOCK_TIME_FUTURE;
    case BlockValidationResult::BLOCK_HEADER_LOW_WORK:
        return kernel_BlockValidationResult::kernel_BLOCK_HEADER_LOW_WORK;
    } // no default case, so the compiler can warn about missing cases
    assert(false);
}

kernel_ChainstateManagerOptions* kernel_chainstate_manager_options_create(const kernel_Context* context_, const char* data_dir, size_t data_dir_len, const char* blocks_dir, size_t blocks_dir_len)
{
    std::string data_dir_str{data_dir, data_dir_len};
    std::string blocks_dir_str{blocks_dir, blocks_dir_len};
    auto context{cast_const_context(context_)};
    auto chainman_opts{new ChainstateManagerOptions(*context, data_dir_str, blocks_dir_str)};
    if (!*chainman_opts) {
        return nullptr;
    }
    return reinterpret_cast<kernel_ChainstateManagerOptions*>(chainman_opts);
}

void kernel_chainstate_manager_options_set_worker_threads_num(kernel_ChainstateManagerOptions* opts_, int worker_threads)
{
    auto opts{cast_chainstate_manager_options(opts_)};
    opts->SetWorkerThreads(worker_threads);
}

bool kernel_chainstate_manager_options_set_wipe_dbs(kernel_ChainstateManagerOptions* chainman_opts_, bool wipe_block_tree_db, bool wipe_chainstate_db)
{
    auto opts{cast_chainstate_manager_options(chainman_opts_)};
    return opts->SetWipeDbs(wipe_block_tree_db, wipe_chainstate_db);
}


void kernel_chainstate_manager_options_set_block_tree_db_in_memory(
    kernel_ChainstateManagerOptions* chainstate_load_opts_,
    bool block_tree_db_in_memory)
{
    auto opts{cast_chainstate_manager_options(chainstate_load_opts_)};
    opts->SetBlockTreeDbInMemory(block_tree_db_in_memory);
}

void kernel_chainstate_manager_options_set_chainstate_db_in_memory(
    kernel_ChainstateManagerOptions* chainstate_load_opts_,
    bool chainstate_db_in_memory)
{
    auto opts{cast_chainstate_manager_options(chainstate_load_opts_)};
    opts->SetChainstateDbInMemory(chainstate_db_in_memory);
}

void kernel_chainstate_manager_options_destroy(kernel_ChainstateManagerOptions* options)
{
    if (options) {
        delete cast_chainstate_manager_options(options);
    }
}

kernel_ChainstateManager* kernel_chainstate_manager_create(
    const kernel_Context* context_,
    const kernel_ChainstateManagerOptions* chainman_opts_)
{
    auto chainman_opts{cast_const_chainstate_manager_options(chainman_opts_)};
    auto context{cast_const_context(context_)};

    auto chainman{new ChainstateManager(*context, *chainman_opts)};

    if (!*chainman) {
        return nullptr;
    }
    return reinterpret_cast<kernel_ChainstateManager*>(chainman);
}

void kernel_chainstate_manager_destroy(kernel_ChainstateManager* chainman_, const kernel_Context* context_)
{
    if (!chainman_) return;
    delete cast_chainstate_manager(chainman_);
}

kernel_Block* kernel_block_create(const unsigned char* raw_block, size_t raw_block_length)
{
    auto block = new Block{std::span{raw_block, raw_block_length}};
    if (!*block) {
        delete block;
        return nullptr;
    }

    return reinterpret_cast<kernel_Block*>(block);
}

void kernel_byte_array_destroy(kernel_ByteArray* byte_array)
{
    if (byte_array && byte_array->data) delete[] byte_array->data;
    if (byte_array) delete byte_array;
}

kernel_ByteArray* kernel_copy_block_data(kernel_Block* block_)
{
    auto block{cast_block(block_)};

    std::vector<std::byte> ser_block{block->GetBlockData()};

    auto byte_array{new kernel_ByteArray{
        .data = new unsigned char[ser_block.size()],
        .size = ser_block.size(),
    }};

    std::memcpy(byte_array->data, ser_block.data(), byte_array->size);

    return byte_array;
}

kernel_ByteArray* kernel_copy_block_pointer_data(const kernel_BlockPointer* block_)
{
    auto block{cast_const_block(block_)};

    std::vector<std::byte> ser_block{block->GetBlockData()};

    auto byte_array{new kernel_ByteArray{
        .data = new unsigned char[ser_block.size()],
        .size = ser_block.size(),
    }};

    std::memcpy(byte_array->data, ser_block.data(), byte_array->size);

    return byte_array;
}

kernel_BlockHash* kernel_block_get_hash(kernel_Block* block_)
{
    Block* block{cast_block(block_)};
    auto kernel_hash{new kernel_BlockHash{.hash = {0}}};
    auto hash{block->GetHash()};
    std::copy(hash.hash.begin(), hash.hash.end(), kernel_hash->hash);
    return kernel_hash;
}

kernel_BlockHash* kernel_block_pointer_get_hash(const kernel_BlockPointer* block_)
{
    const UnownedBlock* block{cast_const_block(block_)};
    auto kernel_hash{new kernel_BlockHash{.hash = {0}}};
    auto hash{block->GetHash()};
    std::copy(hash.hash.begin(), hash.hash.end(), kernel_hash->hash);
    return kernel_hash;
}

void kernel_block_destroy(kernel_Block* block)
{
    if (block) {
        delete cast_block(block);
    }
}

bool kernel_import_blocks(const kernel_Context* context_,
                          kernel_ChainstateManager* chainman_,
                          const char** block_file_paths,
                          size_t* block_file_paths_lens,
                          size_t block_file_paths_len)
{
    auto chainman{cast_chainstate_manager(chainman_)};
    std::vector<std::string> import_files;
    import_files.reserve(block_file_paths_len);
    for (uint32_t i = 0; i < block_file_paths_len; i++) {
        if (block_file_paths[i] != nullptr) {
            import_files.emplace_back(block_file_paths[i], block_file_paths_lens[i]);
        }
    }
    return chainman->ImportBlocks(import_files);
}

kernel_BlockIndex* kernel_get_block_index_from_tip(const kernel_Context* context_, kernel_ChainstateManager* chainman_)
{
    auto chainman{cast_chainstate_manager(chainman_)};
    auto block_index = new BlockIndex(chainman->GetBlockIndexFromTip());
    if (!*block_index) return nullptr;
    return reinterpret_cast<kernel_BlockIndex*>(block_index);
}

kernel_BlockIndex* kernel_get_block_index_from_genesis(const kernel_Context* context_, kernel_ChainstateManager* chainman_)
{
    auto chainman{cast_chainstate_manager(chainman_)};
    return reinterpret_cast<kernel_BlockIndex*>(new BlockIndex(chainman->GetBlockIndexFromGenesis()));
}

kernel_BlockIndex* kernel_get_block_index_from_hash(const kernel_Context* context_, kernel_ChainstateManager* chainman_, kernel_BlockHash* block_hash)
{
    auto chainman{cast_chainstate_manager(chainman_)};
    BlockHash hash{.hash = std::to_array(block_hash->hash)};
    std::optional<BlockIndex> block_index{chainman->GetBlockIndexByHash(hash)};
    if (!block_index) {
        return nullptr;
    }
    return reinterpret_cast<kernel_BlockIndex*>(new BlockIndex(*block_index));
}

kernel_BlockIndex* kernel_get_block_index_from_height(const kernel_Context* context_, kernel_ChainstateManager* chainman_, int height)
{
    auto chainman{cast_chainstate_manager(chainman_)};
    std::optional<BlockIndex> block_index{chainman->GetBlockIndexByHeight(height)};
    if (!block_index) {
        return nullptr;
    }
    return reinterpret_cast<kernel_BlockIndex*>(new BlockIndex(*block_index));
}

kernel_BlockIndex* kernel_get_next_block_index(const kernel_Context* context_, kernel_ChainstateManager* chainman_, const kernel_BlockIndex* block_index_)
{
    const auto block_index{cast_const_block_index(block_index_)};
    auto chainman{cast_chainstate_manager(chainman_)};

    std::optional<BlockIndex> next_block_index{chainman->GetNextBlockIndex(*block_index)};
    if (!next_block_index) {
        return nullptr;
    }
    return reinterpret_cast<kernel_BlockIndex*>(new BlockIndex(*next_block_index));
}

kernel_BlockIndex* kernel_get_previous_block_index(const kernel_BlockIndex* block_index_)
{
    const BlockIndex* block_index{cast_const_block_index(block_index_)};
    std::optional<BlockIndex> prev_block_index{block_index->GetPreviousBlockIndex()};

    if (!prev_block_index) {
        return nullptr;
    }

    return reinterpret_cast<kernel_BlockIndex*>(new BlockIndex(prev_block_index.value()));
}

kernel_Block* kernel_read_block_from_disk(const kernel_Context* context_,
                                          kernel_ChainstateManager* chainman_,
                                          const kernel_BlockIndex* block_index_)
{
    auto chainman{cast_chainstate_manager(chainman_)};
    const BlockIndex* block_index{cast_const_block_index(block_index_)};

    std::optional<Block> block{chainman->ReadBlock(*block_index)};

    if (!block) return nullptr;

    return reinterpret_cast<kernel_Block*>(new Block(std::move(*block)));
}

kernel_BlockUndo* kernel_read_block_undo_from_disk(const kernel_Context* context_,
                                                   kernel_ChainstateManager* chainman_,
                                                   const kernel_BlockIndex* block_index_)
{
    auto chainman{cast_chainstate_manager(chainman_)};
    const auto block_index{cast_const_block_index(block_index_)};

    std::optional<BlockUndo> block_undo{chainman->ReadBlockUndo(*block_index)};
    if (!block_undo) return nullptr;

    return reinterpret_cast<kernel_BlockUndo*>(new BlockUndo(std::move(*block_undo)));
}

void kernel_block_index_destroy(kernel_BlockIndex* block_index)
{
    if (block_index) {
        delete reinterpret_cast<BlockIndex*>(block_index);
    }
}


uint64_t kernel_block_undo_size(const kernel_BlockUndo* block_undo_)
{
    const auto block_undo{cast_const_block_undo(block_undo_)};
    return block_undo->m_size;
}

void kernel_block_undo_destroy(kernel_BlockUndo* block_undo)
{
    if (block_undo) {
        delete cast_block_undo(block_undo);
    }
}

uint64_t kernel_get_transaction_undo_size(const kernel_BlockUndo* block_undo_, uint64_t transaction_undo_index)
{
    const auto block_undo{cast_const_block_undo(block_undo_)};
    return block_undo->GetTxOutSize(transaction_undo_index);
}

kernel_TransactionOutput* kernel_get_undo_output_by_index(const kernel_BlockUndo* block_undo_,
                                                          uint64_t transaction_undo_index,
                                                          uint64_t output_index)
{
    const auto block_undo{cast_const_block_undo(block_undo_)};

    TransactionOutput output = block_undo->GetTxUndoPrevoutByIndex(transaction_undo_index, output_index);
    if (!output) return nullptr;

    return reinterpret_cast<kernel_TransactionOutput*>(new TransactionOutput(std::move(output)));
}

int32_t kernel_block_index_get_height(const kernel_BlockIndex* block_index_)
{
    auto block_index{cast_const_block_index(block_index_)};
    return block_index->GetHeight();
}

kernel_BlockHash* kernel_block_index_get_block_hash(const kernel_BlockIndex* block_index_)
{
    auto block_index{cast_const_block_index(block_index_)};
    auto kernel_hash{new kernel_BlockHash{.hash = {0}}};
    auto hash{block_index->GetHash()};
    std::copy(hash.hash.begin(), hash.hash.end(), kernel_hash->hash);
    return kernel_hash;
}

void kernel_block_hash_destroy(kernel_BlockHash* hash)
{
    if (hash) delete hash;
}

kernel_ScriptPubkey* kernel_copy_script_pubkey_from_output(kernel_TransactionOutput* output_)
{
    auto output{cast_transaction_output(output_)};
    return reinterpret_cast<kernel_ScriptPubkey*>(new ScriptPubkey(output->GetScriptPubkey()));
}

int64_t kernel_get_transaction_output_amount(kernel_TransactionOutput* output_)
{
    auto output{cast_transaction_output(output_)};
    return output->GetOutputAmount();
}

bool kernel_chainstate_manager_process_block(
    const kernel_Context* context_,
    kernel_ChainstateManager* chainman_,
    kernel_Block* block_,
    bool* new_block)
{
    auto& chainman{*cast_chainstate_manager(chainman_)};

    auto block{cast_block(block_)};

    return chainman.ProcessBlock(*block, *new_block);
}
