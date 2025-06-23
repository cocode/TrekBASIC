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
        self.loop_stack = []  # Track nested FOR loops

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
                elif isinstance(stmt, ParsedStatementFor):
                    var_names.add(stmt._index_clause)
        
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
        elif isinstance(stmt, ParsedStatementFor):
             self._codegen_for(stmt)
        elif isinstance(stmt, ParsedStatementNext):
             self._codegen_next(stmt)
        elif stmt.keyword.name == "END":
             self.builder.ret(ir.Constant(ir.IntType(32), 0))
        # Add other statements here
        else:
            print(f"Warning: Codegen for statement '{type(stmt).__name__}' not implemented.")

    def _codegen_for(self, stmt):
        """Generate LLVM IR for a FOR loop"""
        # Get the loop variable
        loop_var = stmt._index_clause
        var_ptr = self.symbol_table.get(loop_var)
        if not var_ptr:
            var_ptr = self.builder.alloca(ir.DoubleType(), name=loop_var)
            self.symbol_table[loop_var] = var_ptr
        
        # Parse and evaluate start, end, and step expressions
        lexer = get_lexer()
        start_tokens = lexer.lex(stmt._start_clause)
        end_tokens = lexer.lex(stmt._to_clause)
        step_tokens = lexer.lex(stmt._step_clause)
        
        start_val = self._codegen_expr(start_tokens)
        end_val = self._codegen_expr(end_tokens)
        step_val = self._codegen_expr(step_tokens)
        
        # Store initial value
        self.builder.store(start_val, var_ptr)
        
        # Create loop blocks
        func = self.builder.block.function
        cond_block = func.append_basic_block(name=f"for_{loop_var}_cond")
        body_block = func.append_basic_block(name=f"for_{loop_var}_body")
        after_block = func.append_basic_block(name=f"for_{loop_var}_after")
        
        # Branch to condition block
        self.builder.branch(cond_block)
        
        # Condition block
        self.builder.position_at_end(cond_block)
        current_val = self.builder.load(var_ptr, name=f"load_{loop_var}")
        
        # Compare current value with end value
        # For positive step: current <= end
        # For negative step: current >= end
        zero = ir.Constant(ir.DoubleType(), 0.0)
        step_positive = self.builder.fcmp_ordered(">=", step_val, zero, name="step_positive")
        
        # Create conditional comparison
        cmp_positive = self.builder.fcmp_ordered("<=", current_val, end_val, name="cmp_positive")
        cmp_negative = self.builder.fcmp_ordered(">=", current_val, end_val, name="cmp_negative")
        
        # Select the appropriate comparison based on step sign
        condition = self.builder.select(step_positive, cmp_positive, cmp_negative, name="loop_condition")
        
        # Branch based on condition
        self.builder.cbranch(condition, body_block, after_block)
        
        # Push loop context onto stack
        self.loop_stack.append({
            'var': loop_var,
            'var_ptr': var_ptr,
            'step_val': step_val,
            'cond_block': cond_block,
            'after_block': after_block
        })
        
        # Position builder at start of body block
        self.builder.position_at_end(body_block)

    def _codegen_next(self, stmt):
        """Generate LLVM IR for a NEXT statement"""
        if not self.loop_stack:
            raise Exception("NEXT without corresponding FOR")
        
        loop_context = self.loop_stack.pop()
        loop_var = stmt.loop_var
        
        if loop_var != loop_context['var']:
            raise Exception(f"NEXT variable {loop_var} doesn't match FOR variable {loop_context['var']}")
        
        # Increment the loop variable
        current_val = self.builder.load(loop_context['var_ptr'], name=f"load_{loop_var}")
        new_val = self.builder.fadd(current_val, loop_context['step_val'], name=f"inc_{loop_var}")
        self.builder.store(new_val, loop_context['var_ptr'])
        
        # Branch back to condition block
        self.builder.branch(loop_context['cond_block'])
        
        # Position builder at after block for any code that follows
        self.builder.position_at_end(loop_context['after_block'])

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