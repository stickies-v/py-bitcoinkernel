#include <kernel/bitcoinkernel.hpp>

#include <kernel/validation_state.h>
#include <util/chaintype.h>

#include <cassert>
#include <cstddef>
#include <charconv>
#include <filesystem>
#include <functional>
#include <iostream>
#include <memory>
#include <span>
#include <string>
#include <string_view>
#include <system_error>
#include <vector>

enum class SynchronizationState;
namespace kernel { enum class Warning; }

using kernel_header::Block;
using kernel_header::BlockIndex;
using kernel_header::ChainParameters;
using kernel_header::ChainstateManager;
using kernel_header::ChainstateManagerOptions;
using kernel_header::Context;
using kernel_header::ContextOptions;
using kernel_header::KernelNotifications;
using kernel_header::Logger;
using kernel_header::UnownedBlock;
using kernel_header::ValidationInterface;

using kernel_header::SetLogAlwaysPrintCategoryLevel;
using kernel_header::SetLogSourcelocations;
using kernel_header::SetLogThreadnames;
using kernel_header::SetLogTimeMicros;
using kernel_header::SetLogTimestamps;

#ifdef WIN32
#include <windows.h>
#include <codecvt>
#include <shellapi.h>
#include <locale>
#endif

std::vector<unsigned char> hex_string_to_char_vec(std::string_view hex)
{
    std::vector<unsigned char> bytes;
    bytes.reserve(hex.length() / 2);

    for (size_t i{0}; i < hex.length(); i += 2) {
        unsigned char byte;
        auto [ptr, ec] = std::from_chars(hex.data() + i, hex.data() + i + 2, byte, 16);
        if (ec == std::errc{} && ptr == hex.data() + i + 2) {
            bytes.push_back(byte);
        }
    }
    return bytes;
}

class TestValidationInterface : public ValidationInterface
{
public:
    TestValidationInterface() : ValidationInterface() {}

    void BlockCheckedHandler(const UnownedBlock block, const BlockValidationState state) override
    {
        if (state.IsValid()) {
            std::cout << "Valid block" << std::endl;
            return;
        }

        if (state.IsError()) {
            std::cout << "Internal error" << std::endl;
            return;
        }

        std::cout << "Invalid block: ";
        auto result{state.GetResult()};
        switch (result) {
        case BlockValidationResult::BLOCK_RESULT_UNSET:
            std::cout << "initial value. Block has not yet been rejected" << std::endl;
            break;
        case BlockValidationResult::BLOCK_HEADER_LOW_WORK:
            std::cout << "the block header may be on a too-little-work chain" << std::endl;
            break;
        case BlockValidationResult::BLOCK_CONSENSUS:
            std::cout << "invalid by consensus rules (excluding any below reasons)" << std::endl;
            break;
        case BlockValidationResult::BLOCK_CACHED_INVALID:
            std::cout << "this block was cached as being invalid and we didn't store the reason why" << std::endl;
            break;
        case BlockValidationResult::BLOCK_INVALID_HEADER:
            std::cout << "invalid proof of work or time too old" << std::endl;
            break;
        case BlockValidationResult::BLOCK_MUTATED:
            std::cout << "the block's data didn't match the data committed to by the PoW" << std::endl;
            break;
        case BlockValidationResult::BLOCK_MISSING_PREV:
            std::cout << "We don't have the previous block the checked one is built on" << std::endl;
            break;
        case BlockValidationResult::BLOCK_INVALID_PREV:
            std::cout << "A block this one builds on is invalid" << std::endl;
            break;
        case BlockValidationResult::BLOCK_TIME_FUTURE:
            std::cout << "block timestamp was > 2 hours in the future (or our clock is bad)" << std::endl;
            break;
        }
    }
};

class TestKernelNotifications : public KernelNotifications
{
public:
    void BlockTipHandler(SynchronizationState state, const BlockIndex index) override
    {
        std::cout << "Block tip changed" << std::endl;
    }

    void ProgressHandler(std::string_view title, int progress_percent, bool resume_possible) override
    {
        std::cout << "Made progress: " << title << " " << progress_percent << "%" << std::endl;
    }

    void WarningSetHandler(kernel::Warning warning, std::string_view message) override
    {
        std::cout << message << std::endl;
    }

    void WarningUnsetHandler(kernel::Warning warning) override
    {
        std::cout << "Warning unset. " << std::endl;
    }

    void FlushErrorHandler(std::string_view error) override
    {
        std::cout << error << std::endl;
    }

    void FatalErrorHandler(std::string_view error) override
    {
        std::cout << error << std::endl;
    }
};

int main(int argc, char* argv[])
{
    // SETUP: Argument parsing and handling
    if (argc != 2) {
        std::cerr
            << "Usage: " << argv[0] << " DATADIR" << std::endl
            << "Display DATADIR information, and process hex-encoded blocks on standard input." << std::endl
            << std::endl
            << "IMPORTANT: THIS EXECUTABLE IS EXPERIMENTAL, FOR TESTING ONLY, AND EXPECTED TO" << std::endl
            << "           BREAK IN FUTURE VERSIONS. DO NOT USE ON YOUR ACTUAL DATADIR." << std::endl;
        return 1;
    }

#ifdef WIN32
    int win_argc;
    wchar_t** wargv = CommandLineToArgvW(GetCommandLineW(), &win_argc);
    std::vector<std::string> utf8_args(win_argc);
    std::vector<char*> win_argv(win_argc);
    std::wstring_convert<std::codecvt_utf8_utf16<wchar_t>, wchar_t> utf8_cvt;
    for (int i = 0; i < win_argc; i++) {
        utf8_args[i] = utf8_cvt.to_bytes(wargv[i]);
        win_argv[i] = &utf8_args[i][0];
    }
    LocalFree(wargv);
    argc = win_argc;
    argv = win_argv.data();
#endif

    std::filesystem::path abs_datadir{std::filesystem::absolute(argv[1])};
    std::filesystem::create_directories(abs_datadir);

    SetLogTimestamps(true);
    SetLogTimeMicros(false);
    SetLogThreadnames(false);
    SetLogSourcelocations(false);
    SetLogAlwaysPrintCategoryLevel(true);

    Logger logger{[](std::string_view message) { std::cout << "kernel: " << message; }};

    ContextOptions options{};
    ChainParameters params{ChainType::MAIN};
    options.SetChainParameters(params);

    auto notifications{std::make_shared<TestKernelNotifications>()};
    options.SetNotifications(notifications);
    auto validation_interface{std::make_shared<TestValidationInterface>()};
    options.SetValidationInterface(validation_interface);

    Context context{options};
    assert(context);

    ChainstateManagerOptions chainman_opts{context, abs_datadir.string(), (abs_datadir / "blocks").string()};
    assert(chainman_opts);
    chainman_opts.SetWorkerThreads(4);

    auto chainman{std::make_unique<ChainstateManager>(context, chainman_opts)};
    if (!*chainman) {
        return 1;
    }

    std::cout << "Enter the block you want to validate on the next line:" << std::endl;

    for (std::string line; std::getline(std::cin, line);) {
        if (line.empty()) {
            std::cerr << "Empty line found, try again:" << std::endl;
            continue;
        }

        auto raw_block{hex_string_to_char_vec(line)};
        auto block = Block{raw_block};
        if (!block) {
            std::cerr << "Block decode failed, try again:" << std::endl;
            continue;
        }

        bool new_block = false;
        bool accepted = chainman->ProcessBlock(block, new_block);
        if (accepted) {
            std::cerr << "Block has not yet been rejected" << std::endl;
        } else {
            std::cerr << "Block was not accepted" << std::endl;
        }
        if (!new_block) {
            std::cerr << "Block is a duplicate" << std::endl;
        }
    }
}
