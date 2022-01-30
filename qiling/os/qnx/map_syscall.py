#!/usr/bin/env python3
#
# Cross Platform and Multi Architecture Advanced Binary Emulation Framework
#

from qiling.const import QL_ARCH
from qiling.os.posix.posix import SYSCALL_PREF

def map_syscall(ql, syscall_num):
    if ql.arch.type == QL_ARCH.ARM:
        return f'{SYSCALL_PREF}{arm_syscall_table[syscall_num]}'

# Source: https://github.com/vocho/openqnx
# trunk/services/system/public/sys/kercalls.h
arm_syscall_table = {
    4261412864: 'clock_cycles',
    1: 'trace_event',
    2: 'ring0',
    3: 'spare1',
    4: 'spare2',
    5: 'spare3',
    6: 'spare4',
    7: 'sys_cpupage_get',
    8: 'sys_cpupage_set',
    9: 'sys_spare1',
    10: 'msg_current',
    11: 'msg_sendv',
    12: 'msg_sendvnc',
    13: 'msg_error',
    14: 'msg_receivev',
    15: 'msg_replyv',
    16: 'msg_readv',
    17: 'msg_writev',
    18: 'msg_readwritev',
    19: 'msg_info',
    20: 'msg_send_pulse',
    21: 'msg_deliver_event',
    22: 'msg_keydata',
    23: 'msg_readiov',
    24: 'msg_receivepulsev',
    25: 'msg_verify_event',
    26: 'signal_kill',
    27: 'signal_return',
    28: 'signal_fault',
    29: 'signal_action',
    30: 'signal_procmask',
    31: 'signal_suspend',
    32: 'signal_waitinfo',
    33: 'signal_spare1',
    34: 'signal_spare2',
    35: 'channel_create',
    36: 'channel_destroy',
    37: 'chancon_attr',
    38: 'channel_spare1',
    39: 'connect_attach',
    40: 'connect_detach',
    41: 'connect_server_info',
    42: 'connect_client_info',
    43: 'connect_flags',
    44: 'connect_spare1',
    45: 'connect_spare2',
    46: 'thread_create',
    47: 'thread_destroy',
    48: 'thread_destroyall',
    49: 'thread_detach',
    50: 'thread_join',
    51: 'thread_cancel',
    52: 'thread_ctl',
    53: 'thread_spare1',
    54: 'thread_spare2',
    55: 'interrupt_attach',
    56: 'interrupt_detach_func',
    57: 'interrupt_detach',
    58: 'interrupt_wait',
    59: 'interrupt_mask',
    60: 'interrupt_unmask',
    61: 'interrupt_spare1',
    62: 'interrupt_spare2',
    63: 'interrupt_spare3',
    64: 'interrupt_spare4',
    65: 'clock_time',
    66: 'clock_adjust',
    67: 'clock_period',
    68: 'clock_id',
    69: 'clock_spare2',
    70: 'timer_create',
    71: 'timer_destroy',
    72: 'timer_settime',
    73: 'timer_info',
    74: 'timer_alarm',
    75: 'timer_timeout',
    76: 'timer_spare1',
    77: 'timer_spare2',
    78: 'sync_create',
    79: 'sync_destroy',
    80: 'sync_mutex_lock',
    81: 'sync_mutex_unlock',
    82: 'sync_condvar_wait',
    83: 'sync_condvar_signal',
    84: 'sync_sem_post',
    85: 'sync_sem_wait',
    86: 'sync_ctl',
    87: 'sync_mutex_revive',
    88: 'sched_get',
    89: 'sched_set',
    90: 'sched_yield',
    91: 'sched_info',
    92: 'sched_ctl',
    93: 'net_cred',
    94: 'net_vtid',
    95: 'net_unblock',
    96: 'net_infoscoid',
    97: 'net_signal_kill',
    98: 'net_spare1',
    99: 'net_spare2',
    100: 'mt_ctl',
    101: 'bad',
}