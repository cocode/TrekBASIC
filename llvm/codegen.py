from llvmlite import ir, binding
from basic_parsing import (
    ParsedStatementLet, ParsedStatementPrint, ParsedStatementIf,
    ParsedStatementFor, ParsedStatementNext, ParsedStatementGo,
    ParsedStatementOnGoto, ParsedStatementInput, ParsedStatementDim
)
from basic_expressions import Expression
from basic_lexer import get_lexer
from basic_utils import smart_split
from basic_types import lexer_token, BasicSyntaxError, assert_syntax, OP_TOKEN, UNARY_MINUS, SymbolType, UndefinedSymbol
from basic_operators import get_op_def, get_precedence


class LLVMCodeGenerator:
    def __init__(self, program):
        self.program = program
        self.module = ir.Module(name="basic_program")
        self.module.triple = binding.get_default_triple()

        # External functions
        printf_ty = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8))], var_arg=True)
        self.printf = ir.Function(self.module, printf_ty, name="printf")

        self.builder = None
        self.symbol_table = {}
        self.line_blocks = {}

    def generate_ir(self):
        main_func_type = ir.FunctionType(ir.IntType(32), [])
        main_func = ir.Function(self.module, main_func_type, name="main")
        
        entry_block = main_func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(entry_block)

        # Allocate variables
        self._allocate_variables()

        # Create blocks for each line
        for line in self.program:
            block = main_func.append_basic_block(name=f"line_{line.line}")
            self.line_blocks[line.line] = block
        
        # Branch to first line
        if self.program:
            self.builder.branch(self.line_blocks[self.program[0].line])
        else:
            self.builder.ret(ir.Constant(ir.IntType(32), 0))

        # Generate code for each line
        for i, line in enumerate(self.program):
            self.builder.position_at_end(self.line_blocks[line.line])
            
            for stmt in line.stmts:
                self._generate_statement_ir(stmt)
            
            # Branch to next line if not a branching statement
            if not self.builder.block.is_terminated:
                if line.next is not None:
                     next_line_num = self.program[line.next].line
                     self.builder.branch(self.line_blocks[next_line_num])
                else:
                     self.builder.ret(ir.Constant(ir.IntType(32), 0))

        return str(self.module)

    def _allocate_variables(self):
        var_names = set()
        for line in self.program:
            for stmt in line.stmts:
                if isinstance(stmt, ParsedStatementLet):
                    var_names.add(stmt._variable)
        
        for var_name in var_names:
            # Assuming all variables are floats for now (f64)
            var_ptr = self.builder.alloca(ir.DoubleType(), name=var_name)
            self.symbol_table[var_name] = var_ptr

    def _generate_statement_ir(self, stmt):
        if isinstance(stmt, ParsedStatementLet):
            self._codegen_let(stmt)
        elif isinstance(stmt, ParsedStatementPrint):
            self._codegen_print(stmt)
        elif isinstance(stmt, ParsedStatementGo):
             self._codegen_goto(stmt)
        elif stmt.keyword.name == "END":
             self.builder.ret(ir.Constant(ir.IntType(32), 0))
        # Add other statements here
        else:
            print(f"Warning: Codegen for statement '{type(stmt).__name__}' not implemented.")

    def _codegen_goto(self, stmt):
        target_line = int(stmt.destination)
        if target_line in self.line_blocks:
            self.builder.branch(self.line_blocks[target_line])
        else:
            raise Exception(f"GOTO target line not found: {target_line}")

    def _codegen_let(self, stmt):
        var_name = stmt._variable
        var_ptr = self.symbol_table.get(var_name)
        if not var_ptr:
            # This is a simplification. All variables should be declared at the start.
            # For dynamic languages like BASIC, we might need a different strategy.
            var_ptr = self.builder.alloca(ir.DoubleType(), name=var_name)
            self.symbol_table[var_name] = var_ptr
        
        value = self._codegen_expr(stmt._tokens)
        self.builder.store(value, var_ptr)

    def _codegen_print(self, stmt: ParsedStatementPrint):
        lexer = get_lexer()
        for output in stmt._outputs:
            if output.startswith('"') and output.endswith('"'):
                # String literal
                str_val = output[1:-1]
                # Create a global string constant
                fmt = str_val + "\\n\\0"
                c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                                    bytearray(fmt.encode("utf8")))
                global_fmt = ir.GlobalVariable(self.module, c_fmt.type, name=f"fmt_{hash(fmt)}")
                global_fmt.linkage = 'internal'
                global_fmt.global_constant = True
                global_fmt.initializer = c_fmt
                fmt_ptr = self.builder.bitcast(global_fmt, ir.IntType(8).as_pointer())
                self.builder.call(self.printf, [fmt_ptr])
            else:
                # Expression
                tokens = lexer.lex(output)
                val = self._codegen_expr(tokens)

                # Print float
                fmt = "%f\\n\\0"
                c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                                    bytearray(fmt.encode("utf8")))
                global_fmt = ir.GlobalVariable(self.module, c_fmt.type, name="fmt_float")
                global_fmt.linkage = 'internal'
                global_fmt.global_constant = True
                global_fmt.initializer = c_fmt
                fmt_ptr = self.builder.bitcast(global_fmt, ir.IntType(8).as_pointer())

                self.builder.call(self.printf, [fmt_ptr, val])

    def _one_op(self, op_stack, data_stack):
        op = op_stack.pop()
        
        right = data_stack.pop()
        left = data_stack.pop()

        if op.token == '+':
            result = self.builder.fadd(left, right, name="addtmp")
        elif op.token == '-':
            result = self.builder.fsub(left, right, name="subtmp")
        elif op.token == '*':
            result = self.builder.fmul(left, right, name="multmp")
        elif op.token == '/':
            result = self.builder.fdiv(left, right, name="divtmp")
        else:
            raise NotImplementedError(f"Operator {op.token} not implemented")
        
        data_stack.append(result)

    def _codegen_expr(self, tokens):
        data_stack = []
        op_stack = []
        is_unary_context = True

        for token in tokens:
            if token.type == 'num':
                data_stack.append(ir.Constant(ir.DoubleType(), float(token.token)))
                is_unary_context = False
            elif token.type == 'id':
                data_stack.append(self.builder.load(self.symbol_table[token.token], name=f"load_{token.token}"))
                is_unary_context = False
            elif token.type == 'op':
                current_op_token = token
                if current_op_token.token == "-" and is_unary_context:
                    # This is a unary minus. We'll handle it by making it 0 - value.
                    # This is a simplification. A better way would be a specific unary minus op.
                    data_stack.append(ir.Constant(ir.DoubleType(), 0.0))

                while op_stack and op_stack[-1].token != '(' and get_precedence(op_stack[-1]) >= get_precedence(current_op_token):
                    self._one_op(op_stack, data_stack)
                
                if current_op_token.token == ')':
                    op_stack.pop() # Pop '('
                else:
                    op_stack.append(current_op_token)
                
                is_unary_context = (current_op_token.token != ')')

        while op_stack:
            self._one_op(op_stack, data_stack)

        if len(data_stack) == 1:
            return data_stack[0]
        else:
            raise Exception("Expression evaluation failed, stack has multiple values.")

def generate_llvm_ir(program):
    codegen = LLVMCodeGenerator(program)
    return codegen.generate_ir()