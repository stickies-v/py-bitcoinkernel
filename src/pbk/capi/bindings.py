# -*- coding: utf-8 -*-
#
# TARGET arch is: []
# WORD_SIZE is: 8
# POINTER_SIZE is: 8
# LONGDOUBLE_SIZE is: 8
#
import ctypes
import site
from importlib import resources
from pathlib import Path


def _find_bitcoinkernel_lib():
    resources_paths = [resources.files("pbk")]
    # Adding site packages makes this work in editable mode with scikit-build-core
    site_packages_paths = [Path(p) / "pbk" for p in site.getsitepackages()]
    for pkg_path in [*resources_paths, *site_packages_paths]:
        matches = list((pkg_path / "_libs").glob('*bitcoinkernel*'))
        if len(matches) == 1:
            return str(matches[0])
        if matches:
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
                type_ = type_._type_
                if hasattr(type_, 'as_dict'):
                    value = [type_.as_dict(v) for v in value]
                else:
                    value = [i for i in value]
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



class FunctionFactoryStub:
    def __getattr__(self, _):
      return ctypes.CFUNCTYPE(lambda y:y)

class struct_btck_Transaction(Structure):
    pass

btck_Transaction = struct_btck_Transaction
class struct_btck_ScriptPubkey(Structure):
    pass

btck_ScriptPubkey = struct_btck_ScriptPubkey
class struct_btck_TransactionOutput(Structure):
    pass

btck_TransactionOutput = struct_btck_TransactionOutput
class struct_btck_LoggingConnection(Structure):
    pass

btck_LoggingConnection = struct_btck_LoggingConnection
class struct_btck_ChainParameters(Structure):
    pass

btck_ChainParameters = struct_btck_ChainParameters
class struct_btck_ContextOptions(Structure):
    pass

btck_ContextOptions = struct_btck_ContextOptions
class struct_btck_Context(Structure):
    pass

btck_Context = struct_btck_Context
class struct_btck_BlockTreeEntry(Structure):
    pass

btck_BlockTreeEntry = struct_btck_BlockTreeEntry
class struct_btck_ChainstateManagerOptions(Structure):
    pass

btck_ChainstateManagerOptions = struct_btck_ChainstateManagerOptions
class struct_btck_ChainstateManager(Structure):
    pass

btck_ChainstateManager = struct_btck_ChainstateManager
class struct_btck_Block(Structure):
    pass

btck_Block = struct_btck_Block
class struct_btck_BlockValidationState(Structure):
    pass

btck_BlockValidationState = struct_btck_BlockValidationState
class struct_btck_Chain(Structure):
    pass

btck_Chain = struct_btck_Chain
class struct_btck_BlockSpentOutputs(Structure):
    pass

btck_BlockSpentOutputs = struct_btck_BlockSpentOutputs
class struct_btck_TransactionSpentOutputs(Structure):
    pass

btck_TransactionSpentOutputs = struct_btck_TransactionSpentOutputs
class struct_btck_Coin(Structure):
    pass

btck_Coin = struct_btck_Coin
class struct_btck_BlockHash(Structure):
    pass

btck_BlockHash = struct_btck_BlockHash
class struct_btck_TransactionInput(Structure):
    pass

btck_TransactionInput = struct_btck_TransactionInput
class struct_btck_TransactionOutPoint(Structure):
    pass

btck_TransactionOutPoint = struct_btck_TransactionOutPoint
class struct_btck_Txid(Structure):
    pass

btck_Txid = struct_btck_Txid
btck_SynchronizationState = ctypes.c_ubyte
btck_Warning = ctypes.c_ubyte
btck_DestroyCallback = ctypes.CFUNCTYPE(None, ctypes.POINTER(None))
btck_NotifyBlockTip = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.c_ubyte, ctypes.POINTER(struct_btck_BlockTreeEntry), ctypes.c_double)
btck_NotifyHeaderTip = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.c_ubyte, ctypes.c_int64, ctypes.c_int64, ctypes.c_int32)
btck_NotifyProgress = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(ctypes.c_char), ctypes.c_uint64, ctypes.c_int32, ctypes.c_int32)
btck_NotifyWarningSet = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.c_ubyte, ctypes.POINTER(ctypes.c_char), ctypes.c_uint64)
btck_NotifyWarningUnset = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.c_ubyte)
btck_NotifyFlushError = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(ctypes.c_char), ctypes.c_uint64)
btck_NotifyFatalError = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(ctypes.c_char), ctypes.c_uint64)
btck_ValidationInterfaceBlockChecked = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(struct_btck_Block), ctypes.POINTER(struct_btck_BlockValidationState))
btck_ValidationInterfacePoWValidBlock = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(struct_btck_Block), ctypes.POINTER(struct_btck_BlockTreeEntry))
btck_ValidationInterfaceBlockConnected = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(struct_btck_Block), ctypes.POINTER(struct_btck_BlockTreeEntry))
btck_ValidationInterfaceBlockDisconnected = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(struct_btck_Block), ctypes.POINTER(struct_btck_BlockTreeEntry))
btck_WriteBytes = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.POINTER(None), ctypes.c_uint64, ctypes.POINTER(None))
btck_ValidationMode = ctypes.c_ubyte
btck_BlockValidationResult = ctypes.c_uint32
class struct_btck_ValidationInterfaceCallbacks(Structure):
    pass

struct_btck_ValidationInterfaceCallbacks._pack_ = 1 # source:False
struct_btck_ValidationInterfaceCallbacks._fields_ = [
    ('user_data', ctypes.POINTER(None)),
    ('user_data_destroy', ctypes.CFUNCTYPE(None, ctypes.POINTER(None))),
    ('block_checked', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(struct_btck_Block), ctypes.POINTER(struct_btck_BlockValidationState))),
    ('pow_valid_block', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(struct_btck_Block), ctypes.POINTER(struct_btck_BlockTreeEntry))),
    ('block_connected', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(struct_btck_Block), ctypes.POINTER(struct_btck_BlockTreeEntry))),
    ('block_disconnected', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(struct_btck_Block), ctypes.POINTER(struct_btck_BlockTreeEntry))),
]

btck_ValidationInterfaceCallbacks = struct_btck_ValidationInterfaceCallbacks
class struct_btck_NotificationInterfaceCallbacks(Structure):
    pass

struct_btck_NotificationInterfaceCallbacks._pack_ = 1 # source:False
struct_btck_NotificationInterfaceCallbacks._fields_ = [
    ('user_data', ctypes.POINTER(None)),
    ('user_data_destroy', ctypes.CFUNCTYPE(None, ctypes.POINTER(None))),
    ('block_tip', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.c_ubyte, ctypes.POINTER(struct_btck_BlockTreeEntry), ctypes.c_double)),
    ('header_tip', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.c_ubyte, ctypes.c_int64, ctypes.c_int64, ctypes.c_int32)),
    ('progress', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(ctypes.c_char), ctypes.c_uint64, ctypes.c_int32, ctypes.c_int32)),
    ('warning_set', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.c_ubyte, ctypes.POINTER(ctypes.c_char), ctypes.c_uint64)),
    ('warning_unset', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.c_ubyte)),
    ('flush_error', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(ctypes.c_char), ctypes.c_uint64)),
    ('fatal_error', ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(ctypes.c_char), ctypes.c_uint64)),
]

btck_NotificationInterfaceCallbacks = struct_btck_NotificationInterfaceCallbacks
btck_LogCategory = ctypes.c_ubyte
btck_LogLevel = ctypes.c_ubyte
class struct_btck_LoggingOptions(Structure):
    pass

struct_btck_LoggingOptions._pack_ = 1 # source:False
struct_btck_LoggingOptions._fields_ = [
    ('log_timestamps', ctypes.c_int32),
    ('log_time_micros', ctypes.c_int32),
    ('log_threadnames', ctypes.c_int32),
    ('log_sourcelocations', ctypes.c_int32),
    ('always_print_category_levels', ctypes.c_int32),
]

btck_LoggingOptions = struct_btck_LoggingOptions
class struct_btck_LogEntry(Structure):
    pass

struct_btck_LogEntry._pack_ = 1 # source:False
struct_btck_LogEntry._fields_ = [
    ('level', ctypes.c_ubyte),
    ('category', ctypes.c_ubyte),
    ('PADDING_0', ctypes.c_ubyte * 6),
    ('message', ctypes.POINTER(ctypes.c_char)),
    ('message_len', ctypes.c_uint64),
    ('source_file', ctypes.POINTER(ctypes.c_char)),
    ('source_file_len', ctypes.c_uint64),
    ('source_func', ctypes.POINTER(ctypes.c_char)),
    ('source_func_len', ctypes.c_uint64),
    ('source_line', ctypes.c_uint32),
    ('PADDING_1', ctypes.c_ubyte * 4),
    ('timestamp_s', ctypes.c_int64),
    ('timestamp_us', ctypes.c_int32),
    ('PADDING_2', ctypes.c_ubyte * 4),
    ('thread_name', ctypes.POINTER(ctypes.c_char)),
    ('thread_name_len', ctypes.c_uint64),
]

btck_LogEntry = struct_btck_LogEntry
btck_LogCallback = ctypes.CFUNCTYPE(None, ctypes.POINTER(None), ctypes.POINTER(struct_btck_LogEntry))
btck_ScriptVerifyStatus = ctypes.c_ubyte
btck_ScriptVerificationFlags = ctypes.c_uint32
btck_ChainType = ctypes.c_ubyte
size_t = ctypes.c_uint64
try:
    btck_transaction_create = BITCOINKERNEL_LIB.btck_transaction_create
    btck_transaction_create.restype = ctypes.POINTER(struct_btck_Transaction)
    btck_transaction_create.argtypes = [ctypes.POINTER(None), size_t]
except AttributeError:
    pass
try:
    btck_transaction_copy = BITCOINKERNEL_LIB.btck_transaction_copy
    btck_transaction_copy.restype = ctypes.POINTER(struct_btck_Transaction)
    btck_transaction_copy.argtypes = [ctypes.POINTER(struct_btck_Transaction)]
except AttributeError:
    pass
try:
    btck_transaction_to_bytes = BITCOINKERNEL_LIB.btck_transaction_to_bytes
    btck_transaction_to_bytes.restype = ctypes.c_int32
    btck_transaction_to_bytes.argtypes = [ctypes.POINTER(struct_btck_Transaction), btck_WriteBytes, ctypes.POINTER(None)]
except AttributeError:
    pass
try:
    btck_transaction_count_outputs = BITCOINKERNEL_LIB.btck_transaction_count_outputs
    btck_transaction_count_outputs.restype = size_t
    btck_transaction_count_outputs.argtypes = [ctypes.POINTER(struct_btck_Transaction)]
except AttributeError:
    pass
try:
    btck_transaction_get_output_at = BITCOINKERNEL_LIB.btck_transaction_get_output_at
    btck_transaction_get_output_at.restype = ctypes.POINTER(struct_btck_TransactionOutput)
    btck_transaction_get_output_at.argtypes = [ctypes.POINTER(struct_btck_Transaction), size_t]
except AttributeError:
    pass
try:
    btck_transaction_get_input_at = BITCOINKERNEL_LIB.btck_transaction_get_input_at
    btck_transaction_get_input_at.restype = ctypes.POINTER(struct_btck_TransactionInput)
    btck_transaction_get_input_at.argtypes = [ctypes.POINTER(struct_btck_Transaction), size_t]
except AttributeError:
    pass
try:
    btck_transaction_count_inputs = BITCOINKERNEL_LIB.btck_transaction_count_inputs
    btck_transaction_count_inputs.restype = size_t
    btck_transaction_count_inputs.argtypes = [ctypes.POINTER(struct_btck_Transaction)]
except AttributeError:
    pass
try:
    btck_transaction_get_txid = BITCOINKERNEL_LIB.btck_transaction_get_txid
    btck_transaction_get_txid.restype = ctypes.POINTER(struct_btck_Txid)
    btck_transaction_get_txid.argtypes = [ctypes.POINTER(struct_btck_Transaction)]
except AttributeError:
    pass
try:
    btck_transaction_destroy = BITCOINKERNEL_LIB.btck_transaction_destroy
    btck_transaction_destroy.restype = None
    btck_transaction_destroy.argtypes = [ctypes.POINTER(struct_btck_Transaction)]
except AttributeError:
    pass
try:
    btck_script_pubkey_create = BITCOINKERNEL_LIB.btck_script_pubkey_create
    btck_script_pubkey_create.restype = ctypes.POINTER(struct_btck_ScriptPubkey)
    btck_script_pubkey_create.argtypes = [ctypes.POINTER(None), size_t]
except AttributeError:
    pass
try:
    btck_script_pubkey_copy = BITCOINKERNEL_LIB.btck_script_pubkey_copy
    btck_script_pubkey_copy.restype = ctypes.POINTER(struct_btck_ScriptPubkey)
    btck_script_pubkey_copy.argtypes = [ctypes.POINTER(struct_btck_ScriptPubkey)]
except AttributeError:
    pass
int64_t = ctypes.c_int64
try:
    btck_script_pubkey_verify = BITCOINKERNEL_LIB.btck_script_pubkey_verify
    btck_script_pubkey_verify.restype = ctypes.c_int32
    btck_script_pubkey_verify.argtypes = [ctypes.POINTER(struct_btck_ScriptPubkey), int64_t, ctypes.POINTER(struct_btck_Transaction), ctypes.POINTER(ctypes.POINTER(struct_btck_TransactionOutput)), size_t, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_ubyte)]
except AttributeError:
    pass
try:
    btck_script_pubkey_to_bytes = BITCOINKERNEL_LIB.btck_script_pubkey_to_bytes
    btck_script_pubkey_to_bytes.restype = ctypes.c_int32
    btck_script_pubkey_to_bytes.argtypes = [ctypes.POINTER(struct_btck_ScriptPubkey), btck_WriteBytes, ctypes.POINTER(None)]
except AttributeError:
    pass
try:
    btck_script_pubkey_destroy = BITCOINKERNEL_LIB.btck_script_pubkey_destroy
    btck_script_pubkey_destroy.restype = None
    btck_script_pubkey_destroy.argtypes = [ctypes.POINTER(struct_btck_ScriptPubkey)]
except AttributeError:
    pass
try:
    btck_transaction_output_create = BITCOINKERNEL_LIB.btck_transaction_output_create
    btck_transaction_output_create.restype = ctypes.POINTER(struct_btck_TransactionOutput)
    btck_transaction_output_create.argtypes = [ctypes.POINTER(struct_btck_ScriptPubkey), int64_t]
except AttributeError:
    pass
try:
    btck_transaction_output_get_script_pubkey = BITCOINKERNEL_LIB.btck_transaction_output_get_script_pubkey
    btck_transaction_output_get_script_pubkey.restype = ctypes.POINTER(struct_btck_ScriptPubkey)
    btck_transaction_output_get_script_pubkey.argtypes = [ctypes.POINTER(struct_btck_TransactionOutput)]
except AttributeError:
    pass
try:
    btck_transaction_output_get_amount = BITCOINKERNEL_LIB.btck_transaction_output_get_amount
    btck_transaction_output_get_amount.restype = int64_t
    btck_transaction_output_get_amount.argtypes = [ctypes.POINTER(struct_btck_TransactionOutput)]
except AttributeError:
    pass
try:
    btck_transaction_output_copy = BITCOINKERNEL_LIB.btck_transaction_output_copy
    btck_transaction_output_copy.restype = ctypes.POINTER(struct_btck_TransactionOutput)
    btck_transaction_output_copy.argtypes = [ctypes.POINTER(struct_btck_TransactionOutput)]
except AttributeError:
    pass
try:
    btck_transaction_output_destroy = BITCOINKERNEL_LIB.btck_transaction_output_destroy
    btck_transaction_output_destroy.restype = None
    btck_transaction_output_destroy.argtypes = [ctypes.POINTER(struct_btck_TransactionOutput)]
except AttributeError:
    pass
try:
    btck_logging_disable = BITCOINKERNEL_LIB.btck_logging_disable
    btck_logging_disable.restype = None
    btck_logging_disable.argtypes = []
except AttributeError:
    pass
try:
    btck_logging_set_options = BITCOINKERNEL_LIB.btck_logging_set_options
    btck_logging_set_options.restype = None
    btck_logging_set_options.argtypes = [btck_LoggingOptions]
except AttributeError:
    pass
try:
    btck_logging_set_level_category = BITCOINKERNEL_LIB.btck_logging_set_level_category
    btck_logging_set_level_category.restype = None
    btck_logging_set_level_category.argtypes = [btck_LogCategory, btck_LogLevel]
except AttributeError:
    pass
try:
    btck_logging_enable_category = BITCOINKERNEL_LIB.btck_logging_enable_category
    btck_logging_enable_category.restype = None
    btck_logging_enable_category.argtypes = [btck_LogCategory]
except AttributeError:
    pass
try:
    btck_logging_disable_category = BITCOINKERNEL_LIB.btck_logging_disable_category
    btck_logging_disable_category.restype = None
    btck_logging_disable_category.argtypes = [btck_LogCategory]
except AttributeError:
    pass
try:
    btck_logging_connection_create = BITCOINKERNEL_LIB.btck_logging_connection_create
    btck_logging_connection_create.restype = ctypes.POINTER(struct_btck_LoggingConnection)
    btck_logging_connection_create.argtypes = [btck_LogCallback, ctypes.POINTER(None), btck_DestroyCallback]
except AttributeError:
    pass
try:
    btck_logging_connection_destroy = BITCOINKERNEL_LIB.btck_logging_connection_destroy
    btck_logging_connection_destroy.restype = None
    btck_logging_connection_destroy.argtypes = [ctypes.POINTER(struct_btck_LoggingConnection)]
except AttributeError:
    pass
try:
    btck_log_level_name = BITCOINKERNEL_LIB.btck_log_level_name
    btck_log_level_name.restype = ctypes.POINTER(ctypes.c_char)
    btck_log_level_name.argtypes = [btck_LogLevel]
except AttributeError:
    pass
try:
    btck_log_category_name = BITCOINKERNEL_LIB.btck_log_category_name
    btck_log_category_name.restype = ctypes.POINTER(ctypes.c_char)
    btck_log_category_name.argtypes = [btck_LogCategory]
except AttributeError:
    pass
try:
    btck_chain_parameters_create = BITCOINKERNEL_LIB.btck_chain_parameters_create
    btck_chain_parameters_create.restype = ctypes.POINTER(struct_btck_ChainParameters)
    btck_chain_parameters_create.argtypes = [btck_ChainType]
except AttributeError:
    pass
try:
    btck_chain_parameters_copy = BITCOINKERNEL_LIB.btck_chain_parameters_copy
    btck_chain_parameters_copy.restype = ctypes.POINTER(struct_btck_ChainParameters)
    btck_chain_parameters_copy.argtypes = [ctypes.POINTER(struct_btck_ChainParameters)]
except AttributeError:
    pass
try:
    btck_chain_parameters_destroy = BITCOINKERNEL_LIB.btck_chain_parameters_destroy
    btck_chain_parameters_destroy.restype = None
    btck_chain_parameters_destroy.argtypes = [ctypes.POINTER(struct_btck_ChainParameters)]
except AttributeError:
    pass
try:
    btck_context_options_create = BITCOINKERNEL_LIB.btck_context_options_create
    btck_context_options_create.restype = ctypes.POINTER(struct_btck_ContextOptions)
    btck_context_options_create.argtypes = []
except AttributeError:
    pass
try:
    btck_context_options_set_chainparams = BITCOINKERNEL_LIB.btck_context_options_set_chainparams
    btck_context_options_set_chainparams.restype = None
    btck_context_options_set_chainparams.argtypes = [ctypes.POINTER(struct_btck_ContextOptions), ctypes.POINTER(struct_btck_ChainParameters)]
except AttributeError:
    pass
try:
    btck_context_options_set_notifications = BITCOINKERNEL_LIB.btck_context_options_set_notifications
    btck_context_options_set_notifications.restype = None
    btck_context_options_set_notifications.argtypes = [ctypes.POINTER(struct_btck_ContextOptions), btck_NotificationInterfaceCallbacks]
except AttributeError:
    pass
try:
    btck_context_options_set_validation_interface = BITCOINKERNEL_LIB.btck_context_options_set_validation_interface
    btck_context_options_set_validation_interface.restype = None
    btck_context_options_set_validation_interface.argtypes = [ctypes.POINTER(struct_btck_ContextOptions), btck_ValidationInterfaceCallbacks]
except AttributeError:
    pass
try:
    btck_context_options_destroy = BITCOINKERNEL_LIB.btck_context_options_destroy
    btck_context_options_destroy.restype = None
    btck_context_options_destroy.argtypes = [ctypes.POINTER(struct_btck_ContextOptions)]
except AttributeError:
    pass
try:
    btck_context_create = BITCOINKERNEL_LIB.btck_context_create
    btck_context_create.restype = ctypes.POINTER(struct_btck_Context)
    btck_context_create.argtypes = [ctypes.POINTER(struct_btck_ContextOptions)]
except AttributeError:
    pass
try:
    btck_context_copy = BITCOINKERNEL_LIB.btck_context_copy
    btck_context_copy.restype = ctypes.POINTER(struct_btck_Context)
    btck_context_copy.argtypes = [ctypes.POINTER(struct_btck_Context)]
except AttributeError:
    pass
try:
    btck_context_interrupt = BITCOINKERNEL_LIB.btck_context_interrupt
    btck_context_interrupt.restype = ctypes.c_int32
    btck_context_interrupt.argtypes = [ctypes.POINTER(struct_btck_Context)]
except AttributeError:
    pass
try:
    btck_context_destroy = BITCOINKERNEL_LIB.btck_context_destroy
    btck_context_destroy.restype = None
    btck_context_destroy.argtypes = [ctypes.POINTER(struct_btck_Context)]
except AttributeError:
    pass
try:
    btck_block_tree_entry_get_previous = BITCOINKERNEL_LIB.btck_block_tree_entry_get_previous
    btck_block_tree_entry_get_previous.restype = ctypes.POINTER(struct_btck_BlockTreeEntry)
    btck_block_tree_entry_get_previous.argtypes = [ctypes.POINTER(struct_btck_BlockTreeEntry)]
except AttributeError:
    pass
int32_t = ctypes.c_int32
try:
    btck_block_tree_entry_get_height = BITCOINKERNEL_LIB.btck_block_tree_entry_get_height
    btck_block_tree_entry_get_height.restype = int32_t
    btck_block_tree_entry_get_height.argtypes = [ctypes.POINTER(struct_btck_BlockTreeEntry)]
except AttributeError:
    pass
try:
    btck_block_tree_entry_get_block_hash = BITCOINKERNEL_LIB.btck_block_tree_entry_get_block_hash
    btck_block_tree_entry_get_block_hash.restype = ctypes.POINTER(struct_btck_BlockHash)
    btck_block_tree_entry_get_block_hash.argtypes = [ctypes.POINTER(struct_btck_BlockTreeEntry)]
except AttributeError:
    pass
try:
    btck_chainstate_manager_options_create = BITCOINKERNEL_LIB.btck_chainstate_manager_options_create
    btck_chainstate_manager_options_create.restype = ctypes.POINTER(struct_btck_ChainstateManagerOptions)
    btck_chainstate_manager_options_create.argtypes = [ctypes.POINTER(struct_btck_Context), ctypes.POINTER(ctypes.c_char), size_t, ctypes.POINTER(ctypes.c_char), size_t]
except AttributeError:
    pass
try:
    btck_chainstate_manager_options_set_worker_threads_num = BITCOINKERNEL_LIB.btck_chainstate_manager_options_set_worker_threads_num
    btck_chainstate_manager_options_set_worker_threads_num.restype = None
    btck_chainstate_manager_options_set_worker_threads_num.argtypes = [ctypes.POINTER(struct_btck_ChainstateManagerOptions), ctypes.c_int32]
except AttributeError:
    pass
try:
    btck_chainstate_manager_options_set_wipe_dbs = BITCOINKERNEL_LIB.btck_chainstate_manager_options_set_wipe_dbs
    btck_chainstate_manager_options_set_wipe_dbs.restype = ctypes.c_int32
    btck_chainstate_manager_options_set_wipe_dbs.argtypes = [ctypes.POINTER(struct_btck_ChainstateManagerOptions), ctypes.c_int32, ctypes.c_int32]
except AttributeError:
    pass
try:
    btck_chainstate_manager_options_update_block_tree_db_in_memory = BITCOINKERNEL_LIB.btck_chainstate_manager_options_update_block_tree_db_in_memory
    btck_chainstate_manager_options_update_block_tree_db_in_memory.restype = None
    btck_chainstate_manager_options_update_block_tree_db_in_memory.argtypes = [ctypes.POINTER(struct_btck_ChainstateManagerOptions), ctypes.c_int32]
except AttributeError:
    pass
try:
    btck_chainstate_manager_options_update_chainstate_db_in_memory = BITCOINKERNEL_LIB.btck_chainstate_manager_options_update_chainstate_db_in_memory
    btck_chainstate_manager_options_update_chainstate_db_in_memory.restype = None
    btck_chainstate_manager_options_update_chainstate_db_in_memory.argtypes = [ctypes.POINTER(struct_btck_ChainstateManagerOptions), ctypes.c_int32]
except AttributeError:
    pass
try:
    btck_chainstate_manager_options_destroy = BITCOINKERNEL_LIB.btck_chainstate_manager_options_destroy
    btck_chainstate_manager_options_destroy.restype = None
    btck_chainstate_manager_options_destroy.argtypes = [ctypes.POINTER(struct_btck_ChainstateManagerOptions)]
except AttributeError:
    pass
try:
    btck_chainstate_manager_create = BITCOINKERNEL_LIB.btck_chainstate_manager_create
    btck_chainstate_manager_create.restype = ctypes.POINTER(struct_btck_ChainstateManager)
    btck_chainstate_manager_create.argtypes = [ctypes.POINTER(struct_btck_ChainstateManagerOptions)]
except AttributeError:
    pass
try:
    btck_chainstate_manager_import_blocks = BITCOINKERNEL_LIB.btck_chainstate_manager_import_blocks
    btck_chainstate_manager_import_blocks.restype = ctypes.c_int32
    btck_chainstate_manager_import_blocks.argtypes = [ctypes.POINTER(struct_btck_ChainstateManager), ctypes.POINTER(ctypes.POINTER(ctypes.c_char)), ctypes.POINTER(ctypes.c_uint64), size_t]
except AttributeError:
    pass
try:
    btck_chainstate_manager_process_block = BITCOINKERNEL_LIB.btck_chainstate_manager_process_block
    btck_chainstate_manager_process_block.restype = ctypes.c_int32
    btck_chainstate_manager_process_block.argtypes = [ctypes.POINTER(struct_btck_ChainstateManager), ctypes.POINTER(struct_btck_Block), ctypes.POINTER(ctypes.c_int32)]
except AttributeError:
    pass
try:
    btck_chainstate_manager_get_active_chain = BITCOINKERNEL_LIB.btck_chainstate_manager_get_active_chain
    btck_chainstate_manager_get_active_chain.restype = ctypes.POINTER(struct_btck_Chain)
    btck_chainstate_manager_get_active_chain.argtypes = [ctypes.POINTER(struct_btck_ChainstateManager)]
except AttributeError:
    pass
try:
    btck_chainstate_manager_get_block_tree_entry_by_hash = BITCOINKERNEL_LIB.btck_chainstate_manager_get_block_tree_entry_by_hash
    btck_chainstate_manager_get_block_tree_entry_by_hash.restype = ctypes.POINTER(struct_btck_BlockTreeEntry)
    btck_chainstate_manager_get_block_tree_entry_by_hash.argtypes = [ctypes.POINTER(struct_btck_ChainstateManager), ctypes.POINTER(struct_btck_BlockHash)]
except AttributeError:
    pass
try:
    btck_chainstate_manager_destroy = BITCOINKERNEL_LIB.btck_chainstate_manager_destroy
    btck_chainstate_manager_destroy.restype = None
    btck_chainstate_manager_destroy.argtypes = [ctypes.POINTER(struct_btck_ChainstateManager)]
except AttributeError:
    pass
try:
    btck_block_read = BITCOINKERNEL_LIB.btck_block_read
    btck_block_read.restype = ctypes.POINTER(struct_btck_Block)
    btck_block_read.argtypes = [ctypes.POINTER(struct_btck_ChainstateManager), ctypes.POINTER(struct_btck_BlockTreeEntry)]
except AttributeError:
    pass
try:
    btck_block_create = BITCOINKERNEL_LIB.btck_block_create
    btck_block_create.restype = ctypes.POINTER(struct_btck_Block)
    btck_block_create.argtypes = [ctypes.POINTER(None), size_t]
except AttributeError:
    pass
try:
    btck_block_copy = BITCOINKERNEL_LIB.btck_block_copy
    btck_block_copy.restype = ctypes.POINTER(struct_btck_Block)
    btck_block_copy.argtypes = [ctypes.POINTER(struct_btck_Block)]
except AttributeError:
    pass
try:
    btck_block_count_transactions = BITCOINKERNEL_LIB.btck_block_count_transactions
    btck_block_count_transactions.restype = size_t
    btck_block_count_transactions.argtypes = [ctypes.POINTER(struct_btck_Block)]
except AttributeError:
    pass
try:
    btck_block_get_transaction_at = BITCOINKERNEL_LIB.btck_block_get_transaction_at
    btck_block_get_transaction_at.restype = ctypes.POINTER(struct_btck_Transaction)
    btck_block_get_transaction_at.argtypes = [ctypes.POINTER(struct_btck_Block), size_t]
except AttributeError:
    pass
try:
    btck_block_get_hash = BITCOINKERNEL_LIB.btck_block_get_hash
    btck_block_get_hash.restype = ctypes.POINTER(struct_btck_BlockHash)
    btck_block_get_hash.argtypes = [ctypes.POINTER(struct_btck_Block)]
except AttributeError:
    pass
try:
    btck_block_to_bytes = BITCOINKERNEL_LIB.btck_block_to_bytes
    btck_block_to_bytes.restype = ctypes.c_int32
    btck_block_to_bytes.argtypes = [ctypes.POINTER(struct_btck_Block), btck_WriteBytes, ctypes.POINTER(None)]
except AttributeError:
    pass
try:
    btck_block_destroy = BITCOINKERNEL_LIB.btck_block_destroy
    btck_block_destroy.restype = None
    btck_block_destroy.argtypes = [ctypes.POINTER(struct_btck_Block)]
except AttributeError:
    pass
try:
    btck_block_validation_state_get_validation_mode = BITCOINKERNEL_LIB.btck_block_validation_state_get_validation_mode
    btck_block_validation_state_get_validation_mode.restype = btck_ValidationMode
    btck_block_validation_state_get_validation_mode.argtypes = [ctypes.POINTER(struct_btck_BlockValidationState)]
except AttributeError:
    pass
try:
    btck_block_validation_state_get_block_validation_result = BITCOINKERNEL_LIB.btck_block_validation_state_get_block_validation_result
    btck_block_validation_state_get_block_validation_result.restype = btck_BlockValidationResult
    btck_block_validation_state_get_block_validation_result.argtypes = [ctypes.POINTER(struct_btck_BlockValidationState)]
except AttributeError:
    pass
try:
    btck_chain_get_tip = BITCOINKERNEL_LIB.btck_chain_get_tip
    btck_chain_get_tip.restype = ctypes.POINTER(struct_btck_BlockTreeEntry)
    btck_chain_get_tip.argtypes = [ctypes.POINTER(struct_btck_Chain)]
except AttributeError:
    pass
try:
    btck_chain_get_height = BITCOINKERNEL_LIB.btck_chain_get_height
    btck_chain_get_height.restype = int32_t
    btck_chain_get_height.argtypes = [ctypes.POINTER(struct_btck_Chain)]
except AttributeError:
    pass
try:
    btck_chain_get_genesis = BITCOINKERNEL_LIB.btck_chain_get_genesis
    btck_chain_get_genesis.restype = ctypes.POINTER(struct_btck_BlockTreeEntry)
    btck_chain_get_genesis.argtypes = [ctypes.POINTER(struct_btck_Chain)]
except AttributeError:
    pass
try:
    btck_chain_get_by_height = BITCOINKERNEL_LIB.btck_chain_get_by_height
    btck_chain_get_by_height.restype = ctypes.POINTER(struct_btck_BlockTreeEntry)
    btck_chain_get_by_height.argtypes = [ctypes.POINTER(struct_btck_Chain), ctypes.c_int32]
except AttributeError:
    pass
try:
    btck_chain_contains = BITCOINKERNEL_LIB.btck_chain_contains
    btck_chain_contains.restype = ctypes.c_int32
    btck_chain_contains.argtypes = [ctypes.POINTER(struct_btck_Chain), ctypes.POINTER(struct_btck_BlockTreeEntry)]
except AttributeError:
    pass
try:
    btck_block_spent_outputs_read = BITCOINKERNEL_LIB.btck_block_spent_outputs_read
    btck_block_spent_outputs_read.restype = ctypes.POINTER(struct_btck_BlockSpentOutputs)
    btck_block_spent_outputs_read.argtypes = [ctypes.POINTER(struct_btck_ChainstateManager), ctypes.POINTER(struct_btck_BlockTreeEntry)]
except AttributeError:
    pass
try:
    btck_block_spent_outputs_copy = BITCOINKERNEL_LIB.btck_block_spent_outputs_copy
    btck_block_spent_outputs_copy.restype = ctypes.POINTER(struct_btck_BlockSpentOutputs)
    btck_block_spent_outputs_copy.argtypes = [ctypes.POINTER(struct_btck_BlockSpentOutputs)]
except AttributeError:
    pass
try:
    btck_block_spent_outputs_count = BITCOINKERNEL_LIB.btck_block_spent_outputs_count
    btck_block_spent_outputs_count.restype = size_t
    btck_block_spent_outputs_count.argtypes = [ctypes.POINTER(struct_btck_BlockSpentOutputs)]
except AttributeError:
    pass
try:
    btck_block_spent_outputs_get_transaction_spent_outputs_at = BITCOINKERNEL_LIB.btck_block_spent_outputs_get_transaction_spent_outputs_at
    btck_block_spent_outputs_get_transaction_spent_outputs_at.restype = ctypes.POINTER(struct_btck_TransactionSpentOutputs)
    btck_block_spent_outputs_get_transaction_spent_outputs_at.argtypes = [ctypes.POINTER(struct_btck_BlockSpentOutputs), size_t]
except AttributeError:
    pass
try:
    btck_block_spent_outputs_destroy = BITCOINKERNEL_LIB.btck_block_spent_outputs_destroy
    btck_block_spent_outputs_destroy.restype = None
    btck_block_spent_outputs_destroy.argtypes = [ctypes.POINTER(struct_btck_BlockSpentOutputs)]
except AttributeError:
    pass
try:
    btck_transaction_spent_outputs_copy = BITCOINKERNEL_LIB.btck_transaction_spent_outputs_copy
    btck_transaction_spent_outputs_copy.restype = ctypes.POINTER(struct_btck_TransactionSpentOutputs)
    btck_transaction_spent_outputs_copy.argtypes = [ctypes.POINTER(struct_btck_TransactionSpentOutputs)]
except AttributeError:
    pass
try:
    btck_transaction_spent_outputs_count = BITCOINKERNEL_LIB.btck_transaction_spent_outputs_count
    btck_transaction_spent_outputs_count.restype = size_t
    btck_transaction_spent_outputs_count.argtypes = [ctypes.POINTER(struct_btck_TransactionSpentOutputs)]
except AttributeError:
    pass
try:
    btck_transaction_spent_outputs_get_coin_at = BITCOINKERNEL_LIB.btck_transaction_spent_outputs_get_coin_at
    btck_transaction_spent_outputs_get_coin_at.restype = ctypes.POINTER(struct_btck_Coin)
    btck_transaction_spent_outputs_get_coin_at.argtypes = [ctypes.POINTER(struct_btck_TransactionSpentOutputs), size_t]
except AttributeError:
    pass
try:
    btck_transaction_spent_outputs_destroy = BITCOINKERNEL_LIB.btck_transaction_spent_outputs_destroy
    btck_transaction_spent_outputs_destroy.restype = None
    btck_transaction_spent_outputs_destroy.argtypes = [ctypes.POINTER(struct_btck_TransactionSpentOutputs)]
except AttributeError:
    pass
try:
    btck_transaction_input_copy = BITCOINKERNEL_LIB.btck_transaction_input_copy
    btck_transaction_input_copy.restype = ctypes.POINTER(struct_btck_TransactionInput)
    btck_transaction_input_copy.argtypes = [ctypes.POINTER(struct_btck_TransactionInput)]
except AttributeError:
    pass
try:
    btck_transaction_input_get_out_point = BITCOINKERNEL_LIB.btck_transaction_input_get_out_point
    btck_transaction_input_get_out_point.restype = ctypes.POINTER(struct_btck_TransactionOutPoint)
    btck_transaction_input_get_out_point.argtypes = [ctypes.POINTER(struct_btck_TransactionInput)]
except AttributeError:
    pass
try:
    btck_transaction_input_destroy = BITCOINKERNEL_LIB.btck_transaction_input_destroy
    btck_transaction_input_destroy.restype = None
    btck_transaction_input_destroy.argtypes = [ctypes.POINTER(struct_btck_TransactionInput)]
except AttributeError:
    pass
try:
    btck_transaction_out_point_copy = BITCOINKERNEL_LIB.btck_transaction_out_point_copy
    btck_transaction_out_point_copy.restype = ctypes.POINTER(struct_btck_TransactionOutPoint)
    btck_transaction_out_point_copy.argtypes = [ctypes.POINTER(struct_btck_TransactionOutPoint)]
except AttributeError:
    pass
uint32_t = ctypes.c_uint32
try:
    btck_transaction_out_point_get_index = BITCOINKERNEL_LIB.btck_transaction_out_point_get_index
    btck_transaction_out_point_get_index.restype = uint32_t
    btck_transaction_out_point_get_index.argtypes = [ctypes.POINTER(struct_btck_TransactionOutPoint)]
except AttributeError:
    pass
try:
    btck_transaction_out_point_get_txid = BITCOINKERNEL_LIB.btck_transaction_out_point_get_txid
    btck_transaction_out_point_get_txid.restype = ctypes.POINTER(struct_btck_Txid)
    btck_transaction_out_point_get_txid.argtypes = [ctypes.POINTER(struct_btck_TransactionOutPoint)]
except AttributeError:
    pass
try:
    btck_transaction_out_point_destroy = BITCOINKERNEL_LIB.btck_transaction_out_point_destroy
    btck_transaction_out_point_destroy.restype = None
    btck_transaction_out_point_destroy.argtypes = [ctypes.POINTER(struct_btck_TransactionOutPoint)]
except AttributeError:
    pass
try:
    btck_txid_copy = BITCOINKERNEL_LIB.btck_txid_copy
    btck_txid_copy.restype = ctypes.POINTER(struct_btck_Txid)
    btck_txid_copy.argtypes = [ctypes.POINTER(struct_btck_Txid)]
except AttributeError:
    pass
try:
    btck_txid_equals = BITCOINKERNEL_LIB.btck_txid_equals
    btck_txid_equals.restype = ctypes.c_int32
    btck_txid_equals.argtypes = [ctypes.POINTER(struct_btck_Txid), ctypes.POINTER(struct_btck_Txid)]
except AttributeError:
    pass
try:
    btck_txid_to_bytes = BITCOINKERNEL_LIB.btck_txid_to_bytes
    btck_txid_to_bytes.restype = None
    btck_txid_to_bytes.argtypes = [ctypes.POINTER(struct_btck_Txid), ctypes.c_ubyte * 32]
except AttributeError:
    pass
try:
    btck_txid_destroy = BITCOINKERNEL_LIB.btck_txid_destroy
    btck_txid_destroy.restype = None
    btck_txid_destroy.argtypes = [ctypes.POINTER(struct_btck_Txid)]
except AttributeError:
    pass
try:
    btck_coin_copy = BITCOINKERNEL_LIB.btck_coin_copy
    btck_coin_copy.restype = ctypes.POINTER(struct_btck_Coin)
    btck_coin_copy.argtypes = [ctypes.POINTER(struct_btck_Coin)]
except AttributeError:
    pass
try:
    btck_coin_confirmation_height = BITCOINKERNEL_LIB.btck_coin_confirmation_height
    btck_coin_confirmation_height.restype = uint32_t
    btck_coin_confirmation_height.argtypes = [ctypes.POINTER(struct_btck_Coin)]
except AttributeError:
    pass
try:
    btck_coin_is_coinbase = BITCOINKERNEL_LIB.btck_coin_is_coinbase
    btck_coin_is_coinbase.restype = ctypes.c_int32
    btck_coin_is_coinbase.argtypes = [ctypes.POINTER(struct_btck_Coin)]
except AttributeError:
    pass
try:
    btck_coin_get_output = BITCOINKERNEL_LIB.btck_coin_get_output
    btck_coin_get_output.restype = ctypes.POINTER(struct_btck_TransactionOutput)
    btck_coin_get_output.argtypes = [ctypes.POINTER(struct_btck_Coin)]
except AttributeError:
    pass
try:
    btck_coin_destroy = BITCOINKERNEL_LIB.btck_coin_destroy
    btck_coin_destroy.restype = None
    btck_coin_destroy.argtypes = [ctypes.POINTER(struct_btck_Coin)]
except AttributeError:
    pass
try:
    btck_block_hash_create = BITCOINKERNEL_LIB.btck_block_hash_create
    btck_block_hash_create.restype = ctypes.POINTER(struct_btck_BlockHash)
    btck_block_hash_create.argtypes = [ctypes.c_ubyte * 32]
except AttributeError:
    pass
try:
    btck_block_hash_equals = BITCOINKERNEL_LIB.btck_block_hash_equals
    btck_block_hash_equals.restype = ctypes.c_int32
    btck_block_hash_equals.argtypes = [ctypes.POINTER(struct_btck_BlockHash), ctypes.POINTER(struct_btck_BlockHash)]
except AttributeError:
    pass
try:
    btck_block_hash_copy = BITCOINKERNEL_LIB.btck_block_hash_copy
    btck_block_hash_copy.restype = ctypes.POINTER(struct_btck_BlockHash)
    btck_block_hash_copy.argtypes = [ctypes.POINTER(struct_btck_BlockHash)]
except AttributeError:
    pass
try:
    btck_block_hash_to_bytes = BITCOINKERNEL_LIB.btck_block_hash_to_bytes
    btck_block_hash_to_bytes.restype = None
    btck_block_hash_to_bytes.argtypes = [ctypes.POINTER(struct_btck_BlockHash), ctypes.c_ubyte * 32]
except AttributeError:
    pass
try:
    btck_block_hash_destroy = BITCOINKERNEL_LIB.btck_block_hash_destroy
    btck_block_hash_destroy.restype = None
    btck_block_hash_destroy.argtypes = [ctypes.POINTER(struct_btck_BlockHash)]
except AttributeError:
    pass
__all__ = \
    ['btck_Block', 'btck_BlockHash', 'btck_BlockSpentOutputs',
    'btck_BlockTreeEntry', 'btck_BlockValidationResult',
    'btck_BlockValidationState', 'btck_Chain', 'btck_ChainParameters',
    'btck_ChainType', 'btck_ChainstateManager',
    'btck_ChainstateManagerOptions', 'btck_Coin', 'btck_Context',
    'btck_ContextOptions', 'btck_DestroyCallback', 'btck_LogCallback',
    'btck_LogCategory', 'btck_LogEntry', 'btck_LogLevel',
    'btck_LoggingConnection', 'btck_LoggingOptions',
    'btck_NotificationInterfaceCallbacks', 'btck_NotifyBlockTip',
    'btck_NotifyFatalError', 'btck_NotifyFlushError',
    'btck_NotifyHeaderTip', 'btck_NotifyProgress',
    'btck_NotifyWarningSet', 'btck_NotifyWarningUnset',
    'btck_ScriptPubkey', 'btck_ScriptVerificationFlags',
    'btck_ScriptVerifyStatus', 'btck_SynchronizationState',
    'btck_Transaction', 'btck_TransactionInput',
    'btck_TransactionOutPoint', 'btck_TransactionOutput',
    'btck_TransactionSpentOutputs', 'btck_Txid',
    'btck_ValidationInterfaceBlockChecked',
    'btck_ValidationInterfaceBlockConnected',
    'btck_ValidationInterfaceBlockDisconnected',
    'btck_ValidationInterfaceCallbacks',
    'btck_ValidationInterfacePoWValidBlock', 'btck_ValidationMode',
    'btck_Warning', 'btck_WriteBytes', 'btck_block_copy',
    'btck_block_count_transactions', 'btck_block_create',
    'btck_block_destroy', 'btck_block_get_hash',
    'btck_block_get_transaction_at', 'btck_block_hash_copy',
    'btck_block_hash_create', 'btck_block_hash_destroy',
    'btck_block_hash_equals', 'btck_block_hash_to_bytes',
    'btck_block_read', 'btck_block_spent_outputs_copy',
    'btck_block_spent_outputs_count',
    'btck_block_spent_outputs_destroy',
    'btck_block_spent_outputs_get_transaction_spent_outputs_at',
    'btck_block_spent_outputs_read', 'btck_block_to_bytes',
    'btck_block_tree_entry_get_block_hash',
    'btck_block_tree_entry_get_height',
    'btck_block_tree_entry_get_previous',
    'btck_block_validation_state_get_block_validation_result',
    'btck_block_validation_state_get_validation_mode',
    'btck_chain_contains', 'btck_chain_get_by_height',
    'btck_chain_get_genesis', 'btck_chain_get_height',
    'btck_chain_get_tip', 'btck_chain_parameters_copy',
    'btck_chain_parameters_create', 'btck_chain_parameters_destroy',
    'btck_chainstate_manager_create',
    'btck_chainstate_manager_destroy',
    'btck_chainstate_manager_get_active_chain',
    'btck_chainstate_manager_get_block_tree_entry_by_hash',
    'btck_chainstate_manager_import_blocks',
    'btck_chainstate_manager_options_create',
    'btck_chainstate_manager_options_destroy',
    'btck_chainstate_manager_options_set_wipe_dbs',
    'btck_chainstate_manager_options_set_worker_threads_num',
    'btck_chainstate_manager_options_update_block_tree_db_in_memory',
    'btck_chainstate_manager_options_update_chainstate_db_in_memory',
    'btck_chainstate_manager_process_block',
    'btck_coin_confirmation_height', 'btck_coin_copy',
    'btck_coin_destroy', 'btck_coin_get_output',
    'btck_coin_is_coinbase', 'btck_context_copy',
    'btck_context_create', 'btck_context_destroy',
    'btck_context_interrupt', 'btck_context_options_create',
    'btck_context_options_destroy',
    'btck_context_options_set_chainparams',
    'btck_context_options_set_notifications',
    'btck_context_options_set_validation_interface',
    'btck_log_category_name', 'btck_log_level_name',
    'btck_logging_connection_create',
    'btck_logging_connection_destroy', 'btck_logging_disable',
    'btck_logging_disable_category', 'btck_logging_enable_category',
    'btck_logging_set_level_category', 'btck_logging_set_options',
    'btck_script_pubkey_copy', 'btck_script_pubkey_create',
    'btck_script_pubkey_destroy', 'btck_script_pubkey_to_bytes',
    'btck_script_pubkey_verify', 'btck_transaction_copy',
    'btck_transaction_count_inputs', 'btck_transaction_count_outputs',
    'btck_transaction_create', 'btck_transaction_destroy',
    'btck_transaction_get_input_at', 'btck_transaction_get_output_at',
    'btck_transaction_get_txid', 'btck_transaction_input_copy',
    'btck_transaction_input_destroy',
    'btck_transaction_input_get_out_point',
    'btck_transaction_out_point_copy',
    'btck_transaction_out_point_destroy',
    'btck_transaction_out_point_get_index',
    'btck_transaction_out_point_get_txid',
    'btck_transaction_output_copy', 'btck_transaction_output_create',
    'btck_transaction_output_destroy',
    'btck_transaction_output_get_amount',
    'btck_transaction_output_get_script_pubkey',
    'btck_transaction_spent_outputs_copy',
    'btck_transaction_spent_outputs_count',
    'btck_transaction_spent_outputs_destroy',
    'btck_transaction_spent_outputs_get_coin_at',
    'btck_transaction_to_bytes', 'btck_txid_copy',
    'btck_txid_destroy', 'btck_txid_equals', 'btck_txid_to_bytes',
    'int32_t', 'int64_t', 'size_t', 'struct_btck_Block',
    'struct_btck_BlockHash', 'struct_btck_BlockSpentOutputs',
    'struct_btck_BlockTreeEntry', 'struct_btck_BlockValidationState',
    'struct_btck_Chain', 'struct_btck_ChainParameters',
    'struct_btck_ChainstateManager',
    'struct_btck_ChainstateManagerOptions', 'struct_btck_Coin',
    'struct_btck_Context', 'struct_btck_ContextOptions',
    'struct_btck_LogEntry', 'struct_btck_LoggingConnection',
    'struct_btck_LoggingOptions',
    'struct_btck_NotificationInterfaceCallbacks',
    'struct_btck_ScriptPubkey', 'struct_btck_Transaction',
    'struct_btck_TransactionInput', 'struct_btck_TransactionOutPoint',
    'struct_btck_TransactionOutput',
    'struct_btck_TransactionSpentOutputs', 'struct_btck_Txid',
    'struct_btck_ValidationInterfaceCallbacks', 'uint32_t']
