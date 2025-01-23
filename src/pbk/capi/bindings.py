# -*- coding: utf-8 -*-
#
# TARGET arch is: []
# WORD_SIZE is: 8
# POINTER_SIZE is: 8
# LONGDOUBLE_SIZE is: 8
#
import ctypes
import ctypes.util
from pathlib import Path


def _find_bitcoinkernel_lib():
    # Check relative ../_libs/ directory
    script_dir = Path(__file__).parent
    if (matches := list((script_dir.parent / "_libs").glob("*bitcoinkernel*"))):
        if len(matches) == 1:
            return str(matches[0])
        raise RuntimeError(f"Found multiple libbitcoinkernel candidates: {matches}")
        
    raise RuntimeError(
        "Could not find libbitcoinkernel. Please re-run `pip install`."
    )

BITCOINKERNEL_LIB = ctypes.CDLL(_find_bitcoinkernel_lib())

class AsDictMixin:
    @classmethod
    def as_dict(cls, self):
        result = {}
        if not isinstance(self, AsDictMixin):
            # not a structure, assume it's already a python object
            return self
        if not hasattr(cls, "_fields_"):
            return result
        # sys.version_info >= (3, 5)
        # for (field, *_) in cls._fields_:  # noqa
        for field_tuple in cls._fields_:  # noqa
            field = field_tuple[0]
            if field.startswith('PADDING_'):
                continue
            value = getattr(self, field)
            type_ = type(value)
            if hasattr(value, "_length_") and hasattr(value, "_type_"):
                # array
                if not hasattr(type_, "as_dict"):
                    value = [v for v in value]
                else:
                    type_ = type_._type_
                    value = [type_.as_dict(v) for v in value]
            elif hasattr(value, "contents") and hasattr(value, "_type_"):
                # pointer
                try:
                    if not hasattr(type_, "as_dict"):
                        value = value.contents
                    else:
                        type_ = type_._type_
                        value = type_.as_dict(value.contents)
                except ValueError:
                    # nullptr
                    value = None
            elif isinstance(value, AsDictMixin):
                # other structure
                value = type_.as_dict(value)
            result[field] = value
        return result


class Structure(ctypes.Structure, AsDictMixin):

    def __init__(self, *args, **kwds):
        # We don't want to use positional arguments fill PADDING_* fields

        args = dict(zip(self.__class__._field_names_(), args))
        args.update(kwds)
        super(Structure, self).__init__(**args)

    @classmethod
    def _field_names_(cls):
        if hasattr(cls, '_fields_'):
            return (f[0] for f in cls._fields_ if not f[0].startswith('PADDING'))
        else:
            return ()

    @classmethod
    def get_type(cls, field):
        for f in cls._fields_:
            if f[0] == field:
                return f[1]
        return None

    @classmethod
    def bind(cls, bound_fields):
        fields = {}
        for name, type_ in cls._fields_:
            if hasattr(type_, "restype"):
                if name in bound_fields:
                    if bound_fields[name] is None:
                        fields[name] = type_()
                    else:
                        # use a closure to capture the callback from the loop scope
                        fields[name] = (
                            type_((lambda callback: lambda *args: callback(*args))(
                                bound_fields[name]))
                        )
                    del bound_fields[name]
                else:
                    # default callback implementation (does nothing)
                    try:
                        default_ = type_(0).restype().value
                    except TypeError:
                        default_ = None
                    fields[name] = type_((
                        lambda default_: lambda *args: default_)(default_))
            else:
                # not a callback function, use default initialization
                if name in bound_fields:
                    fields[name] = bound_fields[name]
                    del bound_fields[name]
                else:
                    fields[name] = type_()
        if len(bound_fields) != 0:
            raise ValueError(
                "Cannot bind the following unknown callback(s) {}.{}".format(
                    cls.__name__, bound_fields.keys()
            ))
        return cls(**fields)


class Union(ctypes.Union, AsDictMixin):
    pass



c_int128 = ctypes.c_ubyte*16
c_uint128 = c_int128
void = None
if ctypes.sizeof(ctypes.c_longdouble) == 8:
    c_long_double_t = ctypes.c_longdouble
else:
    c_long_double_t = ctypes.c_ubyte*8

def string_cast(char_pointer, encoding='utf-8', errors='strict'):
    value = ctypes.cast(char_pointer, ctypes.c_char_p).value
    if value is not None and encoding is not None:
        value = value.decode(encoding, errors=errors)
    return value


def char_pointer_cast(string, encoding='utf-8'):
    if encoding is not None:
        try:
            string = string.encode(encoding)
        except AttributeError:
            # In Python3, bytes has no encode attribute
            pass
    string = ctypes.c_char_p(string)
    return ctypes.cast(string, ctypes.POINTER(ctypes.c_char))


class struct_kernel_Transaction(Structure):
    pass

kernel_Transaction = struct_kernel_Transaction
class struct_kernel_ScriptPubkey(Structure):
    pass

kernel_ScriptPubkey = struct_kernel_ScriptPubkey
class struct_kernel_TransactionOutput(Structure):
    pass

kernel_TransactionOutput = struct_kernel_TransactionOutput
class struct_kernel_LoggingConnection(Structure):
    pass

kernel_LoggingConnection = struct_kernel_LoggingConnection
class struct_kernel_ChainParameters(Structure):
    pass

kernel_ChainParameters = struct_kernel_ChainParameters
class struct_kernel_ContextOptions(Structure):
    pass

kernel_ContextOptions = struct_kernel_ContextOptions
class struct_kernel_Context(Structure):
    pass

kernel_Context = struct_kernel_Context
class struct_kernel_BlockIndex(Structure):
    pass

kernel_BlockIndex = struct_kernel_BlockIndex
class struct_kernel_ChainstateManagerOptions(Structure):
    pass

kernel_ChainstateManagerOptions = struct_kernel_ChainstateManagerOptions
class struct_kernel_BlockManagerOptions(Structure):
    pass

kernel_BlockManagerOptions = struct_kernel_BlockManagerOptions
class struct_kernel_ChainstateManager(Structure):
    pass

kernel_ChainstateManager = struct_kernel_ChainstateManager
class struct_kernel_ChainstateLoadOptions(Structure):
    pass

kernel_ChainstateLoadOptions = struct_kernel_ChainstateLoadOptions
class struct_kernel_Block(Structure):
    pass

kernel_Block = struct_kernel_Block
class struct_kernel_BlockPointer(Structure):
    pass

kernel_BlockPointer = struct_kernel_BlockPointer
class struct_kernel_BlockValidationState(Structure):
    pass

kernel_BlockValidationState = struct_kernel_BlockValidationState
class struct_kernel_ValidationInterface(Structure):
    pass

kernel_ValidationInterface = struct_kernel_ValidationInterface
class struct_kernel_BlockUndo(Structure):
    pass

kernel_BlockUndo = struct_kernel_BlockUndo

# values for enumeration 'kernel_SynchronizationState'
kernel_SynchronizationState__enumvalues = {
    0: 'kernel_INIT_REINDEX',
    1: 'kernel_INIT_DOWNLOAD',
    2: 'kernel_POST_INIT',
}
kernel_INIT_REINDEX = 0
kernel_INIT_DOWNLOAD = 1
kernel_POST_INIT = 2
kernel_SynchronizationState = ctypes.c_uint32 # enum

# values for enumeration 'kernel_Warning'
kernel_Warning__enumvalues = {
    0: 'kernel_UNKNOWN_NEW_RULES_ACTIVATED',
    1: 'kernel_LARGE_WORK_INVALID_CHAIN',
}
kernel_UNKNOWN_NEW_RULES_ACTIVATED = 0
kernel_LARGE_WORK_INVALID_CHAIN = 1
kernel_Warning = ctypes.c_uint32 # enum
kernel_LogCallback = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(ctypes.c_char), ctypes.c_uint64)
kernel_NotifyBlockTip = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), kernel_SynchronizationState, ctypes.POINTER(struct_kernel_BlockIndex))
kernel_NotifyHeaderTip = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), kernel_SynchronizationState, ctypes.c_int64, ctypes.c_int64, ctypes.c_bool)
kernel_NotifyProgress = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(ctypes.c_char), ctypes.c_uint64, ctypes.c_int32, ctypes.c_bool)
kernel_NotifyWarningSet = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), kernel_Warning, ctypes.POINTER(ctypes.c_char), ctypes.c_uint64)
kernel_NotifyWarningUnset = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), kernel_Warning)
kernel_NotifyFlushError = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(ctypes.c_char), ctypes.c_uint64)
kernel_NotifyFatalError = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(ctypes.c_char), ctypes.c_uint64)
kernel_ValidationInterfaceBlockChecked = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(struct_kernel_BlockPointer), ctypes.POINTER(struct_kernel_BlockValidationState))

# values for enumeration 'kernel_ValidationMode'
kernel_ValidationMode__enumvalues = {
    0: 'kernel_VALIDATION_STATE_VALID',
    1: 'kernel_VALIDATION_STATE_INVALID',
    2: 'kernel_VALIDATION_STATE_ERROR',
}
kernel_VALIDATION_STATE_VALID = 0
kernel_VALIDATION_STATE_INVALID = 1
kernel_VALIDATION_STATE_ERROR = 2
kernel_ValidationMode = ctypes.c_uint32 # enum

# values for enumeration 'kernel_BlockValidationResult'
kernel_BlockValidationResult__enumvalues = {
    0: 'kernel_BLOCK_RESULT_UNSET',
    1: 'kernel_BLOCK_CONSENSUS',
    2: 'kernel_BLOCK_CACHED_INVALID',
    3: 'kernel_BLOCK_INVALID_HEADER',
    4: 'kernel_BLOCK_MUTATED',
    5: 'kernel_BLOCK_MISSING_PREV',
    6: 'kernel_BLOCK_INVALID_PREV',
    7: 'kernel_BLOCK_TIME_FUTURE',
    8: 'kernel_BLOCK_CHECKPOINT',
    9: 'kernel_BLOCK_HEADER_LOW_WORK',
}
kernel_BLOCK_RESULT_UNSET = 0
kernel_BLOCK_CONSENSUS = 1
kernel_BLOCK_CACHED_INVALID = 2
kernel_BLOCK_INVALID_HEADER = 3
kernel_BLOCK_MUTATED = 4
kernel_BLOCK_MISSING_PREV = 5
kernel_BLOCK_INVALID_PREV = 6
kernel_BLOCK_TIME_FUTURE = 7
kernel_BLOCK_CHECKPOINT = 8
kernel_BLOCK_HEADER_LOW_WORK = 9
kernel_BlockValidationResult = ctypes.c_uint32 # enum
class struct_kernel_ValidationInterfaceCallbacks(Structure):
    pass

struct_kernel_ValidationInterfaceCallbacks._pack_ = 1 # source:False
struct_kernel_ValidationInterfaceCallbacks._fields_ = [
    ('user_data', ctypes.POINTER(None)),
    ('block_checked', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(struct_kernel_BlockPointer), ctypes.POINTER(struct_kernel_BlockValidationState))),
]

kernel_ValidationInterfaceCallbacks = struct_kernel_ValidationInterfaceCallbacks
class struct_kernel_NotificationInterfaceCallbacks(Structure):
    pass

struct_kernel_NotificationInterfaceCallbacks._pack_ = 1 # source:False
struct_kernel_NotificationInterfaceCallbacks._fields_ = [
    ('user_data', ctypes.POINTER(None)),
    ('block_tip', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), kernel_SynchronizationState, ctypes.POINTER(struct_kernel_BlockIndex))),
    ('header_tip', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), kernel_SynchronizationState, ctypes.c_int64, ctypes.c_int64, ctypes.c_bool)),
    ('progress', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(ctypes.c_char), ctypes.c_uint64, ctypes.c_int32, ctypes.c_bool)),
    ('warning_set', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), kernel_Warning, ctypes.POINTER(ctypes.c_char), ctypes.c_uint64)),
    ('warning_unset', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), kernel_Warning)),
    ('flush_error', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(ctypes.c_char), ctypes.c_uint64)),
    ('fatal_error', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(ctypes.c_char), ctypes.c_uint64)),
]

kernel_NotificationInterfaceCallbacks = struct_kernel_NotificationInterfaceCallbacks

# values for enumeration 'kernel_LogCategory'
kernel_LogCategory__enumvalues = {
    0: 'kernel_LOG_ALL',
    1: 'kernel_LOG_BENCH',
    2: 'kernel_LOG_BLOCKSTORAGE',
    3: 'kernel_LOG_COINDB',
    4: 'kernel_LOG_LEVELDB',
    5: 'kernel_LOG_LOCK',
    6: 'kernel_LOG_MEMPOOL',
    7: 'kernel_LOG_PRUNE',
    8: 'kernel_LOG_RAND',
    9: 'kernel_LOG_REINDEX',
    10: 'kernel_LOG_VALIDATION',
    11: 'kernel_LOG_KERNEL',
}
kernel_LOG_ALL = 0
kernel_LOG_BENCH = 1
kernel_LOG_BLOCKSTORAGE = 2
kernel_LOG_COINDB = 3
kernel_LOG_LEVELDB = 4
kernel_LOG_LOCK = 5
kernel_LOG_MEMPOOL = 6
kernel_LOG_PRUNE = 7
kernel_LOG_RAND = 8
kernel_LOG_REINDEX = 9
kernel_LOG_VALIDATION = 10
kernel_LOG_KERNEL = 11
kernel_LogCategory = ctypes.c_uint32 # enum

# values for enumeration 'kernel_LogLevel'
kernel_LogLevel__enumvalues = {
    0: 'kernel_LOG_INFO',
    1: 'kernel_LOG_DEBUG',
    2: 'kernel_LOG_TRACE',
}
kernel_LOG_INFO = 0
kernel_LOG_DEBUG = 1
kernel_LOG_TRACE = 2
kernel_LogLevel = ctypes.c_uint32 # enum
class struct_kernel_LoggingOptions(Structure):
    pass

struct_kernel_LoggingOptions._pack_ = 1 # source:False
struct_kernel_LoggingOptions._fields_ = [
    ('log_timestamps', ctypes.c_bool),
    ('log_time_micros', ctypes.c_bool),
    ('log_threadnames', ctypes.c_bool),
    ('log_sourcelocations', ctypes.c_bool),
    ('always_print_category_levels', ctypes.c_bool),
]

kernel_LoggingOptions = struct_kernel_LoggingOptions

# values for enumeration 'kernel_ScriptVerifyStatus'
kernel_ScriptVerifyStatus__enumvalues = {
    0: 'kernel_SCRIPT_VERIFY_OK',
    1: 'kernel_SCRIPT_VERIFY_ERROR_TX_INPUT_INDEX',
    2: 'kernel_SCRIPT_VERIFY_ERROR_INVALID_FLAGS',
    3: 'kernel_SCRIPT_VERIFY_ERROR_INVALID_FLAGS_COMBINATION',
    4: 'kernel_SCRIPT_VERIFY_ERROR_SPENT_OUTPUTS_REQUIRED',
    5: 'kernel_SCRIPT_VERIFY_ERROR_SPENT_OUTPUTS_MISMATCH',
}
kernel_SCRIPT_VERIFY_OK = 0
kernel_SCRIPT_VERIFY_ERROR_TX_INPUT_INDEX = 1
kernel_SCRIPT_VERIFY_ERROR_INVALID_FLAGS = 2
kernel_SCRIPT_VERIFY_ERROR_INVALID_FLAGS_COMBINATION = 3
kernel_SCRIPT_VERIFY_ERROR_SPENT_OUTPUTS_REQUIRED = 4
kernel_SCRIPT_VERIFY_ERROR_SPENT_OUTPUTS_MISMATCH = 5
kernel_ScriptVerifyStatus = ctypes.c_uint32 # enum

# values for enumeration 'kernel_ScriptFlags'
kernel_ScriptFlags__enumvalues = {
    0: 'kernel_SCRIPT_FLAGS_VERIFY_NONE',
    1: 'kernel_SCRIPT_FLAGS_VERIFY_P2SH',
    4: 'kernel_SCRIPT_FLAGS_VERIFY_DERSIG',
    16: 'kernel_SCRIPT_FLAGS_VERIFY_NULLDUMMY',
    512: 'kernel_SCRIPT_FLAGS_VERIFY_CHECKLOCKTIMEVERIFY',
    1024: 'kernel_SCRIPT_FLAGS_VERIFY_CHECKSEQUENCEVERIFY',
    2048: 'kernel_SCRIPT_FLAGS_VERIFY_WITNESS',
    131072: 'kernel_SCRIPT_FLAGS_VERIFY_TAPROOT',
    134677: 'kernel_SCRIPT_FLAGS_VERIFY_ALL',
}
kernel_SCRIPT_FLAGS_VERIFY_NONE = 0
kernel_SCRIPT_FLAGS_VERIFY_P2SH = 1
kernel_SCRIPT_FLAGS_VERIFY_DERSIG = 4
kernel_SCRIPT_FLAGS_VERIFY_NULLDUMMY = 16
kernel_SCRIPT_FLAGS_VERIFY_CHECKLOCKTIMEVERIFY = 512
kernel_SCRIPT_FLAGS_VERIFY_CHECKSEQUENCEVERIFY = 1024
kernel_SCRIPT_FLAGS_VERIFY_WITNESS = 2048
kernel_SCRIPT_FLAGS_VERIFY_TAPROOT = 131072
kernel_SCRIPT_FLAGS_VERIFY_ALL = 134677
kernel_ScriptFlags = ctypes.c_uint32 # enum

# values for enumeration 'kernel_ChainType'
kernel_ChainType__enumvalues = {
    0: 'kernel_CHAIN_TYPE_MAINNET',
    1: 'kernel_CHAIN_TYPE_TESTNET',
    2: 'kernel_CHAIN_TYPE_TESTNET_4',
    3: 'kernel_CHAIN_TYPE_SIGNET',
    4: 'kernel_CHAIN_TYPE_REGTEST',
}
kernel_CHAIN_TYPE_MAINNET = 0
kernel_CHAIN_TYPE_TESTNET = 1
kernel_CHAIN_TYPE_TESTNET_4 = 2
kernel_CHAIN_TYPE_SIGNET = 3
kernel_CHAIN_TYPE_REGTEST = 4
kernel_ChainType = ctypes.c_uint32 # enum
class struct_kernel_BlockHash(Structure):
    pass

struct_kernel_BlockHash._pack_ = 1 # source:False
struct_kernel_BlockHash._fields_ = [
    ('hash', ctypes.c_ubyte * 32),
]

kernel_BlockHash = struct_kernel_BlockHash
class struct_kernel_ByteArray(Structure):
    pass

struct_kernel_ByteArray._pack_ = 1 # source:False
struct_kernel_ByteArray._fields_ = [
    ('data', ctypes.POINTER(ctypes.c_ubyte)),
    ('size', ctypes.c_uint64),
]

kernel_ByteArray = struct_kernel_ByteArray
size_t = ctypes.c_uint64
kernel_transaction_create = BITCOINKERNEL_LIB.kernel_transaction_create
kernel_transaction_create.restype = ctypes.POINTER(struct_kernel_Transaction)
kernel_transaction_create.argtypes = [ctypes.POINTER(ctypes.c_ubyte), size_t]
kernel_transaction_destroy = BITCOINKERNEL_LIB.kernel_transaction_destroy
kernel_transaction_destroy.restype = None
kernel_transaction_destroy.argtypes = [ctypes.POINTER(struct_kernel_Transaction)]
kernel_script_pubkey_create = BITCOINKERNEL_LIB.kernel_script_pubkey_create
kernel_script_pubkey_create.restype = ctypes.POINTER(struct_kernel_ScriptPubkey)
kernel_script_pubkey_create.argtypes = [ctypes.POINTER(ctypes.c_ubyte), size_t]
kernel_copy_script_pubkey_data = BITCOINKERNEL_LIB.kernel_copy_script_pubkey_data
kernel_copy_script_pubkey_data.restype = ctypes.POINTER(struct_kernel_ByteArray)
kernel_copy_script_pubkey_data.argtypes = [ctypes.POINTER(struct_kernel_ScriptPubkey)]
kernel_script_pubkey_destroy = BITCOINKERNEL_LIB.kernel_script_pubkey_destroy
kernel_script_pubkey_destroy.restype = None
kernel_script_pubkey_destroy.argtypes = [ctypes.POINTER(struct_kernel_ScriptPubkey)]
int64_t = ctypes.c_int64
kernel_transaction_output_create = BITCOINKERNEL_LIB.kernel_transaction_output_create
kernel_transaction_output_create.restype = ctypes.POINTER(struct_kernel_TransactionOutput)
kernel_transaction_output_create.argtypes = [ctypes.POINTER(struct_kernel_ScriptPubkey), int64_t]
kernel_copy_script_pubkey_from_output = BITCOINKERNEL_LIB.kernel_copy_script_pubkey_from_output
kernel_copy_script_pubkey_from_output.restype = ctypes.POINTER(struct_kernel_ScriptPubkey)
kernel_copy_script_pubkey_from_output.argtypes = [ctypes.POINTER(struct_kernel_TransactionOutput)]
kernel_get_transaction_output_amount = BITCOINKERNEL_LIB.kernel_get_transaction_output_amount
kernel_get_transaction_output_amount.restype = int64_t
kernel_get_transaction_output_amount.argtypes = [ctypes.POINTER(struct_kernel_TransactionOutput)]
kernel_transaction_output_destroy = BITCOINKERNEL_LIB.kernel_transaction_output_destroy
kernel_transaction_output_destroy.restype = None
kernel_transaction_output_destroy.argtypes = [ctypes.POINTER(struct_kernel_TransactionOutput)]
kernel_verify_script = BITCOINKERNEL_LIB.kernel_verify_script
kernel_verify_script.restype = ctypes.c_bool
kernel_verify_script.argtypes = [ctypes.POINTER(struct_kernel_ScriptPubkey), int64_t, ctypes.POINTER(struct_kernel_Transaction), ctypes.POINTER(ctypes.POINTER(struct_kernel_TransactionOutput)), size_t, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(kernel_ScriptVerifyStatus)]
kernel_disable_logging = BITCOINKERNEL_LIB.kernel_disable_logging
kernel_disable_logging.restype = None
kernel_disable_logging.argtypes = []
kernel_add_log_level_category = BITCOINKERNEL_LIB.kernel_add_log_level_category
kernel_add_log_level_category.restype = ctypes.c_bool
kernel_add_log_level_category.argtypes = [kernel_LogCategory, kernel_LogLevel]
kernel_enable_log_category = BITCOINKERNEL_LIB.kernel_enable_log_category
kernel_enable_log_category.restype = ctypes.c_bool
kernel_enable_log_category.argtypes = [kernel_LogCategory]
kernel_disable_log_category = BITCOINKERNEL_LIB.kernel_disable_log_category
kernel_disable_log_category.restype = ctypes.c_bool
kernel_disable_log_category.argtypes = [kernel_LogCategory]
kernel_logging_connection_create = BITCOINKERNEL_LIB.kernel_logging_connection_create
kernel_logging_connection_create.restype = ctypes.POINTER(struct_kernel_LoggingConnection)
kernel_logging_connection_create.argtypes = [kernel_LogCallback, ctypes.POINTER(None), kernel_LoggingOptions]
kernel_logging_connection_destroy = BITCOINKERNEL_LIB.kernel_logging_connection_destroy
kernel_logging_connection_destroy.restype = None
kernel_logging_connection_destroy.argtypes = [ctypes.POINTER(struct_kernel_LoggingConnection)]
kernel_chain_parameters_create = BITCOINKERNEL_LIB.kernel_chain_parameters_create
kernel_chain_parameters_create.restype = ctypes.POINTER(struct_kernel_ChainParameters)
kernel_chain_parameters_create.argtypes = [kernel_ChainType]
kernel_chain_parameters_destroy = BITCOINKERNEL_LIB.kernel_chain_parameters_destroy
kernel_chain_parameters_destroy.restype = None
kernel_chain_parameters_destroy.argtypes = [ctypes.POINTER(struct_kernel_ChainParameters)]
kernel_context_options_create = BITCOINKERNEL_LIB.kernel_context_options_create
kernel_context_options_create.restype = ctypes.POINTER(struct_kernel_ContextOptions)
kernel_context_options_create.argtypes = []
kernel_context_options_set_chainparams = BITCOINKERNEL_LIB.kernel_context_options_set_chainparams
kernel_context_options_set_chainparams.restype = None
kernel_context_options_set_chainparams.argtypes = [ctypes.POINTER(struct_kernel_ContextOptions), ctypes.POINTER(struct_kernel_ChainParameters)]
kernel_context_options_set_notifications = BITCOINKERNEL_LIB.kernel_context_options_set_notifications
kernel_context_options_set_notifications.restype = None
kernel_context_options_set_notifications.argtypes = [ctypes.POINTER(struct_kernel_ContextOptions), kernel_NotificationInterfaceCallbacks]
kernel_context_options_set_validation_interface = BITCOINKERNEL_LIB.kernel_context_options_set_validation_interface
kernel_context_options_set_validation_interface.restype = None
kernel_context_options_set_validation_interface.argtypes = [ctypes.POINTER(struct_kernel_ContextOptions), kernel_ValidationInterfaceCallbacks]
kernel_context_options_destroy = BITCOINKERNEL_LIB.kernel_context_options_destroy
kernel_context_options_destroy.restype = None
kernel_context_options_destroy.argtypes = [ctypes.POINTER(struct_kernel_ContextOptions)]
kernel_context_create = BITCOINKERNEL_LIB.kernel_context_create
kernel_context_create.restype = ctypes.POINTER(struct_kernel_Context)
kernel_context_create.argtypes = [ctypes.POINTER(struct_kernel_ContextOptions)]
kernel_context_interrupt = BITCOINKERNEL_LIB.kernel_context_interrupt
kernel_context_interrupt.restype = ctypes.c_bool
kernel_context_interrupt.argtypes = [ctypes.POINTER(struct_kernel_Context)]
kernel_context_destroy = BITCOINKERNEL_LIB.kernel_context_destroy
kernel_context_destroy.restype = None
kernel_context_destroy.argtypes = [ctypes.POINTER(struct_kernel_Context)]
kernel_chainstate_manager_options_create = BITCOINKERNEL_LIB.kernel_chainstate_manager_options_create
kernel_chainstate_manager_options_create.restype = ctypes.POINTER(struct_kernel_ChainstateManagerOptions)
kernel_chainstate_manager_options_create.argtypes = [ctypes.POINTER(struct_kernel_Context), ctypes.POINTER(ctypes.c_char), size_t]
kernel_chainstate_manager_options_set_worker_threads_num = BITCOINKERNEL_LIB.kernel_chainstate_manager_options_set_worker_threads_num
kernel_chainstate_manager_options_set_worker_threads_num.restype = None
kernel_chainstate_manager_options_set_worker_threads_num.argtypes = [ctypes.POINTER(struct_kernel_ChainstateManagerOptions), ctypes.c_int32]
kernel_chainstate_manager_options_destroy = BITCOINKERNEL_LIB.kernel_chainstate_manager_options_destroy
kernel_chainstate_manager_options_destroy.restype = None
kernel_chainstate_manager_options_destroy.argtypes = [ctypes.POINTER(struct_kernel_ChainstateManagerOptions)]
kernel_block_manager_options_create = BITCOINKERNEL_LIB.kernel_block_manager_options_create
kernel_block_manager_options_create.restype = ctypes.POINTER(struct_kernel_BlockManagerOptions)
kernel_block_manager_options_create.argtypes = [ctypes.POINTER(struct_kernel_Context), ctypes.POINTER(ctypes.c_char), size_t]
kernel_block_manager_options_destroy = BITCOINKERNEL_LIB.kernel_block_manager_options_destroy
kernel_block_manager_options_destroy.restype = None
kernel_block_manager_options_destroy.argtypes = [ctypes.POINTER(struct_kernel_BlockManagerOptions)]
kernel_chainstate_load_options_create = BITCOINKERNEL_LIB.kernel_chainstate_load_options_create
kernel_chainstate_load_options_create.restype = ctypes.POINTER(struct_kernel_ChainstateLoadOptions)
kernel_chainstate_load_options_create.argtypes = []
kernel_chainstate_load_options_set_wipe_block_tree_db = BITCOINKERNEL_LIB.kernel_chainstate_load_options_set_wipe_block_tree_db
kernel_chainstate_load_options_set_wipe_block_tree_db.restype = None
kernel_chainstate_load_options_set_wipe_block_tree_db.argtypes = [ctypes.POINTER(struct_kernel_ChainstateLoadOptions), ctypes.c_bool]
kernel_chainstate_load_options_set_wipe_chainstate_db = BITCOINKERNEL_LIB.kernel_chainstate_load_options_set_wipe_chainstate_db
kernel_chainstate_load_options_set_wipe_chainstate_db.restype = None
kernel_chainstate_load_options_set_wipe_chainstate_db.argtypes = [ctypes.POINTER(struct_kernel_ChainstateLoadOptions), ctypes.c_bool]
kernel_chainstate_load_options_set_block_tree_db_in_memory = BITCOINKERNEL_LIB.kernel_chainstate_load_options_set_block_tree_db_in_memory
kernel_chainstate_load_options_set_block_tree_db_in_memory.restype = None
kernel_chainstate_load_options_set_block_tree_db_in_memory.argtypes = [ctypes.POINTER(struct_kernel_ChainstateLoadOptions), ctypes.c_bool]
kernel_chainstate_load_options_set_chainstate_db_in_memory = BITCOINKERNEL_LIB.kernel_chainstate_load_options_set_chainstate_db_in_memory
kernel_chainstate_load_options_set_chainstate_db_in_memory.restype = None
kernel_chainstate_load_options_set_chainstate_db_in_memory.argtypes = [ctypes.POINTER(struct_kernel_ChainstateLoadOptions), ctypes.c_bool]
kernel_chainstate_load_options_destroy = BITCOINKERNEL_LIB.kernel_chainstate_load_options_destroy
kernel_chainstate_load_options_destroy.restype = None
kernel_chainstate_load_options_destroy.argtypes = [ctypes.POINTER(struct_kernel_ChainstateLoadOptions)]
kernel_chainstate_manager_create = BITCOINKERNEL_LIB.kernel_chainstate_manager_create
kernel_chainstate_manager_create.restype = ctypes.POINTER(struct_kernel_ChainstateManager)
kernel_chainstate_manager_create.argtypes = [ctypes.POINTER(struct_kernel_Context), ctypes.POINTER(struct_kernel_ChainstateManagerOptions), ctypes.POINTER(struct_kernel_BlockManagerOptions), ctypes.POINTER(struct_kernel_ChainstateLoadOptions)]
kernel_import_blocks = BITCOINKERNEL_LIB.kernel_import_blocks
kernel_import_blocks.restype = ctypes.c_bool
kernel_import_blocks.argtypes = [ctypes.POINTER(struct_kernel_Context), ctypes.POINTER(struct_kernel_ChainstateManager), ctypes.POINTER(ctypes.POINTER(ctypes.c_char)), ctypes.POINTER(ctypes.c_uint64), size_t]
kernel_chainstate_manager_process_block = BITCOINKERNEL_LIB.kernel_chainstate_manager_process_block
kernel_chainstate_manager_process_block.restype = ctypes.c_bool
kernel_chainstate_manager_process_block.argtypes = [ctypes.POINTER(struct_kernel_Context), ctypes.POINTER(struct_kernel_ChainstateManager), ctypes.POINTER(struct_kernel_Block), ctypes.POINTER(ctypes.c_bool)]
kernel_chainstate_manager_destroy = BITCOINKERNEL_LIB.kernel_chainstate_manager_destroy
kernel_chainstate_manager_destroy.restype = None
kernel_chainstate_manager_destroy.argtypes = [ctypes.POINTER(struct_kernel_ChainstateManager), ctypes.POINTER(struct_kernel_Context)]
kernel_read_block_from_disk = BITCOINKERNEL_LIB.kernel_read_block_from_disk
kernel_read_block_from_disk.restype = ctypes.POINTER(struct_kernel_Block)
kernel_read_block_from_disk.argtypes = [ctypes.POINTER(struct_kernel_Context), ctypes.POINTER(struct_kernel_ChainstateManager), ctypes.POINTER(struct_kernel_BlockIndex)]
kernel_block_create = BITCOINKERNEL_LIB.kernel_block_create
kernel_block_create.restype = ctypes.POINTER(struct_kernel_Block)
kernel_block_create.argtypes = [ctypes.POINTER(ctypes.c_ubyte), size_t]
kernel_block_get_hash = BITCOINKERNEL_LIB.kernel_block_get_hash
kernel_block_get_hash.restype = ctypes.POINTER(struct_kernel_BlockHash)
kernel_block_get_hash.argtypes = [ctypes.POINTER(struct_kernel_Block)]
kernel_block_pointer_get_hash = BITCOINKERNEL_LIB.kernel_block_pointer_get_hash
kernel_block_pointer_get_hash.restype = ctypes.POINTER(struct_kernel_BlockHash)
kernel_block_pointer_get_hash.argtypes = [ctypes.POINTER(struct_kernel_BlockPointer)]
kernel_copy_block_data = BITCOINKERNEL_LIB.kernel_copy_block_data
kernel_copy_block_data.restype = ctypes.POINTER(struct_kernel_ByteArray)
kernel_copy_block_data.argtypes = [ctypes.POINTER(struct_kernel_Block)]
kernel_copy_block_pointer_data = BITCOINKERNEL_LIB.kernel_copy_block_pointer_data
kernel_copy_block_pointer_data.restype = ctypes.POINTER(struct_kernel_ByteArray)
kernel_copy_block_pointer_data.argtypes = [ctypes.POINTER(struct_kernel_BlockPointer)]
kernel_block_destroy = BITCOINKERNEL_LIB.kernel_block_destroy
kernel_block_destroy.restype = None
kernel_block_destroy.argtypes = [ctypes.POINTER(struct_kernel_Block)]
kernel_byte_array_destroy = BITCOINKERNEL_LIB.kernel_byte_array_destroy
kernel_byte_array_destroy.restype = None
kernel_byte_array_destroy.argtypes = [ctypes.POINTER(struct_kernel_ByteArray)]
kernel_get_validation_mode_from_block_validation_state = BITCOINKERNEL_LIB.kernel_get_validation_mode_from_block_validation_state
kernel_get_validation_mode_from_block_validation_state.restype = kernel_ValidationMode
kernel_get_validation_mode_from_block_validation_state.argtypes = [ctypes.POINTER(struct_kernel_BlockValidationState)]
kernel_get_block_validation_result_from_block_validation_state = BITCOINKERNEL_LIB.kernel_get_block_validation_result_from_block_validation_state
kernel_get_block_validation_result_from_block_validation_state.restype = kernel_BlockValidationResult
kernel_get_block_validation_result_from_block_validation_state.argtypes = [ctypes.POINTER(struct_kernel_BlockValidationState)]
kernel_get_block_index_from_tip = BITCOINKERNEL_LIB.kernel_get_block_index_from_tip
kernel_get_block_index_from_tip.restype = ctypes.POINTER(struct_kernel_BlockIndex)
kernel_get_block_index_from_tip.argtypes = [ctypes.POINTER(struct_kernel_Context), ctypes.POINTER(struct_kernel_ChainstateManager)]
kernel_get_block_index_from_genesis = BITCOINKERNEL_LIB.kernel_get_block_index_from_genesis
kernel_get_block_index_from_genesis.restype = ctypes.POINTER(struct_kernel_BlockIndex)
kernel_get_block_index_from_genesis.argtypes = [ctypes.POINTER(struct_kernel_Context), ctypes.POINTER(struct_kernel_ChainstateManager)]
kernel_get_block_index_from_hash = BITCOINKERNEL_LIB.kernel_get_block_index_from_hash
kernel_get_block_index_from_hash.restype = ctypes.POINTER(struct_kernel_BlockIndex)
kernel_get_block_index_from_hash.argtypes = [ctypes.POINTER(struct_kernel_Context), ctypes.POINTER(struct_kernel_ChainstateManager), ctypes.POINTER(struct_kernel_BlockHash)]
kernel_get_block_index_from_height = BITCOINKERNEL_LIB.kernel_get_block_index_from_height
kernel_get_block_index_from_height.restype = ctypes.POINTER(struct_kernel_BlockIndex)
kernel_get_block_index_from_height.argtypes = [ctypes.POINTER(struct_kernel_Context), ctypes.POINTER(struct_kernel_ChainstateManager), ctypes.c_int32]
kernel_get_next_block_index = BITCOINKERNEL_LIB.kernel_get_next_block_index
kernel_get_next_block_index.restype = ctypes.POINTER(struct_kernel_BlockIndex)
kernel_get_next_block_index.argtypes = [ctypes.POINTER(struct_kernel_Context), ctypes.POINTER(struct_kernel_ChainstateManager), ctypes.POINTER(struct_kernel_BlockIndex)]
kernel_get_previous_block_index = BITCOINKERNEL_LIB.kernel_get_previous_block_index
kernel_get_previous_block_index.restype = ctypes.POINTER(struct_kernel_BlockIndex)
kernel_get_previous_block_index.argtypes = [ctypes.POINTER(struct_kernel_BlockIndex)]
int32_t = ctypes.c_int32
kernel_block_index_get_height = BITCOINKERNEL_LIB.kernel_block_index_get_height
kernel_block_index_get_height.restype = int32_t
kernel_block_index_get_height.argtypes = [ctypes.POINTER(struct_kernel_BlockIndex)]
kernel_block_index_destroy = BITCOINKERNEL_LIB.kernel_block_index_destroy
kernel_block_index_destroy.restype = None
kernel_block_index_destroy.argtypes = [ctypes.POINTER(struct_kernel_BlockIndex)]
kernel_read_block_undo_from_disk = BITCOINKERNEL_LIB.kernel_read_block_undo_from_disk
kernel_read_block_undo_from_disk.restype = ctypes.POINTER(struct_kernel_BlockUndo)
kernel_read_block_undo_from_disk.argtypes = [ctypes.POINTER(struct_kernel_Context), ctypes.POINTER(struct_kernel_ChainstateManager), ctypes.POINTER(struct_kernel_BlockIndex)]
uint64_t = ctypes.c_uint64
kernel_block_undo_size = BITCOINKERNEL_LIB.kernel_block_undo_size
kernel_block_undo_size.restype = uint64_t
kernel_block_undo_size.argtypes = [ctypes.POINTER(struct_kernel_BlockUndo)]
kernel_get_transaction_undo_size = BITCOINKERNEL_LIB.kernel_get_transaction_undo_size
kernel_get_transaction_undo_size.restype = uint64_t
kernel_get_transaction_undo_size.argtypes = [ctypes.POINTER(struct_kernel_BlockUndo), uint64_t]
kernel_get_undo_output_by_index = BITCOINKERNEL_LIB.kernel_get_undo_output_by_index
kernel_get_undo_output_by_index.restype = ctypes.POINTER(struct_kernel_TransactionOutput)
kernel_get_undo_output_by_index.argtypes = [ctypes.POINTER(struct_kernel_BlockUndo), uint64_t, uint64_t]
kernel_block_undo_destroy = BITCOINKERNEL_LIB.kernel_block_undo_destroy
kernel_block_undo_destroy.restype = None
kernel_block_undo_destroy.argtypes = [ctypes.POINTER(struct_kernel_BlockUndo)]
kernel_block_index_get_block_hash = BITCOINKERNEL_LIB.kernel_block_index_get_block_hash
kernel_block_index_get_block_hash.restype = ctypes.POINTER(struct_kernel_BlockHash)
kernel_block_index_get_block_hash.argtypes = [ctypes.POINTER(struct_kernel_BlockIndex)]
kernel_block_hash_destroy = BITCOINKERNEL_LIB.kernel_block_hash_destroy
kernel_block_hash_destroy.restype = None
kernel_block_hash_destroy.argtypes = [ctypes.POINTER(struct_kernel_BlockHash)]
__all__ = \
    ['int32_t', 'int64_t', 'kernel_BLOCK_CACHED_INVALID',
    'kernel_BLOCK_CHECKPOINT', 'kernel_BLOCK_CONSENSUS',
    'kernel_BLOCK_HEADER_LOW_WORK', 'kernel_BLOCK_INVALID_HEADER',
    'kernel_BLOCK_INVALID_PREV', 'kernel_BLOCK_MISSING_PREV',
    'kernel_BLOCK_MUTATED', 'kernel_BLOCK_RESULT_UNSET',
    'kernel_BLOCK_TIME_FUTURE', 'kernel_Block', 'kernel_BlockHash',
    'kernel_BlockIndex', 'kernel_BlockManagerOptions',
    'kernel_BlockPointer', 'kernel_BlockUndo',
    'kernel_BlockValidationResult', 'kernel_BlockValidationState',
    'kernel_ByteArray', 'kernel_CHAIN_TYPE_MAINNET',
    'kernel_CHAIN_TYPE_REGTEST', 'kernel_CHAIN_TYPE_SIGNET',
    'kernel_CHAIN_TYPE_TESTNET', 'kernel_CHAIN_TYPE_TESTNET_4',
    'kernel_ChainParameters', 'kernel_ChainType',
    'kernel_ChainstateLoadOptions', 'kernel_ChainstateManager',
    'kernel_ChainstateManagerOptions', 'kernel_Context',
    'kernel_ContextOptions', 'kernel_INIT_DOWNLOAD',
    'kernel_INIT_REINDEX', 'kernel_LARGE_WORK_INVALID_CHAIN',
    'kernel_LOG_ALL', 'kernel_LOG_BENCH', 'kernel_LOG_BLOCKSTORAGE',
    'kernel_LOG_COINDB', 'kernel_LOG_DEBUG', 'kernel_LOG_INFO',
    'kernel_LOG_KERNEL', 'kernel_LOG_LEVELDB', 'kernel_LOG_LOCK',
    'kernel_LOG_MEMPOOL', 'kernel_LOG_PRUNE', 'kernel_LOG_RAND',
    'kernel_LOG_REINDEX', 'kernel_LOG_TRACE', 'kernel_LOG_VALIDATION',
    'kernel_LogCallback', 'kernel_LogCategory', 'kernel_LogLevel',
    'kernel_LoggingConnection', 'kernel_LoggingOptions',
    'kernel_NotificationInterfaceCallbacks', 'kernel_NotifyBlockTip',
    'kernel_NotifyFatalError', 'kernel_NotifyFlushError',
    'kernel_NotifyHeaderTip', 'kernel_NotifyProgress',
    'kernel_NotifyWarningSet', 'kernel_NotifyWarningUnset',
    'kernel_POST_INIT', 'kernel_SCRIPT_FLAGS_VERIFY_ALL',
    'kernel_SCRIPT_FLAGS_VERIFY_CHECKLOCKTIMEVERIFY',
    'kernel_SCRIPT_FLAGS_VERIFY_CHECKSEQUENCEVERIFY',
    'kernel_SCRIPT_FLAGS_VERIFY_DERSIG',
    'kernel_SCRIPT_FLAGS_VERIFY_NONE',
    'kernel_SCRIPT_FLAGS_VERIFY_NULLDUMMY',
    'kernel_SCRIPT_FLAGS_VERIFY_P2SH',
    'kernel_SCRIPT_FLAGS_VERIFY_TAPROOT',
    'kernel_SCRIPT_FLAGS_VERIFY_WITNESS',
    'kernel_SCRIPT_VERIFY_ERROR_INVALID_FLAGS',
    'kernel_SCRIPT_VERIFY_ERROR_INVALID_FLAGS_COMBINATION',
    'kernel_SCRIPT_VERIFY_ERROR_SPENT_OUTPUTS_MISMATCH',
    'kernel_SCRIPT_VERIFY_ERROR_SPENT_OUTPUTS_REQUIRED',
    'kernel_SCRIPT_VERIFY_ERROR_TX_INPUT_INDEX',
    'kernel_SCRIPT_VERIFY_OK', 'kernel_ScriptFlags',
    'kernel_ScriptPubkey', 'kernel_ScriptVerifyStatus',
    'kernel_SynchronizationState', 'kernel_Transaction',
    'kernel_TransactionOutput', 'kernel_UNKNOWN_NEW_RULES_ACTIVATED',
    'kernel_VALIDATION_STATE_ERROR',
    'kernel_VALIDATION_STATE_INVALID',
    'kernel_VALIDATION_STATE_VALID', 'kernel_ValidationInterface',
    'kernel_ValidationInterfaceBlockChecked',
    'kernel_ValidationInterfaceCallbacks', 'kernel_ValidationMode',
    'kernel_Warning', 'kernel_add_log_level_category',
    'kernel_block_create', 'kernel_block_destroy',
    'kernel_block_get_hash', 'kernel_block_hash_destroy',
    'kernel_block_index_destroy', 'kernel_block_index_get_block_hash',
    'kernel_block_index_get_height',
    'kernel_block_manager_options_create',
    'kernel_block_manager_options_destroy',
    'kernel_block_pointer_get_hash', 'kernel_block_undo_destroy',
    'kernel_block_undo_size', 'kernel_byte_array_destroy',
    'kernel_chain_parameters_create',
    'kernel_chain_parameters_destroy',
    'kernel_chainstate_load_options_create',
    'kernel_chainstate_load_options_destroy',
    'kernel_chainstate_load_options_set_block_tree_db_in_memory',
    'kernel_chainstate_load_options_set_chainstate_db_in_memory',
    'kernel_chainstate_load_options_set_wipe_block_tree_db',
    'kernel_chainstate_load_options_set_wipe_chainstate_db',
    'kernel_chainstate_manager_create',
    'kernel_chainstate_manager_destroy',
    'kernel_chainstate_manager_options_create',
    'kernel_chainstate_manager_options_destroy',
    'kernel_chainstate_manager_options_set_worker_threads_num',
    'kernel_chainstate_manager_process_block',
    'kernel_context_create', 'kernel_context_destroy',
    'kernel_context_interrupt', 'kernel_context_options_create',
    'kernel_context_options_destroy',
    'kernel_context_options_set_chainparams',
    'kernel_context_options_set_notifications',
    'kernel_context_options_set_validation_interface',
    'kernel_copy_block_data', 'kernel_copy_block_pointer_data',
    'kernel_copy_script_pubkey_data',
    'kernel_copy_script_pubkey_from_output',
    'kernel_disable_log_category', 'kernel_disable_logging',
    'kernel_enable_log_category',
    'kernel_get_block_index_from_genesis',
    'kernel_get_block_index_from_hash',
    'kernel_get_block_index_from_height',
    'kernel_get_block_index_from_tip',
    'kernel_get_block_validation_result_from_block_validation_state',
    'kernel_get_next_block_index', 'kernel_get_previous_block_index',
    'kernel_get_transaction_output_amount',
    'kernel_get_transaction_undo_size',
    'kernel_get_undo_output_by_index',
    'kernel_get_validation_mode_from_block_validation_state',
    'kernel_import_blocks', 'kernel_logging_connection_create',
    'kernel_logging_connection_destroy',
    'kernel_read_block_from_disk', 'kernel_read_block_undo_from_disk',
    'kernel_script_pubkey_create', 'kernel_script_pubkey_destroy',
    'kernel_transaction_create', 'kernel_transaction_destroy',
    'kernel_transaction_output_create',
    'kernel_transaction_output_destroy', 'kernel_verify_script',
    'size_t', 'struct_kernel_Block', 'struct_kernel_BlockHash',
    'struct_kernel_BlockIndex', 'struct_kernel_BlockManagerOptions',
    'struct_kernel_BlockPointer', 'struct_kernel_BlockUndo',
    'struct_kernel_BlockValidationState', 'struct_kernel_ByteArray',
    'struct_kernel_ChainParameters',
    'struct_kernel_ChainstateLoadOptions',
    'struct_kernel_ChainstateManager',
    'struct_kernel_ChainstateManagerOptions', 'struct_kernel_Context',
    'struct_kernel_ContextOptions', 'struct_kernel_LoggingConnection',
    'struct_kernel_LoggingOptions',
    'struct_kernel_NotificationInterfaceCallbacks',
    'struct_kernel_ScriptPubkey', 'struct_kernel_Transaction',
    'struct_kernel_TransactionOutput',
    'struct_kernel_ValidationInterface',
    'struct_kernel_ValidationInterfaceCallbacks', 'uint64_t']
