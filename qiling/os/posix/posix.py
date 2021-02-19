#!/usr/bin/env python3
# 
# Cross Platform and Multi Architecture Advanced Binary Emulation Framework
#

from inspect import signature

from unicorn.arm64_const import UC_ARM64_REG_X8, UC_ARM64_REG_X16
from unicorn.arm_const import UC_ARM_REG_R7
from unicorn.mips_const import UC_MIPS_REG_V0
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_RAX

from qiling.const import QL_ARCH, QL_OS, QL_INTERCEPT, QL_CALL_BLOCK, QL_OS_POSIX
from qiling.exception import QlErrorSyscallNotFound
from qiling.os.os import QlOs
from qiling.os.posix.const import errors
from qiling.utils import QlFileDes, ostype_convert_str, ql_get_module_function, ql_syscall_mapping_function

from qiling.os.posix.syscall import *
from qiling.os.linux.syscall import *
from qiling.os.macos.syscall import *
from qiling.os.freebsd.syscall import *

from qiling.os.linux.function_hook import ARMFunctionArg, MIPS32FunctionArg, ARM64FunctionArg, X86FunctionArg, X64FunctionArg

SYSCALL_PREF: str = f'ql_syscall_'

def getNameFromErrorCode(ret):
    """
    Return the hex representation of a return value and if possible
    add the corresponding error name to it.
    :param ret: Return value of a syscall.
    :return: The string representation of the error.
    """
    if -ret in errors:
        return hex(ret) + "(" + errors[-ret] + ")"
    else:
        return hex(ret)


class QlOsPosix(QlOs):
    def __init__(self, ql):
        super(QlOsPosix, self).__init__(ql)
        self.ql = ql
        self.sigaction_act = []
        
        if self.ql.root == True:
            self.uid = 0
            self.gid = 0
        else:    
            self.uid = self.profile.getint("KERNEL","uid")
            self.gid = self.profile.getint("KERNEL","gid")

        self.ipv6 = self.profile.getboolean("NETWORK","ipv6")
        self.bindtolocalhost = self.profile.getboolean("NETWORK","bindtolocalhost")
        self.fd = QlFileDes([0] * 256)

        self.posix_syscall_hooks = {
            QL_INTERCEPT.CALL : {},
            QL_INTERCEPT.ENTER: {},
            QL_INTERCEPT.EXIT : {}
        }

        self.__syscall_id_reg = {
            QL_ARCH.ARM64: UC_ARM64_REG_X8,
            QL_ARCH.ARM  : UC_ARM_REG_R7,
            QL_ARCH.MIPS : UC_MIPS_REG_V0,
            QL_ARCH.X86  : UC_X86_REG_EAX,
            QL_ARCH.X8664: UC_X86_REG_RAX
        }[self.ql.archtype]

        # handle a special case
        if (self.ql.archtype == QL_ARCH.ARM64) and (self.ql.ostype == QL_OS.MACOS):
            self.__syscall_id_reg = UC_ARM64_REG_X16
        if self.ql.ostype in QL_OS_POSIX:
            self.fd[0] = self.stdin
            self.fd[1] = self.stdout
            self.fd[2] = self.stderr

        for _ in range(256):
            self.sigaction_act.append(0)

    # ql.syscall - get syscall for all posix series
    @property
    def syscall(self):
        return self.get_syscall()

    def set_syscall(self, target: Union[int, str], handler: Callable, intercept: QL_INTERCEPT):
        if type(target) is str:
            target = f'{SYSCALL_PREF}{target}'

        # BUG: workaround missing arg
        if intercept is None:
            intercept = QL_INTERCEPT.CALL

        self.posix_syscall_hooks[intercept][target] = handler

        # if intercept == QL_INTERCEPT.CALL:
        #     if self.ql.ostype in (QL_OS.WINDOWS, QL_OS.UEFI):
        #         self.set_api(target_syscall, intercept_function)

    # ql.func_arg - get syscall for all posix series
    @property
    def function_arg(self):
        if self.ql.ostype in (QL_OS_POSIX):
            # ARM
            if self.ql.archtype== QL_ARCH.ARM:
                return ARMFunctionArg(self.ql)

            # MIPS32
            elif self.ql.archtype== QL_ARCH.MIPS:
                return MIPS32FunctionArg(self.ql)

            # ARM64
            elif self.ql.archtype== QL_ARCH.ARM64:
                return ARM64FunctionArg(self.ql)

            # X86
            elif  self.ql.archtype== QL_ARCH.X86:
                return X86FunctionArg(self.ql)

            # X8664
            elif  self.ql.archtype== QL_ARCH.X8664:
                return X64FunctionArg(self.ql)
            else:
                raise

    def load_syscall(self, intno=None):
        # import syscall mapping function
        map_syscall = ql_syscall_mapping_function(self.ql.ostype)
        self.syscall_name = map_syscall(self.ql, self.syscall)

        if self.dict_posix_onEnter_syscall.get(self.syscall_name) != None:
            self.syscall_onEnter = self.dict_posix_onEnter_syscall.get(self.syscall_name)
        elif self.dict_posix_onEnter_syscall_by_num.get(self.syscall) != None:
            self.syscall_onEnter = self.dict_posix_onEnter_syscall_by_num.get(self.syscall)
        else:
            self.syscall_onEnter = None    
        
        if self.dict_posix_onExit_syscall.get(self.syscall_name) != None:
            self.syscall_onExit = self.dict_posix_onExit_syscall.get(self.syscall_name)
        elif self.dict_posix_onExit_syscall_by_num.get(self.syscall) != None:
            self.syscall_onExit = self.dict_posix_onExit_syscall_by_num.get(self.syscall)
        else:
            self.syscall_onExit = None    
        
        self.syscall_map = self.dict_posix_syscall_by_num.get(self.syscall)
        syscall_name_str = None
        

        if self.syscall_map is not None:
            self.syscall_name = self.syscall_map.__name__
        else:
            self.syscall_name = map_syscall(self.ql, self.syscall)
            _ostype_str = ostype_convert_str(self.ql.ostype)
            _posix_syscall = ql_get_module_function(f"qiling.os.posix", "syscall")
            _os_syscall = ql_get_module_function(f"qiling.os.{_ostype_str.lower()}", "syscall")
            
            if self.syscall_name not in dir(_posix_syscall) \
            and self.syscall_name not in dir(_os_syscall):

                syscall_name_str = self.syscall_name
                self.syscall_map = None
                self.syscall_name = None

                
            if self.syscall_name is not None:
                replace_func = self.dict_posix_syscall.get(self.syscall_name)
                if replace_func is not None:
                    self.syscall_map = replace_func
                    self.syscall_name = replace_func.__name__
                else:
                    self.syscall_map = eval(self.syscall_name)
            else:
                self.syscall_map = None
                self.syscall_name = None

        if self.syscall_map is not None:
            self.syscalls.setdefault(self.syscall_name, []).append({
                "params": {
                    "param0": self.get_func_arg()[0],
                    "param1": self.get_func_arg()[1],
                    "param2": self.get_func_arg()[2],
                    "param3": self.get_func_arg()[3],
                    "param4": self.get_func_arg()[4],
                    "param5": self.get_func_arg()[5]
                },
                "result": None,
                "address": self.ql.reg.arch_pc,
                "return_address": None,
                "position": self.syscalls_counter
            })

            self.syscalls_counter += 1

            try:                
                if self.syscall_onEnter is None:
                    ret = 0
                else:
                    ret = self.syscall_onEnter(self.ql, self.get_func_arg()[0], self.get_func_arg()[1], self.get_func_arg()[2], self.get_func_arg()[3], self.get_func_arg()[4], self.get_func_arg()[5])

                if isinstance(ret, int) == False or ret & QL_CALL_BLOCK == 0:
                    args = []
                    for n, argname in enumerate(signature(self.syscall_map).parameters.values()):
                        argname = str(argname)
                        if not n or argname.startswith("*"):
                            # first arg for syscalls is ql
                            continue
                        else:
                            # cut the first part of the arg if it is of form fstatat64_fd
                            argname = argname if "_" not in argname else "".join(argname.split("_")[1:])
                            args.append(f"{argname}={hex(self.get_func_arg()[n-1])}")
                    args = ", ".join(args)
                    self.ql.log.info("0x%x: %s(%s)" % (self.ql.reg.arch_pc, self.syscall_map.__name__[11:], args))
                    ret = self.syscall_map(self.ql, self.get_func_arg()[0], self.get_func_arg()[1], self.get_func_arg()[2], self.get_func_arg()[3], self.get_func_arg()[4], self.get_func_arg()[5])
                    if ret is not None and isinstance(ret, int):
                        # each name has a list of calls, we want the last one and we want to update the return value
                        self.syscalls[self.syscall_name][-1]["result"] = ret
                        ret = self.set_syscall_return(ret)
                        self.ql.log.debug("%s() = %s" % (self.syscall_map.__name__[11:], getNameFromErrorCode(ret)))

                if self.syscall_onExit is not None:
                    self.syscall_onExit(self.ql, self.get_func_arg()[0], self.get_func_arg()[1], self.get_func_arg()[2], self.get_func_arg()[3], self.get_func_arg()[4], self.get_func_arg()[5])

            except KeyboardInterrupt:
                raise
            except Exception as e:
                self.ql.log.exception("")
                self.ql.log.info("Syscall ERROR: %s DEBUG: %s" % (self.syscall_name, e))
                raise e
        else:
            self.ql.log.warning(
                "0x%x: syscall %s number = 0x%x(%d) not implemented" % (self.ql.reg.arch_pc, syscall_name_str, self.syscall, self.syscall))
            if self.ql.debug_stop:
                raise QlErrorSyscallNotFound("Syscall Not Found")

    def get_syscall(self) -> int:
        return self.ql.reg.read(self.__syscall_id_reg)
    def set_syscall_return(self, regreturn):
        if self.ql.archtype == QL_ARCH.ARM:  # ARM
            self.ql.reg.r0 = regreturn

        elif self.ql.archtype == QL_ARCH.ARM64:  # ARM64
            self.ql.reg.x0 = regreturn

        elif self.ql.archtype == QL_ARCH.X86:  # X86
            self.ql.reg.eax = regreturn

        elif self.ql.archtype == QL_ARCH.X8664:  # X8664
            self.ql.reg.rax = regreturn

        elif self.ql.archtype == QL_ARCH.MIPS:  # MIPSE32EL
            if regreturn < 0 and regreturn > -1134:
                a3return = 1
                regreturn = - regreturn
            else:
                a3return = 0

            self.ql.reg.v0 = regreturn
            self.ql.reg.a3 = a3return
        return regreturn

    # get syscall
    def get_func_arg(self):
        if self.ql.archtype == QL_ARCH.ARM64:
            param0 = self.ql.reg.x0
            param1 = self.ql.reg.x1
            param2 = self.ql.reg.x2
            param3 = self.ql.reg.x3
            param4 = self.ql.reg.x4
            param5 = self.ql.reg.x5
        elif self.ql.archtype == QL_ARCH.ARM:
            param0 = self.ql.reg.r0
            param1 = self.ql.reg.r1
            param2 = self.ql.reg.r2
            param3 = self.ql.reg.r3
            param4 = self.ql.reg.r4
            param5 = self.ql.reg.r5
        elif self.ql.archtype == QL_ARCH.MIPS:
            param0 = self.ql.reg.a0
            param1 = self.ql.reg.a1
            param2 = self.ql.reg.a2
            param3 = self.ql.reg.a3
            param4 = self.ql.reg.sp
            param4 = param4 + 0x10
            param5 = self.ql.reg.sp
            param5 = param5 + 0x14
        elif self.ql.archtype == QL_ARCH.X86:
            param0 = self.ql.reg.ebx
            param1 = self.ql.reg.ecx
            param2 = self.ql.reg.edx
            param3 = self.ql.reg.esi
            param4 = self.ql.reg.edi
            param5 = self.ql.reg.ebp
        elif self.ql.archtype == QL_ARCH.X8664:
            param0 = self.ql.reg.rdi
            param1 = self.ql.reg.rsi
            param2 = self.ql.reg.rdx
            param3 = self.ql.reg.r10
            param4 = self.ql.reg.r8
            param5 = self.ql.reg.r9

        return [param0, param1, param2, param3, param4, param5]
