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
        printf_type = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer()], var_arg=True)
        self.printf = ir.Function(self.module, printf_type, name="printf")

        self.builder = None
        self.symbol_table = {}
        self.array_info = {}  # Track array dimensions and storage
        self.line_blocks = {}
        self.loop_stack = []  # Track nested FOR loops
        self.if_condition = None  # Track current IF condition
        self.return_stack = []  # Track GOSUB return addresses
        self.current_line_index = 0
        
        # Runtime return address stack
        self.return_stack_size = 100  # Maximum depth
        self.return_stack_ptr = None
        self.return_stack_top = None

    def generate_ir(self):
        main_func_type = ir.FunctionType(ir.IntType(32), [])
        main_func = ir.Function(self.module, main_func_type, name="main")
        
        entry_block = main_func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(entry_block)

        # Initialize runtime return address stack
        self._init_return_stack()

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
            self.if_condition = None  # Reset IF condition for each line
            self.current_line_index = i  # Track current line index for GOSUB
            
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

    def _init_return_stack(self):
        """Initialize the runtime return address stack"""
        # Create global array for return addresses (store line numbers as integers)
        return_stack_type = ir.ArrayType(ir.IntType(32), self.return_stack_size)
        self.return_stack_ptr = ir.GlobalVariable(self.module, return_stack_type, name="return_stack")
        self.return_stack_ptr.linkage = 'internal'
        self.return_stack_ptr.global_constant = False
        self.return_stack_ptr.initializer = ir.Constant(return_stack_type, [ir.Constant(ir.IntType(32), 0)] * self.return_stack_size)
        
        # Create global variable for stack top
        self.return_stack_top = ir.GlobalVariable(self.module, ir.IntType(32), name="return_stack_top")
        self.return_stack_top.linkage = 'internal'
        self.return_stack_top.global_constant = False
        self.return_stack_top.initializer = ir.Constant(ir.IntType(32), 0)

    def _allocate_variables(self):
        var_names = set()
        array_names = set()
        
        for line in self.program:
            for stmt in line.stmts:
                if isinstance(stmt, ParsedStatementLet):
                    var_names.add(stmt._variable)
                elif isinstance(stmt, ParsedStatementFor):
                    var_names.add(stmt._index_clause)
                elif isinstance(stmt, ParsedStatementDim):
                    for name, dimensions in stmt._dimensions:
                        array_names.add(name)
        
        # Allocate regular variables
        for var_name in var_names:
            var_ptr = self.builder.alloca(ir.DoubleType(), name=var_name)
            self.symbol_table[var_name] = var_ptr
        
        # Arrays will be allocated in DIM statements, not here

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
        elif isinstance(stmt, ParsedStatementIf):
             self._codegen_if(stmt)
        elif isinstance(stmt, ParsedStatementDim):
             self._codegen_dim(stmt)
        elif stmt.keyword.name == "END":
             self.builder.ret(ir.Constant(ir.IntType(32), 0))
        elif stmt.keyword.name == "RETURN":
             self._codegen_return(stmt)
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

    def _codegen_return(self, stmt):
        """Generate LLVM IR for a RETURN statement"""
        # Check if stack is empty
        stack_top = self.builder.load(self.return_stack_top, name="stack_top")
        zero = ir.Constant(ir.IntType(32), 0)
        stack_empty = self.builder.icmp_signed("==", stack_top, zero)
        
        # Create blocks for error and normal return
        func = self.builder.block.function
        error_block = func.append_basic_block(name=f"return_error_{self.builder.block.name}")
        return_block = func.append_basic_block(name=f"return_normal_{self.builder.block.name}")
        
        # Branch based on stack emptiness
        self.builder.cbranch(stack_empty, error_block, return_block)
        
        # Error block: raise exception (for now, just return)
        self.builder.position_at_end(error_block)
        self.builder.ret(ir.Constant(ir.IntType(32), 1))  # Error return code
        
        # Normal return block
        self.builder.position_at_end(return_block)
        
        # Pop return address from stack
        line_number = self._pop_return_address()
        print(f"DEBUG: RETURN to line {line_number}")
        
        # Use a switch statement to branch to the correct block
        default_block = func.append_basic_block(name="return_invalid")
        switch_inst = self.builder.switch(line_number, default_block)
        for ln, block in self.line_blocks.items():
            switch_inst.add_case(ir.Constant(ir.IntType(32), ln), block)
        # Default: return error
        self.builder.position_at_end(default_block)
        self.builder.ret(ir.Constant(ir.IntType(32), 1))

    def _codegen_let(self, stmt):
        var_name = stmt._variable
        
        # Check if this is an array assignment
        if '(' in var_name:
            # Parse array name and indices
            array_name = var_name[:var_name.find('(')]
            indices_str = var_name[var_name.find('(')+1:var_name.rfind(')')]
            indices = [self._codegen_expr(get_lexer().lex(idx.strip())) for idx in indices_str.split(',')]
            
            # Get array element pointer
            element_ptr = self._codegen_array_access(array_name, indices)
            
            # Store the value
            value = self._codegen_expr(stmt._tokens)
            
            # If we're in an IF context, make this a conditional assignment
            if self.if_condition is not None:
                # Create blocks for then and after
                func = self.builder.block.function
                then_block = func.append_basic_block(name=f"if_then_{self.builder.block.name}")
                after_block = func.append_basic_block(name=f"if_after_{self.builder.block.name}")
                
                # Branch based on condition
                self.builder.cbranch(self.if_condition, then_block, after_block)
                
                # THEN block: do the assignment
                self.builder.position_at_end(then_block)
                self.builder.store(value, element_ptr)
                self.builder.branch(after_block)
                
                # AFTER block: continue normally
                self.builder.position_at_end(after_block)
                self.if_condition = None  # Clear the condition
            else:
                # Normal assignment
                self.builder.store(value, element_ptr)
        else:
            # Regular variable assignment
            var_ptr = self.symbol_table.get(var_name)
            if not var_ptr:
                var_ptr = self.builder.alloca(ir.DoubleType(), name=var_name)
                self.symbol_table[var_name] = var_ptr
            
            value = self._codegen_expr(stmt._tokens)
            
            # If we're in an IF context, make this a conditional assignment
            if self.if_condition is not None:
                # Create blocks for then and after
                func = self.builder.block.function
                then_block = func.append_basic_block(name=f"if_then_{self.builder.block.name}")
                after_block = func.append_basic_block(name=f"if_after_{self.builder.block.name}")
                
                # Branch based on condition
                self.builder.cbranch(self.if_condition, then_block, after_block)
                
                # THEN block: do the assignment
                self.builder.position_at_end(then_block)
                self.builder.store(value, var_ptr)
                self.builder.branch(after_block)
                
                # AFTER block: continue normally
                self.builder.position_at_end(after_block)
                self.if_condition = None  # Clear the condition
            else:
                # Normal assignment
                self.builder.store(value, var_ptr)

    def _codegen_print(self, stmt: ParsedStatementPrint):
        lexer = get_lexer()
        
        # If we're in an IF context, make this a conditional print
        if self.if_condition is not None:
            # Create blocks for then and after
            func = self.builder.block.function
            then_block = func.append_basic_block(name=f"if_then_{self.builder.block.name}")
            after_block = func.append_basic_block(name=f"if_after_{self.builder.block.name}")
            
            # Branch based on condition
            self.builder.cbranch(self.if_condition, then_block, after_block)
            
            # THEN block: do the printing
            self.builder.position_at_end(then_block)
            self._do_print(stmt, lexer)
            self.builder.branch(after_block)
            
            # AFTER block: continue normally
            self.builder.position_at_end(after_block)
            self.if_condition = None  # Clear the condition
        else:
            # Normal print
            self._do_print(stmt, lexer)

    def _do_print(self, stmt, lexer):
        """Helper method to do the actual printing"""
        for output in stmt._outputs:
            if output.startswith('"') and output.endswith('"'):
                # String literal
                str_val = output[1:-1]
                # Process escape sequences
                str_val = str_val.encode('utf-8').decode('unicode_escape')
                # Create a global string constant
                fmt = str_val + "\n\0"
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
                fmt = "%f\n\0"
                c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                                    bytearray(fmt.encode("utf8")))
                global_fmt = ir.GlobalVariable(self.module, c_fmt.type, name="fmt_float")
                global_fmt.linkage = 'internal'
                global_fmt.global_constant = True
                global_fmt.initializer = c_fmt
                fmt_ptr = self.builder.bitcast(global_fmt, ir.IntType(8).as_pointer())

                self.builder.call(self.printf, [fmt_ptr, val])

    def _codegen_expr(self, tokens):
        data_stack = []
        op_stack = []
        is_unary_context = True
        i = 0

        print(f"DEBUG: Processing tokens: {tokens}")  # Debug output

        while i < len(tokens):
            token = tokens[i]
            print(f"DEBUG: Token: {token.type} = '{token.token}'")  # Debug output
            
            if token.type == 'num':
                data_stack.append(ir.Constant(ir.DoubleType(), float(token.token)))
                is_unary_context = False
            elif token.type == 'id':
                # Check if this is followed by array access
                if i + 1 < len(tokens) and tokens[i + 1].token == '(':
                    # This is array access - handle it specially
                    array_name = token.token
                    if array_name not in self.array_info:
                        raise Exception(f"Array {array_name} not declared")
                    
                    # Find the closing parenthesis and extract indices
                    indices = []
                    i += 2  # Skip the opening parenthesis
                    while i < len(tokens) and tokens[i].token != ')':
                        if tokens[i].type == 'num':
                            indices.append(ir.Constant(ir.DoubleType(), float(tokens[i].token)))
                        elif tokens[i].type == 'id':
                            indices.append(self.builder.load(self.symbol_table[tokens[i].token], name=f"load_{tokens[i].token}"))
                        else:
                            raise Exception(f"Invalid array index: {tokens[i].token}")
                        i += 1
                        if i < len(tokens) and tokens[i].token == ',':
                            i += 1  # Skip comma
                    
                    if i >= len(tokens) or tokens[i].token != ')':
                        raise Exception("Missing closing parenthesis in array access")
                    
                    # Get array element
                    element_ptr = self._codegen_array_access(array_name, indices)
                    data_stack.append(self.builder.load(element_ptr, name=f"load_{array_name}_element"))
                else:
                    # Regular variable
                    if token.token in self.array_info:
                        # This is an array variable, we need to handle it specially
                        # For now, just load the array storage pointer
                        array_storage = self.symbol_table[token.token]
                        data_stack.append(array_storage)
                    else:
                        # Regular variable
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
            
            i += 1

        while op_stack:
            self._one_op(op_stack, data_stack)

        print(f"DEBUG: Final data_stack size: {len(data_stack)}")  # Debug output
        if len(data_stack) == 1:
            return data_stack[0]
        else:
            raise Exception("Expression evaluation failed, stack has multiple values.")

    def _one_op(self, op_stack, data_stack):
        op = op_stack.pop()
        
        if op.token == '@':  # ARRAY_ACCESS operator
            # Array access: pop array name and indices, return element value
            indices = data_stack.pop()
            array_name = data_stack.pop()
            
            # For now, handle simple 1D array access
            # In a full implementation, we'd need to parse the array name and indices properly
            # This is a simplified version
            if array_name in self.array_info:
                array_info = self.array_info[array_name]
                array_storage = array_info['storage']
                
                # Convert index to 0-based
                index_val = self.builder.fptoui(indices, ir.IntType(32))
                one = ir.Constant(ir.IntType(32), 1)
                zero_based_index = self.builder.sub(index_val, one)
                
                # Get element pointer and load value
                element_ptr = self.builder.gep(array_storage, [ir.Constant(ir.IntType(32), 0), zero_based_index])
                result = self.builder.load(element_ptr, name="array_element")
                data_stack.append(result)
            else:
                raise Exception(f"Array {array_name} not found")
        else:
            # Regular binary operators
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
            elif op.token == '=':
                # Equal comparison
                cmp_result = self.builder.fcmp_ordered("==", left, right, name="cmptmp")
                result = self.builder.uitofp(cmp_result, ir.DoubleType(), name="booltmp")
            elif op.token == '<>':
                # Not equal comparison
                cmp_result = self.builder.fcmp_ordered("!=", left, right, name="cmptmp")
                result = self.builder.uitofp(cmp_result, ir.DoubleType(), name="booltmp")
            elif op.token == '<':
                # Less than comparison
                cmp_result = self.builder.fcmp_ordered("<", left, right, name="cmptmp")
                result = self.builder.uitofp(cmp_result, ir.DoubleType(), name="booltmp")
            elif op.token == '>':
                # Greater than comparison
                cmp_result = self.builder.fcmp_ordered(">", left, right, name="cmptmp")
                result = self.builder.uitofp(cmp_result, ir.DoubleType(), name="booltmp")
            elif op.token == '<=':
                # Less than or equal comparison
                cmp_result = self.builder.fcmp_ordered("<=", left, right, name="cmptmp")
                result = self.builder.uitofp(cmp_result, ir.DoubleType(), name="booltmp")
            elif op.token == '>=':
                # Greater than or equal comparison
                cmp_result = self.builder.fcmp_ordered(">=", left, right, name="cmptmp")
                result = self.builder.uitofp(cmp_result, ir.DoubleType(), name="booltmp")
            else:
                raise NotImplementedError(f"Operator {op.token} not implemented")
            
            data_stack.append(result)

    def _codegen_if(self, stmt):
        """Generate LLVM IR for an IF/THEN statement"""
        # Evaluate the condition
        condition_val = self._codegen_expr(stmt._tokens)
        
        # Convert to boolean (non-zero is true)
        zero = ir.Constant(ir.DoubleType(), 0.0)
        condition = self.builder.fcmp_ordered("!=", condition_val, zero, name="if_condition")
        
        # Store the condition for this line
        self.if_condition = condition

    def _codegen_goto(self, stmt):
        target_line = int(stmt.destination)
        if target_line in self.line_blocks:
            # Check if this is GOSUB or GOTO
            is_gosub = stmt.keyword.name == "GOSUB"
            
            # If we're in an IF context, make this a conditional GOTO/GOSUB
            if self.if_condition is not None:
                # Create blocks for then and after
                func = self.builder.block.function
                then_block = func.append_basic_block(name=f"if_then_{self.builder.block.name}")
                after_block = func.append_basic_block(name=f"if_after_{self.builder.block.name}")
                
                # Branch based on condition
                self.builder.cbranch(self.if_condition, then_block, after_block)
                
                # THEN block: do the GOTO/GOSUB
                self.builder.position_at_end(then_block)
                if is_gosub:
                    # For GOSUB, push return address and branch
                    if self.current_line_index + 1 < len(self.program):
                        next_line = self.program[self.current_line_index + 1].line
                        self._push_return_address(next_line)
                        print(f"DEBUG: GOSUB from line {self.program[self.current_line_index].line} to {target_line}, return to {next_line}")
                    self.builder.branch(self.line_blocks[target_line])
                else:
                    # Normal GOTO
                    self.builder.branch(self.line_blocks[target_line])
                
                # AFTER block: continue normally
                self.builder.position_at_end(after_block)
                self.if_condition = None  # Clear the condition
            else:
                # Normal unconditional GOTO/GOSUB
                if is_gosub:
                    # For GOSUB, push return address and branch
                    # Find the next line to return to using tracked index
                    if self.current_line_index + 1 < len(self.program):
                        next_line = self.program[self.current_line_index + 1].line
                        self._push_return_address(next_line)
                        print(f"DEBUG: GOSUB from line {self.program[self.current_line_index].line} to {target_line}, return to {next_line}")
                    
                    self.builder.branch(self.line_blocks[target_line])
                else:
                    # Normal GOTO
                    self.builder.branch(self.line_blocks[target_line])
        else:
            raise Exception(f"GOTO/GOSUB target line not found: {target_line}")

    def _push_return_address(self, line_number):
        """Push a return address onto the runtime stack"""
        # Load current stack top
        stack_top = self.builder.load(self.return_stack_top, name="stack_top")
        
        # Store line number at stack[top]
        stack_ptr = self.builder.gep(self.return_stack_ptr, [ir.Constant(ir.IntType(32), 0), stack_top])
        self.builder.store(ir.Constant(ir.IntType(32), line_number), stack_ptr)
        
        # Increment stack top
        new_top = self.builder.add(stack_top, ir.Constant(ir.IntType(32), 1))
        self.builder.store(new_top, self.return_stack_top)

    def _pop_return_address(self):
        """Pop a return address from the runtime stack"""
        # Decrement stack top
        stack_top = self.builder.load(self.return_stack_top, name="stack_top")
        new_top = self.builder.sub(stack_top, ir.Constant(ir.IntType(32), 1))
        self.builder.store(new_top, self.return_stack_top)
        
        # Load line number from stack[top-1]
        stack_ptr = self.builder.gep(self.return_stack_ptr, [ir.Constant(ir.IntType(32), 0), new_top])
        line_number = self.builder.load(stack_ptr, name="return_line")
        
        return line_number

    def _codegen_dim(self, stmt):
        """Generate LLVM IR for a DIM statement"""
        for name, dimensions in stmt._dimensions:
            # Calculate total size needed
            total_size = 1
            for dim in dimensions:
                total_size *= (dim + 1)  # +1 because BASIC arrays are 0-based internally
            
            # Allocate array storage directly
            array_type = ir.ArrayType(ir.DoubleType(), total_size)
            array_storage = self.builder.alloca(array_type, name=f"{name}_storage")
            
            # Initialize all elements to 0.0
            zero = ir.Constant(ir.DoubleType(), 0.0)
            for i in range(total_size):
                element_ptr = self.builder.gep(array_storage, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), i)])
                self.builder.store(zero, element_ptr)
            
            # Store array info for access
            self.array_info[name] = {
                'storage': array_storage,
                'dimensions': dimensions,
                'total_size': total_size
            }
            
            # Store the array storage directly in symbol table
            self.symbol_table[name] = array_storage

    def _codegen_array_access(self, array_name, indices):
        """Generate LLVM IR for array access"""
        if array_name not in self.array_info:
            raise Exception(f"Array {array_name} not declared")
        
        array_info = self.array_info[array_name]
        array_storage = array_info['storage']
        dimensions = array_info['dimensions']
        
        # Convert indices to 0-based and calculate offset
        if len(indices) != len(dimensions):
            raise Exception(f"Array {array_name} has {len(dimensions)} dimensions, got {len(indices)} indices")
        
        # Calculate offset: index1 * dim2 * dim3 + index2 * dim3 + index3
        offset = ir.Constant(ir.IntType(32), 0)
        multiplier = 1
        
        for i in range(len(indices) - 1, -1, -1):
            # Convert 1-based index to 0-based
            index_val = self.builder.fptoui(indices[i], ir.IntType(32))
            one = ir.Constant(ir.IntType(32), 1)
            zero_based_index = self.builder.sub(index_val, one)
            
            # Add to offset
            index_offset = self.builder.mul(zero_based_index, ir.Constant(ir.IntType(32), multiplier))
            offset = self.builder.add(offset, index_offset)
            
            # Update multiplier for next dimension
            if i > 0:
                multiplier *= (dimensions[i] + 1)
        
        # Get element pointer
        element_ptr = self.builder.gep(array_storage, [ir.Constant(ir.IntType(32), 0), offset])
        return element_ptr


def generate_llvm_ir(program):
    codegen = LLVMCodeGenerator(program)
    return codegen.generate_ir()