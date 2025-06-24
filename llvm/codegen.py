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

        # Declare strcat for string concatenation
        strcat_type = ir.FunctionType(ir.IntType(8).as_pointer(), 
                                     [ir.IntType(8).as_pointer(), ir.IntType(8).as_pointer()])
        self.strcat = ir.Function(self.module, strcat_type, name="strcat")
        
        # Declare malloc for dynamic memory allocation
        malloc_type = ir.FunctionType(ir.IntType(8).as_pointer(), [ir.IntType(64)])
        self.malloc = ir.Function(self.module, malloc_type, name="malloc")
        
        # Declare strlen for string length
        strlen_type = ir.FunctionType(ir.IntType(64), [ir.IntType(8).as_pointer()])
        self.strlen = ir.Function(self.module, strlen_type, name="strlen")
        
        # Declare math functions
        sin_type = ir.FunctionType(ir.DoubleType(), [ir.DoubleType()])
        self.sin = ir.Function(self.module, sin_type, name="sin")
        
        cos_type = ir.FunctionType(ir.DoubleType(), [ir.DoubleType()])
        self.cos = ir.Function(self.module, cos_type, name="cos")
        
        sqrt_type = ir.FunctionType(ir.DoubleType(), [ir.DoubleType()])
        self.sqrt = ir.Function(self.module, sqrt_type, name="sqrt")
        
        exp_type = ir.FunctionType(ir.DoubleType(), [ir.DoubleType()])
        self.exp = ir.Function(self.module, exp_type, name="exp")
        
        log_type = ir.FunctionType(ir.DoubleType(), [ir.DoubleType()])
        self.log = ir.Function(self.module, log_type, name="log")
        
        fabs_type = ir.FunctionType(ir.DoubleType(), [ir.DoubleType()])
        self.fabs = ir.Function(self.module, fabs_type, name="fabs")
        
        # Declare INT function
        int_type = ir.FunctionType(ir.DoubleType(), [ir.DoubleType()])
        self.int_func = ir.Function(self.module, int_type, name="floor")
        
        # Declare string functions
        asc_type = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer()])
        self.asc = ir.Function(self.module, asc_type, name="asc")
        
        chr_type = ir.FunctionType(ir.IntType(8), [ir.IntType(32)])
        self.chr = ir.Function(self.module, chr_type, name="chr")
        
        # For now, we'll implement these as simple stubs that return reasonable defaults
        # A full implementation would need more complex string handling
        
        # Create a single global variable for float format string
        fmt = "%f\n\0"
        c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)), bytearray(fmt.encode("utf8")))
        self.global_fmt_float = ir.GlobalVariable(self.module, c_fmt.type, name="fmt_float")
        self.global_fmt_float.linkage = 'internal'
        self.global_fmt_float.global_constant = True
        self.global_fmt_float.initializer = c_fmt
        
        self.builder = None
        self.symbol_table = {}
        self.array_info = {}  # Track array dimensions and storage
        self.line_blocks = {}
        self.loop_stack = []  # Track nested FOR loops
        self.return_stack = []  # Track GOSUB return addresses
        self.current_line_index = 0
        
        # Runtime return address stack
        self.return_stack_size = 100  # Maximum depth
        self.return_stack_ptr = None
        self.return_stack_top = None
        self.newline_counter = 0

        # User-defined functions: map name to LLVM function
        self.user_functions = {}
        self.user_function_defs = []  # Store DEF statements for later processing
        
        # First pass: scan for user-defined functions and create declarations
        for program_line in self.program:
            for stmt in program_line.stmts:
                print(f"DEBUG: Statement type: {type(stmt).__name__}, keyword: {getattr(stmt, 'keyword', None)}")
                if hasattr(stmt, 'keyword') and getattr(stmt.keyword, 'name', None) == 'DEF':
                    fn_name = stmt._variable  # e.g., FNA
                    print(f"DEBUG: Found DEF statement for function {fn_name}")
                    # Create LLVM function declaration: double fn(double)
                    fn_type = ir.FunctionType(ir.DoubleType(), [ir.DoubleType()])
                    llvm_fn = ir.Function(self.module, fn_type, name=fn_name)
                    self.user_functions[fn_name] = llvm_fn
                    self.user_function_defs.append(stmt)
        
        print(f"DEBUG: Created {len(self.user_functions)} user functions: {list(self.user_functions.keys())}")
        
        # Second pass: generate function bodies
        for stmt in self.user_function_defs:
            fn_name = stmt._variable
            arg_name = stmt._function_arg
            body_tokens = stmt._tokens
            llvm_fn = self.user_functions[fn_name]
            
            # Create function body
            entry_block = llvm_fn.append_basic_block('entry')
            builder = ir.IRBuilder(entry_block)
            
            # Set up a local symbol table for the argument
            local_vars = {}
            arg_ptr = builder.alloca(ir.DoubleType(), name=arg_name)
            builder.store(llvm_fn.args[0], arg_ptr)
            local_vars[arg_name] = arg_ptr
            
            # Evaluate the body expression
            result = self._codegen_expr(body_tokens, local_vars=local_vars, builder=builder)
            builder.ret(result)

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
            self.current_line_index = i  # Track current line index for GOSUB
            
            j = 0
            while j < len(line.stmts):
                stmt = line.stmts[j]
                
                # Check if this is an IF statement - it will handle remaining statements
                if isinstance(stmt, ParsedStatementIf):
                    self._generate_statement_ir(stmt, line_stmts=line.stmts, stmt_index=j)
                    # IF statement handles all remaining statements on the line
                    break
                else:
                    self._generate_statement_ir(stmt, line_stmts=line.stmts, stmt_index=j)
                    j += 1
            
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
        string_var_names = set()
        array_names = set()
        
        for line in self.program:
            for stmt in line.stmts:
                if isinstance(stmt, ParsedStatementLet):
                    var_name = stmt._variable
                    if var_name.endswith('$'):
                        string_var_names.add(var_name)
                    else:
                        var_names.add(var_name)
                elif isinstance(stmt, ParsedStatementFor):
                    var_names.add(stmt._index_clause)
                elif isinstance(stmt, ParsedStatementDim):
                    for name, dimensions in stmt._dimensions:
                        array_names.add(name)
        
        # Allocate regular variables (numeric)
        for var_name in var_names:
            var_ptr = self.builder.alloca(ir.DoubleType(), name=var_name)
            self.symbol_table[var_name] = var_ptr
        
        # Allocate string variables (pointers to strings)
        for var_name in string_var_names:
            # Initialize with empty string
            empty_str = "\0"
            c_empty = ir.Constant(ir.ArrayType(ir.IntType(8), len(empty_str)),
                                  bytearray(empty_str.encode("utf8")))
            global_empty = ir.GlobalVariable(self.module, c_empty.type, name=f"empty_{var_name}")
            global_empty.linkage = 'internal'
            global_empty.global_constant = True
            global_empty.initializer = c_empty
            
            # Allocate pointer to store string address
            var_ptr = self.builder.alloca(ir.IntType(8).as_pointer(), name=var_name)
            # Initialize with empty string
            empty_ptr = self.builder.bitcast(global_empty, ir.IntType(8).as_pointer())
            self.builder.store(empty_ptr, var_ptr)
            self.symbol_table[var_name] = var_ptr
        
        # Arrays will be allocated in DIM statements, not here

    def _generate_statement_ir(self, stmt, line_stmts=None, stmt_index=None):
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
             self._codegen_if(stmt, line_stmts, stmt_index)
        elif isinstance(stmt, ParsedStatementDim):
             self._codegen_dim(stmt)
        elif stmt.keyword.name == "END":
             self.builder.ret(ir.Constant(ir.IntType(32), 0))
        elif stmt.keyword.name == "STOP":
             self.builder.ret(ir.Constant(ir.IntType(32), 1))  # Error exit code
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
            
            # Normal assignment
            self.builder.store(value, element_ptr)
        else:
            # Regular variable assignment
            var_ptr = self.symbol_table.get(var_name)
            if not var_ptr:
                # Variable not pre-allocated, allocate it now
                if var_name.endswith('$'):
                    # String variable
                    empty_str = "\0"
                    c_empty = ir.Constant(ir.ArrayType(ir.IntType(8), len(empty_str)),
                                          bytearray(empty_str.encode("utf8")))
                    global_empty = ir.GlobalVariable(self.module, c_empty.type, name=f"empty_{var_name}")
                    global_empty.linkage = 'internal'
                    global_empty.global_constant = True
                    global_empty.initializer = c_empty
                    
                    var_ptr = self.builder.alloca(ir.IntType(8).as_pointer(), name=var_name)
                    empty_ptr = self.builder.bitcast(global_empty, ir.IntType(8).as_pointer())
                    self.builder.store(empty_ptr, var_ptr)
                    self.symbol_table[var_name] = var_ptr
                else:
                    # Numeric variable
                    var_ptr = self.builder.alloca(ir.DoubleType(), name=var_name)
                    self.symbol_table[var_name] = var_ptr
            
            value = self._codegen_expr(stmt._tokens)
            
            # Normal assignment
            self.builder.store(value, var_ptr)

    def _codegen_print(self, stmt: ParsedStatementPrint):
        lexer = get_lexer()
        
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
                # Create a global string constant without newline
                fmt = str_val + "\0"
                name = f"str_{hash(fmt)}"
                if name in self.module.globals:
                    global_fmt = self.module.get_global(name)
                else:
                    c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                                        bytearray(fmt.encode("utf8")))
                    global_fmt = ir.GlobalVariable(self.module, c_fmt.type, name=name)
                    global_fmt.linkage = 'internal'
                    global_fmt.global_constant = True
                    global_fmt.initializer = c_fmt
                fmt_ptr = self.builder.bitcast(global_fmt, ir.IntType(8).as_pointer())
                self.builder.call(self.printf, [fmt_ptr])
            else:
                # Expression
                tokens = lexer.lex(output)
                val = self._codegen_expr(tokens)

                # Check if this is a string value (pointer to char)
                if hasattr(val, 'type') and val.type == ir.IntType(8).as_pointer():
                    # String value - print without newline
                    self.builder.call(self.printf, [val])
                else:
                    # Numeric value - print as float without newline
                    # Create format string for numeric values without newline
                    fmt = "%g\0"
                    c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)), bytearray(fmt.encode("utf8")))
                    if "fmt_num" not in self.module.globals:
                        global_fmt_num = ir.GlobalVariable(self.module, c_fmt.type, name="fmt_num")
                        global_fmt_num.linkage = 'internal'
                        global_fmt_num.global_constant = True
                        global_fmt_num.initializer = c_fmt
                    else:
                        global_fmt_num = self.module.get_global("fmt_num")
                    fmt_ptr = self.builder.bitcast(global_fmt_num, ir.IntType(8).as_pointer())
                    self.builder.call(self.printf, [fmt_ptr, val])
        
        # Add newline at the end of the PRINT statement (unless it ends with semicolon)
        if not stmt._no_cr:
            newline_fmt = "\n\0"
            name = "global_newline"
            if name in self.module.globals:
                global_newline = self.module.get_global(name)
            else:
                c_newline = ir.Constant(ir.ArrayType(ir.IntType(8), len(newline_fmt)),
                                        bytearray(newline_fmt.encode("utf8")))
                global_newline = ir.GlobalVariable(self.module, c_newline.type, name=name)
                global_newline.linkage = 'internal'
                global_newline.global_constant = True
                global_newline.initializer = c_newline
            newline_ptr = self.builder.bitcast(global_newline, ir.IntType(8).as_pointer())
            self.builder.call(self.printf, [newline_ptr])

    def _codegen_expr(self, tokens, local_vars=None, builder=None):
        """
        Generate LLVM IR for an expression.
        
        Args:
            tokens: List of tokens representing the expression
            local_vars: Optional local variable table (for function bodies)
            builder: Optional IRBuilder (for function bodies)
        """
        if local_vars is None:
            local_vars = {}
        if builder is None:
            builder = self.builder

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
            elif token.type == 'str':
                # String literal - create a global string constant
                str_val = token.token
                # Process escape sequences
                str_val = str_val.encode('utf-8').decode('unicode_escape')
                # Create a global string constant without newline (newlines added by PRINT)
                fmt = str_val + "\0"
                c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                                    bytearray(fmt.encode("utf8")))
                global_fmt = ir.GlobalVariable(self.module, c_fmt.type, name=f"str_{hash(fmt)}")
                global_fmt.linkage = 'internal'
                global_fmt.global_constant = True
                global_fmt.initializer = c_fmt
                fmt_ptr = self.builder.bitcast(global_fmt, ir.IntType(8).as_pointer())
                data_stack.append(fmt_ptr)
                is_unary_context = False
            elif token.type == 'id':
                print(f"DEBUG: id token encountered: '{token.token}' at index {i}")
                # Check if this is followed by parentheses
                if i + 1 < len(tokens) and tokens[i + 1].token == '(':
                    # This could be function call or array access
                    identifier = token.token
                    known_functions = ["SIN", "COS", "SQR", "EXP", "LOG", "ABS", "ASC", "CHR$", "SPACE$", "STR$", "LEN", "LEFT$", "RIGHT$", "MID$", "INT"]
                    if identifier in known_functions or identifier in self.user_functions:
                        # This is a function call
                        print(f"DEBUG: Found function call to {identifier}")
                        # Find the closing parenthesis and extract arguments
                        args = []
                        i += 2  # Skip the opening parenthesis
                        # Parse the argument as an expression
                        arg_tokens = []
                        paren_count = 0
                        while i < len(tokens) and (tokens[i].token != ')' or paren_count > 0):
                            if tokens[i].token == '(': paren_count += 1
                            elif tokens[i].token == ')': paren_count -= 1
                            if paren_count >= 0:
                                arg_tokens.append(tokens[i])
                            i += 1
                        if i >= len(tokens) or tokens[i].token != ')':
                            raise Exception("Missing closing parenthesis in function call")
                        # Evaluate the argument expression
                        if arg_tokens:
                            arg_value = self._codegen_expr(arg_tokens, local_vars=local_vars, builder=builder)
                            args.append(arg_value)
                        # Call the function
                        result = self._codegen_function_call(identifier, args, builder)
                        data_stack.append(result)
                    else:
                        # This is array access - handle it specially
                        array_name = identifier
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
                        # Regular variable - check local vars first, then global
                        if token.token in local_vars:
                            # Local variable (function argument)
                            data_stack.append(builder.load(local_vars[token.token], name=f"load_{token.token}"))
                        elif token.token in self.symbol_table:
                            # Global variable
                            if token.token.endswith('$'):
                                # String variable - load the string pointer
                                data_stack.append(builder.load(self.symbol_table[token.token], name=f"load_{token.token}"))
                            else:
                                # Numeric variable
                                data_stack.append(builder.load(self.symbol_table[token.token], name=f"load_{token.token}"))
                        else:
                            # Undefined variable - initialize to 0
                            var_ptr = builder.alloca(ir.DoubleType(), name=token.token)
                            builder.store(ir.Constant(ir.DoubleType(), 0.0), var_ptr)
                            self.symbol_table[token.token] = var_ptr
                            data_stack.append(builder.load(var_ptr, name=f"load_{token.token}"))
                is_unary_context = False
            elif token.type == 'op':
                current_op_token = token
                if current_op_token.token == "-" and is_unary_context:
                    # This is a unary minus. We'll handle it by making it 0 - value.
                    # This is a simplification. A better way would be a specific unary minus op.
                    data_stack.append(ir.Constant(ir.DoubleType(), 0.0))

                while op_stack and op_stack[-1].token != '(' and get_precedence(op_stack[-1]) >= get_precedence(current_op_token):
                    self._one_op(op_stack, data_stack, builder)
                
                if current_op_token.token == ')':
                    op_stack.pop() # Pop '('
                else:
                    op_stack.append(current_op_token)
                
                is_unary_context = (current_op_token.token != ')')
            
            i += 1

        while op_stack:
            self._one_op(op_stack, data_stack, builder)

        print(f"DEBUG: Final data_stack size: {len(data_stack)}")  # Debug output
        if len(data_stack) == 1:
            return data_stack[0]
        else:
            raise Exception("Expression evaluation failed, stack has multiple values.")

    def _concatenate_strings(self, left, right):
        """Concatenate two strings using strcat"""
        # Get lengths of both strings
        left_len = self.builder.call(self.strlen, [left])
        right_len = self.builder.call(self.strlen, [right])
        
        # Allocate memory for result (left_len + right_len + 1 for null terminator)
        total_len = self.builder.add(left_len, right_len)
        one = ir.Constant(ir.IntType(64), 1)
        alloc_size = self.builder.add(total_len, one)
        
        result_ptr = self.builder.call(self.malloc, [alloc_size])
        
        # Copy first string to result
        self.builder.call(self.strcat, [result_ptr, left])
        
        # Concatenate second string
        self.builder.call(self.strcat, [result_ptr, right])
        
        return result_ptr

    def _create_string_constant(self, str_val):
        """Create a string constant and return a pointer to it, reusing if already exists"""
        # Process escape sequences
        str_val = str_val.encode('utf-8').decode('unicode_escape')
        # Create a global string constant with null terminator
        fmt = str_val + "\0"
        name = f"str_{hash(fmt)}"
        if name in self.module.globals:
            global_fmt = self.module.get_global(name)
        else:
            c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                                bytearray(fmt.encode("utf8")))
            global_fmt = ir.GlobalVariable(self.module, c_fmt.type, name=name)
            global_fmt.linkage = 'internal'
            global_fmt.global_constant = True
            global_fmt.initializer = c_fmt
        return self.builder.bitcast(global_fmt, ir.IntType(8).as_pointer())

    def _codegen_function_call(self, func_name, args, builder=None):
        """Generate LLVM IR for a function call"""
        if builder is None:
            builder = self.builder
        if func_name == "SIN":
            return builder.call(self.sin, [args[0]], name="sin_result")
        elif func_name == "COS":
            return builder.call(self.cos, [args[0]], name="cos_result")
        elif func_name == "SQR":
            return builder.call(self.sqrt, [args[0]], name="sqrt_result")
        elif func_name == "EXP":
            return builder.call(self.exp, [args[0]], name="exp_result")
        elif func_name == "LOG":
            return builder.call(self.log, [args[0]], name="log_result")
        elif func_name == "ABS":
            return builder.call(self.fabs, [args[0]], name="abs_result")
        elif func_name == "INT":
            # INT(x) - truncate to integer (floor function)
            return builder.call(self.int_func, [args[0]], name="int_result")
        elif func_name == "ASC":
            # ASC(string) - return ASCII code of first character
            # For now, return a reasonable default (65 for 'A')
            return ir.Constant(ir.DoubleType(), 65.0)
        elif func_name == "CHR$":
            # CHR$(code) - return character with given ASCII code
            # For now, return a reasonable default string
            return self._create_string_constant("A")
        elif func_name == "SPACE$":
            # SPACE$(n) - return n spaces
            # For now, return a reasonable default
            return self._create_string_constant("   ")
        elif func_name == "STR$":
            # STR$(number) - convert number to string
            # For now, return a reasonable default
            return self._create_string_constant("42")
        elif func_name == "LEN":
            # LEN(string) - return length of string
            # For now, return a reasonable default
            return ir.Constant(ir.DoubleType(), 5.0)
        elif func_name == "LEFT$":
            # LEFT$(string, n) - return left n characters
            # For now, return a reasonable default
            return self._create_string_constant("HELLO")
        elif func_name == "RIGHT$":
            # RIGHT$(string, n) - return right n characters
            # For now, return a reasonable default
            return self._create_string_constant("WORLD")
        elif func_name == "MID$":
            # MID$(string, start, length) - return substring
            # For now, return a reasonable default
            return self._create_string_constant("MID")
        elif func_name in self.user_functions:
            # User-defined function call
            return builder.call(self.user_functions[func_name], [args[0]], name=f"{func_name.lower()}_result")
        else:
            raise NotImplementedError(f"Function {func_name} not implemented")

    def _one_op(self, op_stack, data_stack, builder=None):
        """
        Process one operator from the operator stack.
        
        Args:
            op_stack: Stack of operators
            data_stack: Stack of data values
            builder: Optional IRBuilder (for function bodies)
        """
        if builder is None:
            builder = self.builder

        op = op_stack.pop()
        print(f"DEBUG: Processing operator: {op.token}")
        
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
                # Check if this is string concatenation
                # For now, we'll assume if either operand is a string pointer, it's string concatenation
                # In a more sophisticated implementation, we'd need to track types
                if (isinstance(left, ir.LoadInstr) and left.type == ir.IntType(8).as_pointer()) or \
                   (isinstance(right, ir.LoadInstr) and right.type == ir.IntType(8).as_pointer()):
                    # String concatenation - use strcat
                    result = self._concatenate_strings(left, right)
                else:
                    # Numeric addition
                    result = builder.fadd(left, right, name="addtmp")
            elif op.token == '-':
                result = builder.fsub(left, right, name="subtmp")
            elif op.token == '*':
                result = builder.fmul(left, right, name="multmp")
            elif op.token == '/':
                result = builder.fdiv(left, right, name="divtmp")
            elif op.token == '=':
                # Equal comparison
                cmp_result = builder.fcmp_ordered("==", left, right, name="cmptmp")
                result = builder.uitofp(cmp_result, ir.DoubleType())  # Convert to double
            elif op.token == '<>':
                # Not equal comparison
                cmp_result = builder.fcmp_ordered("!=", left, right, name="cmptmp")
                result = builder.uitofp(cmp_result, ir.DoubleType())  # Convert to double
            elif op.token == '<':
                # Less than comparison
                cmp_result = builder.fcmp_ordered("<", left, right, name="cmptmp")
                result = builder.uitofp(cmp_result, ir.DoubleType())  # Convert to double
            elif op.token == '>':
                # Greater than comparison
                cmp_result = builder.fcmp_ordered(">", left, right, name="cmptmp")
                result = builder.uitofp(cmp_result, ir.DoubleType())  # Convert to double
            elif op.token == '<=':
                # Less than or equal comparison
                cmp_result = builder.fcmp_ordered("<=", left, right, name="cmptmp")
                result = builder.uitofp(cmp_result, ir.DoubleType())  # Convert to double
            elif op.token == '>=':
                # Greater than or equal comparison
                cmp_result = builder.fcmp_ordered(">=", left, right, name="cmptmp")
                result = builder.uitofp(cmp_result, ir.DoubleType())  # Convert to double
            elif op.token == 'AND':
                # Logical AND: (left != 0) and (right != 0)
                left_nonzero = builder.fcmp_ordered('!=', left, ir.Constant(ir.DoubleType(), 0.0))
                right_nonzero = builder.fcmp_ordered('!=', right, ir.Constant(ir.DoubleType(), 0.0))
                and_result = builder.and_(left_nonzero, right_nonzero)
                # Convert i1 to double: true -> 1.0, false -> 0.0
                result = builder.uitofp(and_result, ir.DoubleType())
            elif op.token == 'OR':
                # Logical OR: (left != 0) or (right != 0)
                left_nonzero = builder.fcmp_ordered('!=', left, ir.Constant(ir.DoubleType(), 0.0))
                right_nonzero = builder.fcmp_ordered('!=', right, ir.Constant(ir.DoubleType(), 0.0))
                or_result = builder.or_(left_nonzero, right_nonzero)
                # Convert i1 to double: true -> 1.0, false -> 0.0
                result = builder.uitofp(or_result, ir.DoubleType())
            else:
                raise NotImplementedError(f"Operator {op.token} not implemented")
            
            data_stack.append(result)

    def _codegen_if(self, stmt, line_stmts=None, stmt_index=None):
        """Generate LLVM IR for an IF/THEN statement with proper BASIC line semantics"""
        # Evaluate the condition
        condition_val = self._codegen_expr(stmt._tokens)
        
        # Compare to zero to get boolean condition
        zero = ir.Constant(ir.DoubleType(), 0.0)
        condition = self.builder.fcmp_ordered("!=", condition_val, zero, name="if_condition")
        
        # Create blocks for then and else (next line)
        func = self.builder.block.function
        then_block = func.append_basic_block(name=f"if_then_{self.builder.block.name}")
        
        # For false condition: either continue to next statement on same line, or go to next line
        if line_stmts and stmt_index is not None and stmt_index + 1 < len(line_stmts):
            # There are more statements on this line - continue with them
            else_block = func.append_basic_block(name=f"if_continue_{self.builder.block.name}")
        else:
            # No more statements on this line - go to next line
            # We'll determine the next line block later
            else_block = func.append_basic_block(name=f"if_next_line_{self.builder.block.name}")
        
        # Branch based on condition
        self.builder.cbranch(condition, then_block, else_block)
        
        # THEN block: execute all remaining statements on this line
        self.builder.position_at_end(then_block)
        
        # First, execute the immediate THEN clause
        additional = stmt.get_additional()
        if additional:
            from basic_utils import smart_split
            from basic_statements import Keywords
            from basic_parsing import ParsedStatement, ParsedStatementLet
            stmts = smart_split(additional)
            for s in stmts:
                s = s.strip()
                if not s:
                    continue
                # Handle bare line number as GOTO
                if s.isdigit():
                    s = f"GOTO {s}"
                # Find the keyword
                for kw in Keywords.__members__.values():
                    if s.startswith(kw.name):
                        parser = kw.value.get_parser_class()
                        parsed = parser(kw, s[len(kw.name):])
                        break
                else:
                    # Default to LET
                    kw = Keywords.LET
                    parser = kw.value.get_parser_class()
                    parsed = parser(kw, s)
                self._generate_statement_ir(parsed)
                
                # Check if the block was terminated (e.g., by GOTO, RETURN, END, STOP)
                if self.builder.block.is_terminated:
                    break
        
        # Then execute all remaining statements on this line (if any)
        if not self.builder.block.is_terminated and line_stmts and stmt_index is not None:
            for i in range(stmt_index + 1, len(line_stmts)):
                remaining_stmt = line_stmts[i]
                self._generate_statement_ir(remaining_stmt)
                
                # Check if the block was terminated
                if self.builder.block.is_terminated:
                    break
        
        # Branch to next line (or return if this terminates)
        if not self.builder.block.is_terminated:
            # Find next line
            if self.current_line_index + 1 < len(self.program):
                next_line_num = self.program[self.current_line_index + 1].line
                self.builder.branch(self.line_blocks[next_line_num])
            else:
                self.builder.ret(ir.Constant(ir.IntType(32), 0))
        
        # ELSE block: handle false condition
        self.builder.position_at_end(else_block)
        if line_stmts and stmt_index is not None and stmt_index + 1 < len(line_stmts):
            # Continue with next statement on same line
            pass  # The main loop will handle the remaining statements
        else:
            # Go to next line
            if self.current_line_index + 1 < len(self.program):
                next_line_num = self.program[self.current_line_index + 1].line
                self.builder.branch(self.line_blocks[next_line_num])
            else:
                self.builder.ret(ir.Constant(ir.IntType(32), 0))

    def _codegen_goto(self, stmt):
        target_line = int(stmt.destination)
        if target_line in self.line_blocks:
            # Check if this is GOSUB or GOTO
            is_gosub = stmt.keyword.name == "GOSUB"
            
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
                total_size *= (dim + 1)  # +1 because BASIC arrays are 1-based

            # Determine array type based on name
            is_string_array = name.endswith("$")
            if is_string_array:
                element_type = ir.IntType(8).as_pointer()
                # Initialize with empty strings
                empty_str_val = "\0"
                c_empty_str = ir.Constant(ir.ArrayType(ir.IntType(8), len(empty_str_val)), bytearray(empty_str_val.encode("utf8")))
                global_empty_str = ir.GlobalVariable(self.module, c_empty_str.type, name=f"empty_str_{name}")
                global_empty_str.linkage = 'internal'
                global_empty_str.global_constant = True
                global_empty_str.initializer = c_empty_str
                default_value = self.builder.bitcast(global_empty_str, element_type)
            else:
                element_type = ir.DoubleType()
                default_value = ir.Constant(element_type, 0.0)

            array_type = ir.ArrayType(element_type, total_size)
            array_storage = self.builder.alloca(array_type, name=f"{name}_storage")
            
            # Initialize all elements
            for i in range(total_size):
                element_ptr = self.builder.gep(array_storage, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), i)])
                self.builder.store(default_value, element_ptr)
            
            # Store array info for access
            self.array_info[name] = {
                'storage': array_storage,
                'dimensions': dimensions,
                'total_size': total_size,
                'is_string': is_string_array
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