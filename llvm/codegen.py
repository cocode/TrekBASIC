from llvmlite import ir, binding
from basic_parsing import (
    ParsedStatementLet, ParsedStatementPrint, ParsedStatementIf,
    ParsedStatementFor, ParsedStatementNext, ParsedStatementGo,
    ParsedStatementOnGoto, ParsedStatementInput, ParsedStatementDim,
    ParsedStatementThen, ParsedStatementElse, ParsedStatementData,
    ParsedStatementRead, ParsedStatementRestore
)
from basic_lexer import get_lexer
from basic_operators import get_precedence
from basic_dialect import DIALECT


class LLVMCodeGenerator:
    def __init__(self, program, debug=False, trace=False):
        self.program = program
        self.debug = debug
        self.trace = trace
        self.rnd_seeded = False  # Track if random number generator has been seeded
        self.module = ir.Module(name="basic_program")
        self.module.triple = binding.get_default_triple()

        # External functions
        printf_type = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer()], var_arg=True)
        self.printf = ir.Function(self.module, printf_type, name="printf")

        # Declare sprintf function for string formatting
        sprintf_type = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer(), ir.IntType(8).as_pointer()],
                                       var_arg=True)
        self.sprintf = ir.Function(self.module, sprintf_type, name="sprintf")

        # Declare sscanf function for parsing strings
        sscanf_type = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer(), ir.IntType(8).as_pointer()],
                                      var_arg=True)
        self.sscanf = ir.Function(self.module, sscanf_type, name="sscanf")

        # Declare scanf function for input
        scanf_type = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer()], var_arg=True)
        self.scanf = ir.Function(self.module, scanf_type, name="scanf")

        # Declare fgets function for reading lines (better for string input)
        fgets_type = ir.FunctionType(ir.IntType(8).as_pointer(),
                                     [ir.IntType(8).as_pointer(), ir.IntType(32), ir.IntType(8).as_pointer()])
        self.fgets = ir.Function(self.module, fgets_type, name="fgets")

        # Declare getchar function for reading single characters
        getchar_type = ir.FunctionType(ir.IntType(32), [])
        self.getchar = ir.Function(self.module, getchar_type, name="getchar")

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

        # Declare strcmp for string comparison
        strcmp_type = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer(), ir.IntType(8).as_pointer()])
        self.strcmp = ir.Function(self.module, strcmp_type, name="strcmp")

        # Declare strchr for finding characters in strings
        strchr_type = ir.FunctionType(ir.IntType(8).as_pointer(), [ir.IntType(8).as_pointer(), ir.IntType(32)])
        self.strchr = ir.Function(self.module, strchr_type, name="strchr")

        # Declare strncpy for copying strings with length limit
        strncpy_type = ir.FunctionType(ir.IntType(8).as_pointer(),
                                       [ir.IntType(8).as_pointer(), ir.IntType(8).as_pointer(), ir.IntType(64)])
        self.strncpy = ir.Function(self.module, strncpy_type, name="strncpy")

        # Declare strcpy for copying strings
        strcpy_type = ir.FunctionType(ir.IntType(8).as_pointer(),
                                      [ir.IntType(8).as_pointer(), ir.IntType(8).as_pointer()])
        self.strcpy = ir.Function(self.module, strcpy_type, name="strcpy")

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

        # Declare pow function for exponentiation
        pow_type = ir.FunctionType(ir.DoubleType(), [ir.DoubleType(), ir.DoubleType()])
        self.pow = ir.Function(self.module, pow_type, name="pow")

        # Declare rand function for random numbers
        rand_type = ir.FunctionType(ir.IntType(32), [])
        self.rand = ir.Function(self.module, rand_type, name="rand")

        # Declare srand function for seeding random number generator
        srand_type = ir.FunctionType(ir.VoidType(), [ir.IntType(32)])
        self.srand = ir.Function(self.module, srand_type, name="srand")

        # Declare time function for seeding
        time_type = ir.FunctionType(ir.IntType(64), [ir.IntType(64).as_pointer()])
        self.time = ir.Function(self.module, time_type, name="time")

        # Declare INT function
        int_type = ir.FunctionType(ir.DoubleType(), [ir.DoubleType()])
        self.int_func = ir.Function(self.module, int_type, name="floor")

        # Declare string functions
        asc_type = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer()])
        self.asc = ir.Function(self.module, asc_type, name="asc")

        chr_type = ir.FunctionType(ir.IntType(8), [ir.IntType(32)])
        self.chr = ir.Function(self.module, chr_type, name="chr")

        # Declare toupper function for converting strings to uppercase
        toupper_type = ir.FunctionType(ir.IntType(32), [ir.IntType(32)])
        self.toupper = ir.Function(self.module, toupper_type, name="toupper")

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

        # DATA/READ infrastructure
        self.data_values = []  # Collect all DATA values at compile time
        self.data_line_map = {}  # Map line numbers to starting indices in data_values
        self.data_ptr = None  # Global pointer to track current read position
        self._collect_data_values()

        # User-defined functions: map name to LLVM function
        self.user_functions = {}
        self.user_function_defs = []  # Store DEF statements for later processing

        # First pass: scan for user-defined functions and create declarations only
        for program_line in self.program:
            for stmt in program_line.stmts:
                if self.debug:
                    print(f"DEBUG: Statement type: {type(stmt).__name__}, keyword: {getattr(stmt, 'keyword', None)}")
                if hasattr(stmt, 'keyword') and getattr(stmt.keyword, 'name', None) == 'DEF':
                    fn_name = stmt._variable  # e.g., FNA
                    if self.debug:
                        print(f"DEBUG: Found DEF statement for function {fn_name}")
                    # Create LLVM function declaration: double fn(double)
                    fn_type = ir.FunctionType(ir.DoubleType(), [ir.DoubleType()])
                    llvm_fn = ir.Function(self.module, fn_type, name=fn_name)
                    self.user_functions[fn_name] = llvm_fn
                    self.user_function_defs.append(stmt)

        if self.debug:
            print(f"DEBUG: Created {len(self.user_functions)} user functions: {list(self.user_functions.keys())}")

        # Note: Function bodies will be generated later in generate_ir() after variables are allocated

        # Declare SGN as a function (stub, for completeness; actual logic is in codegen)
        sgn_type = ir.FunctionType(ir.DoubleType(), [ir.DoubleType()])
        self.sgn = ir.Function(self.module, sgn_type, name="sgn")

    def generate_ir(self):
        main_func_type = ir.FunctionType(ir.IntType(32), [])
        main_func = ir.Function(self.module, main_func_type, name="main")

        entry_block = main_func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(entry_block)

        # Initialize runtime return address stack
        self._init_return_stack()

        # Allocate variables
        self._allocate_variables()

        # Initialize string variables at runtime
        self._initialize_string_variables()

        # Seed random number generator once at program start
        self._seed_random_generator()

        # Generate user-defined function bodies (now that variables/arrays are allocated)
        self._generate_user_function_bodies()

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

            # Add optional trace output to show which line is being executed
            if self.trace:
                debug_str = f"Executing line {line.line}\\n"
                debug_str_global_name = f"debug_str_{line.line}"
                if debug_str_global_name not in self.module.globals:
                    debug_str_global = ir.GlobalVariable(self.module, ir.ArrayType(ir.IntType(8), len(debug_str)),
                                                         name=debug_str_global_name)
                    debug_str_global.linkage = 'internal'
                    debug_str_global.global_constant = True
                    debug_str_global.initializer = ir.Constant(ir.ArrayType(ir.IntType(8), len(debug_str)),
                                                               bytearray(debug_str.encode("utf-8")))
                else:
                    debug_str_global = self.module.get_global(debug_str_global_name)
                debug_str_ptr = self.builder.bitcast(debug_str_global, ir.PointerType(ir.IntType(8)))
                self.builder.call(self.printf, [debug_str_ptr])

            # Check if this basic block is empty (no instructions yet) 
            trace_instructions = 2 if self.trace else 0
            block_was_empty = len(self.builder.block.instructions) <= trace_instructions

            self._generate_line_statements(line.stmts)

            # If block is still empty after processing statements, add a no-op
            # But only if the block doesn't already have a terminator instruction
            if (block_was_empty and len(self.builder.block.instructions) <= trace_instructions and
                    not self.builder.block.is_terminated):
                # Add a simple no-op to prevent empty basic blocks
                temp_val = ir.Constant(ir.DoubleType(), 0.0)
                if "noop_var" not in self.module.globals:
                    noop_global = ir.GlobalVariable(self.module, ir.DoubleType(), name="noop_var")
                    noop_global.linkage = 'internal'
                    noop_global.global_constant = False
                    noop_global.initializer = temp_val
                else:
                    noop_global = self.module.get_global("noop_var")
                self.builder.store(temp_val, noop_global)

            # Branch to next line if not a branching statement
            if not self.builder.block.is_terminated:
                if i + 1 < len(self.program):
                    next_line_num = self.program[i + 1].line
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
        self.return_stack_ptr.initializer = ir.Constant(return_stack_type,
                                                        [ir.Constant(ir.IntType(32), 0)] * self.return_stack_size)

        # Create global variable for stack top
        self.return_stack_top = ir.GlobalVariable(self.module, ir.IntType(32), name="return_stack_top")
        self.return_stack_top.linkage = 'internal'
        self.return_stack_top.global_constant = False
        self.return_stack_top.initializer = ir.Constant(ir.IntType(32), 0)

    def _allocate_variables(self):
        var_names = set()
        string_var_names = set()
        array_names = set()

        def extract_vars_from_tokens(tokens):
            """Extract variable names from a list of tokens"""
            if not tokens:
                return
            for token in tokens:
                if hasattr(token, 'type') and token.type == 'id':
                    var_name = token.token
                    if var_name.endswith('$'):
                        string_var_names.add(var_name)
                    else:
                        var_names.add(var_name)

        for line in self.program:
            for stmt in line.stmts:
                if isinstance(stmt, ParsedStatementLet):
                    var_name = stmt._variable
                    # Extract base variable name (without array indices)
                    if '(' in var_name:
                        base_var = var_name[:var_name.find('(')].strip()
                    else:
                        base_var = var_name

                    if base_var.endswith('$'):
                        string_var_names.add(base_var)
                    else:
                        var_names.add(base_var)

                    # Also extract variables from the expression tokens
                    extract_vars_from_tokens(stmt._tokens)
                elif isinstance(stmt, ParsedStatementFor):
                    var_names.add(stmt._index_clause)
                elif isinstance(stmt, ParsedStatementDim):
                    for name, dimensions in stmt._dimensions:
                        array_names.add(name)

                # Extract variables from any statement that has tokens
                if hasattr(stmt, '_tokens') and stmt._tokens:
                    extract_vars_from_tokens(stmt._tokens)

        # Allocate regular variables (numeric) - ALL as global variables (BASIC semantics)
        for var_name in var_names:
            global_var = ir.GlobalVariable(self.module, ir.DoubleType(), name=f"global_{var_name}")
            global_var.linkage = 'internal'
            global_var.global_constant = False
            global_var.initializer = ir.Constant(ir.DoubleType(), 0.0)
            self.symbol_table[var_name] = global_var

        # Allocate string variables (pointers to strings) - ALL as global variables (BASIC semantics)
        for var_name in string_var_names:
            # Initialize with empty string
            empty_str = "\0"
            c_empty = ir.Constant(ir.ArrayType(ir.IntType(8), len(empty_str)),
                                  bytearray(empty_str.encode("utf8")))
            global_empty = ir.GlobalVariable(self.module, c_empty.type, name=f"empty_{var_name}")
            global_empty.linkage = 'internal'
            global_empty.global_constant = True
            global_empty.initializer = c_empty

            # Allocate global pointer to store string address
            global_var = ir.GlobalVariable(self.module, ir.IntType(8).as_pointer(), name=f"global_{var_name}")
            global_var.linkage = 'internal'
            global_var.global_constant = False
            # Initialize with constant null pointer (will be set to empty string at runtime)
            global_var.initializer = ir.Constant(ir.IntType(8).as_pointer(), None)
            self.symbol_table[var_name] = global_var

        # Process all DIM statements to allocate arrays
        for line in self.program:
            for stmt in line.stmts:
                if isinstance(stmt, ParsedStatementDim):
                    self._codegen_dim(stmt)

    def _generate_line_statements(self, stmts):
        """Generate IR for a list of statements on a line, handling GOSUB properly"""
        j = 0
        while j < len(stmts):
            stmt = stmts[j]

            # Check if this is a GOSUB statement in a compound line
            if isinstance(stmt, ParsedStatementGo) and stmt.keyword.name == "GOSUB" and j + 1 < len(stmts):
                # This is a GOSUB with remaining statements on the same line
                # Create a continuation block for statements after GOSUB
                func = self.builder.block.function
                continuation_block = func.append_basic_block(
                    name=f"gosub_cont_{self.program[self.current_line_index].line}_{j}")

                # Store continuation block as return address for this GOSUB
                continuation_line_num = self.program[
                                            self.current_line_index].line * 1000 + j + 1  # Unique ID for continuation
                self.line_blocks[continuation_line_num] = continuation_block
                self._push_return_address(continuation_line_num)

                # Generate the GOSUB
                target_line = int(stmt.destination)
                if self.debug:
                    print(
                        f"DEBUG: GOSUB from line {self.program[self.current_line_index].line} to {target_line}, return to continuation {continuation_line_num}")
                self.builder.branch(self.line_blocks[target_line])

                # Switch to continuation block for remaining statements
                self.builder.position_at_end(continuation_block)

                # Continue with remaining statements
                j += 1
                continue
            elif isinstance(stmt, ParsedStatementIf):
                # Use simple IF handling - it processes all statements internally
                self._generate_statement_ir(stmt, line_stmts=stmts, stmt_index=j)
                # Skip all processed statements
                break
            else:
                # Normal statement
                self._generate_statement_ir(stmt, line_stmts=stmts, stmt_index=j)

                # If this statement terminated the block, stop processing
                if self.builder.block.is_terminated:
                    break

                j += 1

    def _initialize_string_variables(self):
        """Initialize global string variables with empty strings at runtime"""
        for var_name, var_ptr in self.symbol_table.items():
            if var_name.endswith('$') and var_name not in self.array_info:
                # Get the empty string for this variable
                empty_name = f"empty_{var_name}"
                if empty_name in self.module.globals:
                    global_empty = self.module.get_global(empty_name)
                    empty_ptr = self.builder.bitcast(global_empty, ir.IntType(8).as_pointer())
                    self.builder.store(empty_ptr, var_ptr)

    def _seed_random_generator(self):
        """Seed the random number generator once at program start"""
        null_ptr = ir.Constant(ir.IntType(64).as_pointer(), None)
        time_val = self.builder.call(self.time, [null_ptr], name="time_val")
        time_int = self.builder.trunc(time_val, ir.IntType(32), name="time_int")
        self.builder.call(self.srand, [time_int])
        self.rnd_seeded = True

    def _generate_user_function_bodies(self):
        """Generate bodies for user-defined functions after variables are allocated"""
        for stmt in self.user_function_defs:
            fn_name = stmt._variable
            arg_name = stmt._function_arg
            body_tokens = stmt._tokens
            llvm_fn = self.user_functions[fn_name]

            # Create function body
            entry_block = llvm_fn.append_basic_block('entry')
            builder = ir.IRBuilder(entry_block)

            # Set up a local symbol table that includes both argument and global variables
            local_vars = dict(self.symbol_table)  # Copy global symbol table
            arg_ptr = builder.alloca(ir.DoubleType(), name=arg_name)
            builder.store(llvm_fn.args[0], arg_ptr)
            local_vars[arg_name] = arg_ptr  # Override with local argument

            # Evaluate the body expression
            result = self._codegen_expr(body_tokens, local_vars=local_vars, builder=builder)
            builder.ret(result)

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
            self._codegen_if_simple(stmt, line_stmts, stmt_index)
        elif isinstance(stmt, ParsedStatementDim):
            # DIM statements are already processed during variable allocation
            pass
        elif stmt.keyword.name == "END":
            self.builder.ret(ir.Constant(ir.IntType(32), 0))
        elif stmt.keyword.name == "STOP":
            self.builder.ret(ir.Constant(ir.IntType(32), 1))  # Error exit code
        elif stmt.keyword.name == "RETURN":
            self._codegen_return(stmt)
        elif isinstance(stmt, ParsedStatementInput):
            self._codegen_input(stmt)
        elif isinstance(stmt, ParsedStatementOnGoto):
            self._codegen_on_goto(stmt)
        elif isinstance(stmt, ParsedStatementData):
            self._codegen_data(stmt)
        elif isinstance(stmt, ParsedStatementRead):
            self._codegen_read(stmt)
        elif isinstance(stmt, ParsedStatementRestore):
            self._codegen_restore(stmt)
        elif isinstance(stmt, ParsedStatementThen):
            # THEN is a no-op - the IF statement handles the control flow
            pass
        elif isinstance(stmt, ParsedStatementElse):
            # ELSE should jump to next line (ending the THEN block)
            self._codegen_else(stmt)
        # Add other statements here
        else:
            if stmt.keyword.name == "REM":
                # REM should terminate execution of the current line and go to next line
                if self.current_line_index + 1 < len(self.program):
                    next_line_num = self.program[self.current_line_index + 1].line
                    self.builder.branch(self.line_blocks[next_line_num])
                else:
                    self.builder.ret(ir.Constant(ir.IntType(32), 0))
            else:
                print(f"Warning: Codegen for statement '{type(stmt).__name__}' not implemented.", stmt.keyword)
                # Generate a simple no-op to avoid broken control flow
                # Create a global noop variable if it doesn't exist
                if "noop_var" not in self.module.globals:
                    noop_global = ir.GlobalVariable(self.module, ir.DoubleType(), name="noop_var")
                    noop_global.linkage = 'internal'
                    noop_global.global_constant = False
                    noop_global.initializer = ir.Constant(ir.DoubleType(), 0.0)
                else:
                    noop_global = self.module.get_global("noop_var")
                # Add a simple store instruction to prevent empty basic blocks
                temp_val = ir.Constant(ir.DoubleType(), 0.0)
                self.builder.store(temp_val, noop_global)

    def _codegen_for(self, stmt):
        """Generate LLVM IR for a FOR loop"""
        # Get the loop variable
        loop_var = stmt._index_clause
        var_ptr = self.symbol_table.get(loop_var)
        if not var_ptr:
            # Create global variable for loop variable (BASIC semantics)
            global_var = ir.GlobalVariable(self.module, ir.DoubleType(), name=f"global_{loop_var}")
            global_var.linkage = 'internal'
            global_var.global_constant = False
            global_var.initializer = ir.Constant(ir.DoubleType(), 0.0)
            self.symbol_table[loop_var] = global_var
            var_ptr = global_var

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

        # Branch back to condition block (only if current block is not terminated)
        if not self.builder.block.is_terminated:
            self.builder.branch(loop_context['cond_block'])

        # Position builder at after block for any code that follows
        self.builder.position_at_end(loop_context['after_block'])

    def _codegen_input(self, stmt):
        """Generate LLVM IR for an INPUT statement"""
        # Print the prompt if there is one
        if hasattr(stmt, '_prompt') and stmt._prompt:
            # Remove quotes from prompt if present
            prompt = stmt._prompt.strip()
            if prompt.startswith('"') and prompt.endswith('"'):
                prompt = prompt[1:-1]

            # Create format string for prompt with space after it (BASIC convention)
            prompt_fmt = prompt + " \0"
            c_prompt_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(prompt_fmt)),
                                       bytearray(prompt_fmt.encode("utf8")))
            prompt_fmt_name = f"input_prompt_{hash(prompt)}"
            if prompt_fmt_name not in self.module.globals:
                global_prompt_fmt = ir.GlobalVariable(self.module, c_prompt_fmt.type, name=prompt_fmt_name)
                global_prompt_fmt.linkage = 'internal'
                global_prompt_fmt.global_constant = True
                global_prompt_fmt.initializer = c_prompt_fmt
            else:
                global_prompt_fmt = self.module.get_global(prompt_fmt_name)

            prompt_fmt_ptr = self.builder.bitcast(global_prompt_fmt, ir.IntType(8).as_pointer())
            self.builder.call(self.printf, [prompt_fmt_ptr])

        for var_name in stmt._input_vars:
            if var_name.endswith('$'):
                # String variable - read string input
                if var_name not in self.symbol_table:
                    # Create the variable if it doesn't exist
                    global_var = ir.GlobalVariable(self.module, ir.IntType(8).as_pointer(), name=f"global_{var_name}")
                    global_var.linkage = 'internal'
                    global_var.global_constant = False
                    global_var.initializer = ir.Constant(ir.IntType(8).as_pointer(), None)
                    self.symbol_table[var_name] = global_var

                # Allocate buffer for string input (256 characters max)
                buffer_size = ir.Constant(ir.IntType(64), 256)
                input_buffer = self.builder.call(self.malloc, [buffer_size], name=f"input_buffer_{var_name}")

                # Initialize buffer to empty string
                null_char = ir.Constant(ir.IntType(8), 0)
                self.builder.store(null_char, input_buffer)

                # Use scanf with format that handles empty input
                # %[^\n] reads everything up to newline, allows empty input
                line_fmt = "%[^\n]\0"
                c_line_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(line_fmt)),
                                         bytearray(line_fmt.encode("utf8")))
                line_fmt_name = f"line_input_fmt_{var_name}"
                if line_fmt_name not in self.module.globals:
                    global_line_fmt = ir.GlobalVariable(self.module, c_line_fmt.type, name=line_fmt_name)
                    global_line_fmt.linkage = 'internal'
                    global_line_fmt.global_constant = True
                    global_line_fmt.initializer = c_line_fmt
                else:
                    global_line_fmt = self.module.get_global(line_fmt_name)

                line_fmt_ptr = self.builder.bitcast(global_line_fmt, ir.IntType(8).as_pointer())

                # Call scanf to read the line (may be empty)
                scanf_result = self.builder.call(self.scanf, [line_fmt_ptr, input_buffer])

                # Consume the newline character left by scanf
                self.builder.call(self.getchar, [])

                # Convert string to uppercase if UPPERCASE_INPUT is enabled
                if DIALECT.UPPERCASE_INPUT:
                    # Create a loop to iterate through the string and convert each character
                    func = self.builder.block.function
                    loop_block = func.append_basic_block(name=f"uppercase_loop_{var_name}")
                    after_loop_block = func.append_basic_block(name=f"after_uppercase_{var_name}")

                    # Initialize loop counter
                    counter_var = self.builder.alloca(ir.IntType(32), name=f"counter_{var_name}")
                    self.builder.store(ir.Constant(ir.IntType(32), 0), counter_var)
                    self.builder.branch(loop_block)

                    # Loop to convert each character
                    self.builder.position_at_end(loop_block)
                    counter = self.builder.load(counter_var, name="counter")

                    # Get current character
                    char_ptr = self.builder.gep(input_buffer, [counter], name="char_ptr")
                    current_char = self.builder.load(char_ptr, name="current_char")

                    # Check if we've reached null terminator
                    null_char = ir.Constant(ir.IntType(8), 0)
                    is_null = self.builder.icmp_signed("==", current_char, null_char)

                    # Create block for character conversion
                    convert_block = func.append_basic_block(name=f"convert_char_{var_name}")
                    self.builder.cbranch(is_null, after_loop_block, convert_block)

                    # Convert character to uppercase
                    self.builder.position_at_end(convert_block)
                    char_as_int = self.builder.zext(current_char, ir.IntType(32))
                    upper_char_int = self.builder.call(self.toupper, [char_as_int])
                    upper_char = self.builder.trunc(upper_char_int, ir.IntType(8))

                    # Store the uppercase character back
                    self.builder.store(upper_char, char_ptr)

                    # Increment counter and continue loop
                    next_counter = self.builder.add(counter, ir.Constant(ir.IntType(32), 1))
                    self.builder.store(next_counter, counter_var)
                    self.builder.branch(loop_block)

                    # After loop - position builder at the after block
                    self.builder.position_at_end(after_loop_block)

                # Store the buffer pointer in the variable
                self.builder.store(input_buffer, self.symbol_table[var_name])
            else:
                # Numeric variable - read entire line then parse number
                if var_name not in self.symbol_table:
                    # Create the variable if it doesn't exist
                    global_var = ir.GlobalVariable(self.module, ir.DoubleType(), name=f"global_{var_name}")
                    global_var.linkage = 'internal'
                    global_var.global_constant = False
                    global_var.initializer = ir.Constant(ir.DoubleType(), 0.0)
                    self.symbol_table[var_name] = global_var

                # Allocate buffer for line input (same approach as string input)
                buffer_size = ir.Constant(ir.IntType(64), 256)
                input_buffer = self.builder.call(self.malloc, [buffer_size], name=f"numeric_input_buffer_{var_name}")

                # Initialize buffer to empty string
                null_char = ir.Constant(ir.IntType(8), 0)
                self.builder.store(null_char, input_buffer)

                # Read entire line (same as string input)
                line_fmt = "%[^\n]\0"
                c_line_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(line_fmt)),
                                         bytearray(line_fmt.encode("utf8")))
                line_fmt_name = f"numeric_line_input_fmt_{var_name}"
                if line_fmt_name not in self.module.globals:
                    global_line_fmt = ir.GlobalVariable(self.module, c_line_fmt.type, name=line_fmt_name)
                    global_line_fmt.linkage = 'internal'
                    global_line_fmt.global_constant = True
                    global_line_fmt.initializer = c_line_fmt
                else:
                    global_line_fmt = self.module.get_global(line_fmt_name)

                line_fmt_ptr = self.builder.bitcast(global_line_fmt, ir.IntType(8).as_pointer())

                # Call scanf to read the line (may be empty)
                scanf_result = self.builder.call(self.scanf, [line_fmt_ptr, input_buffer])

                # Consume the newline character left by scanf
                self.builder.call(self.getchar, [])

                # Now parse the number from the string using sscanf
                double_fmt = "%lf\0"
                c_double_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(double_fmt)),
                                           bytearray(double_fmt.encode("utf8")))
                double_fmt_name = f"double_parse_fmt_{var_name}"
                if double_fmt_name not in self.module.globals:
                    global_double_fmt = ir.GlobalVariable(self.module, c_double_fmt.type, name=double_fmt_name)
                    global_double_fmt.linkage = 'internal'
                    global_double_fmt.global_constant = True
                    global_double_fmt.initializer = c_double_fmt
                else:
                    global_double_fmt = self.module.get_global(double_fmt_name)

                double_fmt_ptr = self.builder.bitcast(global_double_fmt, ir.IntType(8).as_pointer())

                # Use sscanf to parse the number from the string
                var_ptr = self.symbol_table[var_name]
                self.builder.call(self.sscanf, [input_buffer, double_fmt_ptr, var_ptr])

    def _codegen_on_goto(self, stmt):
        """Generate LLVM IR for an ON...GOTO or ON...GOSUB statement"""
        if not stmt._target_lines or len(stmt._target_lines) == 0:
            return

        # Evaluate the expression to get the index
        lexer = get_lexer()
        expr_tokens = lexer.lex(stmt._expression)
        index_value = self._codegen_expr(expr_tokens)

        # Convert to integer index (1-based in BASIC)
        index_int = self.builder.fptosi(index_value, ir.IntType(32), name="on_index")

        # Create blocks for each target and a default block
        func = self.builder.block.function
        target_blocks = []
        for i, target_line in enumerate(stmt._target_lines):
            block_name = f"on_{stmt._op.lower()}_{i + 1}_{target_line}"
            target_blocks.append(func.append_basic_block(name=block_name))

        # Create default block (for index <= 0 or index > number of targets)
        default_block = func.append_basic_block(name=f"on_{stmt._op.lower()}_default")

        # Create switch statement
        switch_inst = self.builder.switch(index_int, default_block)

        # Add cases for each target (1-based indexing)
        for i, target_line in enumerate(stmt._target_lines):
            case_value = ir.Constant(ir.IntType(32), i + 1)
            switch_inst.add_case(case_value, target_blocks[i])

        # Generate code for each target block
        for i, target_line in enumerate(stmt._target_lines):
            self.builder.position_at_end(target_blocks[i])
            target_line_num = int(target_line)

            if stmt._op == "GOTO":
                # Simple GOTO
                if target_line_num in self.line_blocks:
                    self.builder.branch(self.line_blocks[target_line_num])
                else:
                    # Target not found, go to default
                    self.builder.branch(default_block)
            elif stmt._op == "GOSUB":
                # GOSUB - need to push return address and branch
                # Find the next line to return to
                if self.current_line_index + 1 < len(self.program):
                    next_line = self.program[self.current_line_index + 1].line
                    self._push_return_address(next_line)

                if target_line_num in self.line_blocks:
                    self.builder.branch(self.line_blocks[target_line_num])
                else:
                    # Target not found, go to default
                    self.builder.branch(default_block)

        # Default block - generate runtime error for out-of-range index
        self.builder.position_at_end(default_block)
        # Create error message for out-of-range ON...GOTO/GOSUB
        error_msg = f"ON {stmt._op} index out of range (1-{len(stmt._target_lines)})\n\0"
        error_fmt = self._create_string_constant(error_msg)
        self.builder.call(self.printf, [error_fmt])
        # Exit with error code
        self.builder.ret(ir.Constant(ir.IntType(32), 1))

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
        if self.debug:
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
        var_name = stmt._variable.strip()

        # Check if this is an array assignment by parsing the variable name
        if '(' in var_name:
            # Parse array name and indices from the variable name
            array_name = var_name[:var_name.find('(')].strip()  # Strip whitespace from array name
            indices_str = var_name[var_name.find('(') + 1:var_name.rfind(')')]
            indices = [self._codegen_expr(get_lexer().lex(idx.strip())) for idx in indices_str.split(',')]

            # Get array element pointer
            element_ptr = self._codegen_array_access(array_name, indices)

            # Store the value
            value = self._codegen_expr(stmt._tokens)

            # Array assignment
            self.builder.store(value, element_ptr)
        elif var_name in self.array_info:
            # Array name used as scalar - create a separate scalar variable
            # This is allowed in BASIC - array name can be used as a regular variable too
            var_ptr = self.symbol_table.get(f"{var_name}_scalar")
            if not var_ptr:
                # Create a separate scalar variable for the array name
                if var_name.endswith('$'):
                    # String variable
                    empty_str = "\0"
                    c_empty = ir.Constant(ir.ArrayType(ir.IntType(8), len(empty_str)),
                                          bytearray(empty_str.encode("utf8")))
                    global_empty = ir.GlobalVariable(self.module, c_empty.type, name=f"empty_{var_name}_scalar")
                    global_empty.linkage = 'internal'
                    global_empty.global_constant = True
                    global_empty.initializer = c_empty

                    var_ptr = self.builder.alloca(ir.IntType(8).as_pointer(), name=f"{var_name}_scalar")
                    empty_ptr = self.builder.bitcast(global_empty, ir.IntType(8).as_pointer())
                    self.builder.store(empty_ptr, var_ptr)
                    self.symbol_table[f"{var_name}_scalar"] = var_ptr
                else:
                    # Numeric variable
                    var_ptr = self.builder.alloca(ir.DoubleType(), name=f"{var_name}_scalar")
                    self.symbol_table[f"{var_name}_scalar"] = var_ptr

            value = self._codegen_expr(stmt._tokens)
            self.builder.store(value, var_ptr)
        else:
            # Regular variable assignment
            var_ptr = self.symbol_table.get(var_name)
            if not var_ptr:
                # Variable not pre-allocated, allocate it now as global (BASIC semantics)
                if var_name.endswith('$'):
                    # String variable
                    empty_str = "\0"
                    c_empty = ir.Constant(ir.ArrayType(ir.IntType(8), len(empty_str)),
                                          bytearray(empty_str.encode("utf8")))
                    global_empty = ir.GlobalVariable(self.module, c_empty.type, name=f"empty_{var_name}")
                    global_empty.linkage = 'internal'
                    global_empty.global_constant = True
                    global_empty.initializer = c_empty

                    global_var = ir.GlobalVariable(self.module, ir.IntType(8).as_pointer(), name=f"global_{var_name}")
                    global_var.linkage = 'internal'
                    global_var.global_constant = False
                    # Initialize with null pointer and set at runtime
                    global_var.initializer = ir.Constant(ir.IntType(8).as_pointer(), None)
                    empty_ptr = self.builder.bitcast(global_empty, ir.IntType(8).as_pointer())
                    self.builder.store(empty_ptr, global_var)
                    self.symbol_table[var_name] = global_var
                    var_ptr = global_var
                else:
                    # Numeric variable
                    global_var = ir.GlobalVariable(self.module, ir.DoubleType(), name=f"global_{var_name}")
                    global_var.linkage = 'internal'
                    global_var.global_constant = False
                    global_var.initializer = ir.Constant(ir.DoubleType(), 0.0)
                    self.symbol_table[var_name] = global_var
                    var_ptr = global_var

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
            if isinstance(output, list):
                # Handle concatenated parts (list of strings/expressions)
                for part in output:
                    if part.startswith('"') and part.endswith('"'):
                        # String literal
                        str_val = part[1:-1]
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
                        tokens = lexer.lex(part)
                        val = self._codegen_expr(tokens)

                        # Check if this is a string value (pointer to char)
                        if hasattr(val, 'type') and val.type == ir.IntType(8).as_pointer():
                            # String value - print without newline
                            self.builder.call(self.printf, [val])
                        else:
                            # Numeric value - print as float with spaces around it (BASIC convention)
                            # Create format string for numeric values with spaces
                            fmt = " %g \0"
                            c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)), bytearray(fmt.encode("utf8")))
                            if "fmt_num_spaced" not in self.module.globals:
                                global_fmt_num = ir.GlobalVariable(self.module, c_fmt.type, name="fmt_num_spaced")
                                global_fmt_num.linkage = 'internal'
                                global_fmt_num.global_constant = True
                                global_fmt_num.initializer = c_fmt
                            else:
                                global_fmt_num = self.module.get_global("fmt_num_spaced")
                            fmt_ptr = self.builder.bitcast(global_fmt_num, ir.IntType(8).as_pointer())
                            self.builder.call(self.printf, [fmt_ptr, val])
            elif output.startswith('"') and output.endswith('"'):
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
                    # Numeric value - print as float with spaces around it (BASIC convention)
                    # Create format string for numeric values with spaces
                    fmt = " %g \0"
                    c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)), bytearray(fmt.encode("utf8")))
                    if "fmt_num_spaced" not in self.module.globals:
                        global_fmt_num = ir.GlobalVariable(self.module, c_fmt.type, name="fmt_num_spaced")
                        global_fmt_num.linkage = 'internal'
                        global_fmt_num.global_constant = True
                        global_fmt_num.initializer = c_fmt
                    else:
                        global_fmt_num = self.module.get_global("fmt_num_spaced")
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

        if self.debug:
            print(f"DEBUG: Processing tokens: {tokens}")  # Debug output

        while i < len(tokens):
            token = tokens[i]
            if self.debug:
                print(f"DEBUG: Token: {token.type} = '{token.token}'")  # Debug output

            if token.type == 'num':
                data_stack.append(ir.Constant(ir.DoubleType(), float(token.token)))
                is_unary_context = False
            elif token.type == 'str':
                # String literal - create a global string constant
                str_val = token.token
                fmt_ptr = self._create_string_constant(str_val)
                data_stack.append(fmt_ptr)
                is_unary_context = False
            elif token.type == 'id':
                if self.debug:
                    print(f"DEBUG: id token encountered: '{token.token}' at index {i}")
                # Check if this is followed by parentheses
                if i + 1 < len(tokens) and tokens[i + 1].token == '(':
                    # This could be a function call or array access
                    identifier = token.token
                    known_functions = ["SIN", "COS", "SQR", "EXP", "LOG", "ABS", "ASC", "CHR$", "SPACE$", "STR$", "LEN",
                                       "LEFT$", "RIGHT$", "MID$", "INT", "RND", "TAB", "SGN"]
                    if identifier in known_functions or identifier in self.user_functions:
                        # This is a function call
                        if self.debug:
                            print(f"DEBUG: Found function call to {identifier}")
                        # Find the closing parenthesis and extract arguments
                        args = []
                        i += 2  # Skip the opening parenthesis
                        # Parse arguments separated by commas
                        arg_tokens = []
                        paren_count = 0
                        while i < len(tokens) and (tokens[i].token != ')' or paren_count > 0):
                            if tokens[i].token == '(':
                                paren_count += 1
                                arg_tokens.append(tokens[i])
                            elif tokens[i].token == ')':
                                paren_count -= 1
                                if paren_count >= 0:
                                    arg_tokens.append(tokens[i])
                            elif tokens[i].token == ',' and paren_count == 0:
                                # This comma separates arguments
                                if arg_tokens:
                                    arg_value = self._codegen_expr(arg_tokens, local_vars=local_vars, builder=builder)
                                    args.append(arg_value)
                                    arg_tokens = []
                            else:
                                arg_tokens.append(tokens[i])
                            i += 1
                        if i >= len(tokens) or tokens[i].token != ')':
                            raise Exception("Missing closing parenthesis in function call")
                        # Process the last argument
                        if arg_tokens:
                            arg_value = self._codegen_expr(arg_tokens, local_vars=local_vars, builder=builder)
                            args.append(arg_value)
                        # Call the function
                        result = self._codegen_function_call(identifier, args, builder)
                        data_stack.append(result)
                    else:
                        # This is array access - handle it specially
                        array_name = identifier.strip()
                        if array_name not in self.array_info:
                            raise Exception(f"Array {array_name} not declared")
                        # Find the closing parenthesis and extract indices
                        indices = []
                        i += 2  # Skip the opening parenthesis
                        # Parse indices separated by commas
                        index_tokens = []
                        paren_count = 0
                        while i < len(tokens) and (tokens[i].token != ')' or paren_count > 0):
                            if tokens[i].token == '(':
                                paren_count += 1
                                index_tokens.append(tokens[i])
                            elif tokens[i].token == ')':
                                paren_count -= 1
                                if paren_count >= 0:
                                    index_tokens.append(tokens[i])
                            elif tokens[i].token == ',' and paren_count == 0:
                                # This comma separates array indices
                                if index_tokens:
                                    index_value = self._codegen_expr(index_tokens, local_vars=local_vars,
                                                                     builder=builder)
                                    indices.append(index_value)
                                    index_tokens = []
                            else:
                                index_tokens.append(tokens[i])
                            i += 1
                        if i >= len(tokens) or tokens[i].token != ')':
                            raise Exception("Missing closing parenthesis in array access")
                        # Process the last index
                        if index_tokens:
                            index_value = self._codegen_expr(index_tokens, local_vars=local_vars, builder=builder)
                            indices.append(index_value)
                        # Get array element
                        element_ptr = self._codegen_array_access(array_name, indices, builder)
                        data_stack.append(builder.load(element_ptr, name=f"load_{array_name}_element"))
                else:
                    # Regular variable
                    if token.token in self.array_info:
                        # Array name used as scalar - check for scalar version
                        scalar_name = f"{token.token}_scalar"
                        if scalar_name in self.symbol_table:
                            # Load the scalar version
                            if token.token.endswith('$'):
                                data_stack.append(
                                    builder.load(self.symbol_table[scalar_name], name=f"load_{scalar_name}"))
                            else:
                                data_stack.append(
                                    builder.load(self.symbol_table[scalar_name], name=f"load_{scalar_name}"))
                        else:
                            # Initialize scalar version to 0 if not found
                            if token.token.endswith('$'):
                                # String variable
                                empty_str = "\0"
                                c_empty = ir.Constant(ir.ArrayType(ir.IntType(8), len(empty_str)),
                                                      bytearray(empty_str.encode("utf8")))
                                global_empty = ir.GlobalVariable(self.module, c_empty.type, name=f"empty_{scalar_name}")
                                global_empty.linkage = 'internal'
                                global_empty.global_constant = True
                                global_empty.initializer = c_empty

                                var_ptr = builder.alloca(ir.IntType(8).as_pointer(), name=scalar_name)
                                empty_ptr = builder.bitcast(global_empty, ir.IntType(8).as_pointer())
                                builder.store(empty_ptr, var_ptr)
                                self.symbol_table[scalar_name] = var_ptr
                                data_stack.append(builder.load(var_ptr, name=f"load_{scalar_name}"))
                            else:
                                # Numeric variable
                                var_ptr = builder.alloca(ir.DoubleType(), name=scalar_name)
                                builder.store(ir.Constant(ir.DoubleType(), 0.0), var_ptr)
                                self.symbol_table[scalar_name] = var_ptr
                                data_stack.append(builder.load(var_ptr, name=f"load_{scalar_name}"))
                    else:
                        # Regular variable - check local vars first, then global
                        if token.token in local_vars:
                            # Local variable (function argument)
                            data_stack.append(builder.load(local_vars[token.token], name=f"load_{token.token}"))
                        elif token.token in self.symbol_table:
                            # Global variable
                            if token.token.endswith('$'):
                                # String variable - load the string pointer
                                data_stack.append(
                                    builder.load(self.symbol_table[token.token], name=f"load_{token.token}"))
                            else:
                                # Numeric variable
                                data_stack.append(
                                    builder.load(self.symbol_table[token.token], name=f"load_{token.token}"))
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

                while op_stack and op_stack[-1].token != '(' and get_precedence(op_stack[-1]) >= get_precedence(
                        current_op_token):
                    self._one_op(op_stack, data_stack, builder)

                if current_op_token.token == ')':
                    op_stack.pop()  # Pop '('
                else:
                    op_stack.append(current_op_token)

                is_unary_context = (current_op_token.token != ')')

            i += 1

        while op_stack:
            self._one_op(op_stack, data_stack, builder)
        if self.debug:
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
        elif func_name == "RND":
            # RND(x) - return random number between 0 and 1
            # Random generator is seeded once at program start
            rand_int = builder.call(self.rand, [], name="rand_int")
            rand_float = builder.uitofp(rand_int, ir.DoubleType(), name="rand_float")
            max_rand = ir.Constant(ir.DoubleType(), 2147483647.0)  # RAND_MAX
            result = builder.fdiv(rand_float, max_rand, name="rnd_result")
            return result
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
            if len(args) != 1:
                raise Exception("STR$ requires exactly 1 argument")
            number = args[0]

            # Allocate buffer for the string result (enough for a double)
            buffer_size = ir.Constant(ir.IntType(64), 32)  # Should be enough for any double
            result_ptr = builder.call(self.malloc, [buffer_size], name="str_result")

            # Create format string for sprintf ("%g" for general format)
            str_fmt = "%g\0"
            c_str_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(str_fmt)),
                                    bytearray(str_fmt.encode("utf8")))
            str_fmt_name = f"str_fmt_global"
            if str_fmt_name not in self.module.globals:
                global_str_fmt = ir.GlobalVariable(self.module, c_str_fmt.type, name=str_fmt_name)
                global_str_fmt.linkage = 'internal'
                global_str_fmt.global_constant = True
                global_str_fmt.initializer = c_str_fmt
            else:
                global_str_fmt = self.module.get_global(str_fmt_name)

            str_fmt_ptr = builder.bitcast(global_str_fmt, ir.IntType(8).as_pointer())

            # Call sprintf to convert number to string
            builder.call(self.sprintf, [result_ptr, str_fmt_ptr, number])

            return result_ptr
        elif func_name == "LEN":
            # LEN(string) - return length of string
            if len(args) != 1:
                raise Exception("LEN requires exactly 1 argument")
            string_ptr = args[0]
            str_len = builder.call(self.strlen, [string_ptr], name="str_length")
            # Convert to double for BASIC compatibility
            return builder.uitofp(str_len, ir.DoubleType(), name="len_result")
        elif func_name == "LEFT$":
            # LEFT$(string, n) - return left n characters
            if len(args) != 2:
                raise Exception("LEFT$ requires exactly 2 arguments")
            string_ptr = args[0]
            length = args[1]

            # Convert length from double to integer
            length_int = builder.fptosi(length, ir.IntType(64), name="left_length")

            # Get string length
            str_len = builder.call(self.strlen, [string_ptr], name="str_length")

            # Clamp length to string length (use min of requested length and actual length)
            actual_length = builder.select(
                builder.icmp_unsigned("<", length_int, str_len),
                length_int,
                str_len,
                name="actual_left_length"
            )

            # Allocate memory for result (length + 1 for null terminator)
            one = ir.Constant(ir.IntType(64), 1)
            alloc_size = builder.add(actual_length, one, name="left_alloc_size")
            result_ptr = builder.call(self.malloc, [alloc_size], name="left_result")

            # Copy the left portion of the string
            builder.call(self.strncpy, [result_ptr, string_ptr, actual_length])

            # Add null terminator
            null_pos = builder.gep(result_ptr, [actual_length], name="null_pos")
            null_char = ir.Constant(ir.IntType(8), 0)
            builder.store(null_char, null_pos)

            return result_ptr

        elif func_name == "RIGHT$":
            # RIGHT$(string, n) - return right n characters  
            if len(args) != 2:
                raise Exception("RIGHT$ requires exactly 2 arguments")
            string_ptr = args[0]
            length = args[1]

            # Convert length from double to integer
            length_int = builder.fptosi(length, ir.IntType(64), name="right_length")

            # Get string length
            str_len = builder.call(self.strlen, [string_ptr], name="str_length")

            # Clamp length to string length
            actual_length = builder.select(
                builder.icmp_unsigned("<", length_int, str_len),
                length_int,
                str_len,
                name="actual_right_length"
            )

            # Calculate start position (str_len - actual_length)
            start_pos = builder.sub(str_len, actual_length, name="right_start_pos")
            start_ptr = builder.gep(string_ptr, [start_pos], name="right_start_ptr")

            # Allocate memory for result
            one = ir.Constant(ir.IntType(64), 1)
            alloc_size = builder.add(actual_length, one, name="right_alloc_size")
            result_ptr = builder.call(self.malloc, [alloc_size], name="right_result")

            # Copy the right portion of the string
            builder.call(self.strncpy, [result_ptr, start_ptr, actual_length])

            # Add null terminator
            null_pos = builder.gep(result_ptr, [actual_length], name="null_pos")
            null_char = ir.Constant(ir.IntType(8), 0)
            builder.store(null_char, null_pos)

            return result_ptr

        elif func_name == "MID$":
            # MID$(string, start, length) - return substring starting at position start with given length
            if len(args) != 3:
                raise Exception("MID$ requires exactly 3 arguments")
            string_ptr = args[0]
            start = args[1]
            length = args[2]

            # Convert arguments from double to integer (BASIC uses 1-based indexing)
            start_int = builder.fptosi(start, ir.IntType(64), name="mid_start")
            length_int = builder.fptosi(length, ir.IntType(64), name="mid_length")

            # Convert to 0-based indexing
            one = ir.Constant(ir.IntType(64), 1)
            zero = ir.Constant(ir.IntType(64), 0)
            start_zero_based = builder.sub(start_int, one, name="mid_start_zero")

            # Clamp start to be >= 0
            actual_start = builder.select(
                builder.icmp_signed("<", start_zero_based, zero),
                zero,
                start_zero_based,
                name="actual_mid_start"
            )

            # Get string length
            str_len = builder.call(self.strlen, [string_ptr], name="str_length")

            # Check if start is beyond string length
            start_ptr = builder.gep(string_ptr, [actual_start], name="mid_start_ptr")

            # Calculate remaining length from start position
            remaining_len = builder.sub(str_len, actual_start, name="remaining_length")

            # Clamp length to remaining length
            actual_length = builder.select(
                builder.icmp_unsigned("<", length_int, remaining_len),
                length_int,
                remaining_len,
                name="actual_mid_length"
            )

            # Handle case where start is beyond string (return empty string)
            actual_length = builder.select(
                builder.icmp_unsigned(">=", actual_start, str_len),
                zero,
                actual_length,
                name="final_mid_length"
            )

            # Allocate memory for result
            alloc_size = builder.add(actual_length, one, name="mid_alloc_size")
            result_ptr = builder.call(self.malloc, [alloc_size], name="mid_result")

            # Copy the substring
            builder.call(self.strncpy, [result_ptr, start_ptr, actual_length])

            # Add null terminator
            null_pos = builder.gep(result_ptr, [actual_length], name="null_pos")
            null_char = ir.Constant(ir.IntType(8), 0)
            builder.store(null_char, null_pos)

            return result_ptr
        elif func_name == "TAB":
            # TAB(n) - return string with n spaces for print formatting
            # For now, return a reasonable default (some spaces)
            return self._create_string_constant("        ")
        elif func_name in self.user_functions:
            # User-defined function call
            return builder.call(self.user_functions[func_name], [args[0]], name=f"{func_name.lower()}_result")
        elif func_name == "SGN":
            # SGN(x): 1 if x > 0, 0 if x == 0, -1 if x < 0
            x = args[0]
            zero = ir.Constant(ir.DoubleType(), 0.0)
            one = ir.Constant(ir.DoubleType(), 1.0)
            minus_one = ir.Constant(ir.DoubleType(), -1.0)
            is_gt = builder.fcmp_ordered('>', x, zero, name="sgn_gt")
            is_lt = builder.fcmp_ordered('<', x, zero, name="sgn_lt")
            gt_val = builder.select(is_gt, one, zero, name="sgn_gt_val")
            sgn_val = builder.select(is_lt, minus_one, gt_val, name="sgn_result")
            return sgn_val
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
        if self.debug:
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
                # Check if either operand is a string pointer type
                left_is_string = (hasattr(left, 'type') and left.type == ir.IntType(8).as_pointer())
                right_is_string = (hasattr(right, 'type') and right.type == ir.IntType(8).as_pointer())

                if left_is_string or right_is_string:
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
                # Equal comparison - check if comparing strings or numbers
                if left.type == ir.IntType(8).as_pointer() and right.type == ir.IntType(8).as_pointer():
                    # String comparison using strcmp
                    cmp_result = builder.call(self.strcmp, [left, right], name="strcmp_result")
                    # strcmp returns 0 for equal strings
                    zero = ir.Constant(ir.IntType(32), 0)
                    is_equal = builder.icmp_signed("==", cmp_result, zero, name="cmptmp")
                    result = builder.uitofp(is_equal, ir.DoubleType())
                else:
                    # Numeric comparison
                    cmp_result = builder.fcmp_ordered("==", left, right, name="cmptmp")
                    result = builder.uitofp(cmp_result, ir.DoubleType())  # Convert to double
            elif op.token == '<>' or op.token == '#':
                # Not equal comparison (both <> and # operators)
                if left.type == ir.IntType(8).as_pointer() and right.type == ir.IntType(8).as_pointer():
                    # String comparison using strcmp
                    cmp_result = builder.call(self.strcmp, [left, right], name="strcmp_result")
                    # strcmp returns 0 for equal strings, so != 0 means not equal
                    zero = ir.Constant(ir.IntType(32), 0)
                    is_not_equal = builder.icmp_signed("!=", cmp_result, zero, name="cmptmp")
                    result = builder.uitofp(is_not_equal, ir.DoubleType())
                else:
                    # Numeric comparison
                    cmp_result = builder.fcmp_ordered("!=", left, right, name="cmptmp")
                    result = builder.uitofp(cmp_result, ir.DoubleType())  # Convert to double
            elif op.token == '<':
                # Less than comparison
                if left.type == ir.IntType(8).as_pointer() and right.type == ir.IntType(8).as_pointer():
                    # String comparison using strcmp
                    cmp_result = builder.call(self.strcmp, [left, right], name="strcmp_result")
                    # strcmp returns < 0 if left < right
                    zero = ir.Constant(ir.IntType(32), 0)
                    is_less = builder.icmp_signed("<", cmp_result, zero, name="cmptmp")
                    result = builder.uitofp(is_less, ir.DoubleType())
                else:
                    # Numeric comparison
                    cmp_result = builder.fcmp_ordered("<", left, right, name="cmptmp")
                    result = builder.uitofp(cmp_result, ir.DoubleType())  # Convert to double
            elif op.token == '>':
                # Greater than comparison
                if left.type == ir.IntType(8).as_pointer() and right.type == ir.IntType(8).as_pointer():
                    # String comparison using strcmp
                    cmp_result = builder.call(self.strcmp, [left, right], name="strcmp_result")
                    # strcmp returns > 0 if left > right
                    zero = ir.Constant(ir.IntType(32), 0)
                    is_greater = builder.icmp_signed(">", cmp_result, zero, name="cmptmp")
                    result = builder.uitofp(is_greater, ir.DoubleType())
                else:
                    # Numeric comparison
                    cmp_result = builder.fcmp_ordered(">", left, right, name="cmptmp")
                    result = builder.uitofp(cmp_result, ir.DoubleType())  # Convert to double
            elif op.token == '<=':
                # Less than or equal comparison
                if left.type == ir.IntType(8).as_pointer() and right.type == ir.IntType(8).as_pointer():
                    # String comparison using strcmp
                    cmp_result = builder.call(self.strcmp, [left, right], name="strcmp_result")
                    # strcmp returns <= 0 if left <= right
                    zero = ir.Constant(ir.IntType(32), 0)
                    is_less_equal = builder.icmp_signed("<=", cmp_result, zero, name="cmptmp")
                    result = builder.uitofp(is_less_equal, ir.DoubleType())
                else:
                    # Numeric comparison
                    cmp_result = builder.fcmp_ordered("<=", left, right, name="cmptmp")
                    result = builder.uitofp(cmp_result, ir.DoubleType())  # Convert to double
            elif op.token == '>=':
                # Greater than or equal comparison
                if left.type == ir.IntType(8).as_pointer() and right.type == ir.IntType(8).as_pointer():
                    # String comparison using strcmp
                    cmp_result = builder.call(self.strcmp, [left, right], name="strcmp_result")
                    # strcmp returns >= 0 if left >= right
                    zero = ir.Constant(ir.IntType(32), 0)
                    is_greater_equal = builder.icmp_signed(">=", cmp_result, zero, name="cmptmp")
                    result = builder.uitofp(is_greater_equal, ir.DoubleType())
                else:
                    # Numeric comparison
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
            elif op.token == '^':
                # Exponentiation: left ^ right
                result = builder.call(self.pow, [left, right], name="pow_result")
            else:
                raise NotImplementedError(f"Operator {op.token} not implemented")

            data_stack.append(result)

    def _codegen_if_simple(self, stmt, line_stmts=None, stmt_index=None):
        """Simple IF codegen that works like the Python interpreter"""
        # Evaluate the condition
        condition_val = self._codegen_expr(stmt._tokens)

        # Compare to zero to get boolean condition
        zero = ir.Constant(ir.DoubleType(), 0.0)
        condition = self.builder.fcmp_ordered("!=", condition_val, zero, name="if_condition")

        # Find where the ELSE statement is on this line (if any)
        else_stmt_index = None
        if line_stmts and stmt_index is not None:
            for i in range(stmt_index + 1, len(line_stmts)):
                if isinstance(line_stmts[i], ParsedStatementElse):
                    else_stmt_index = i
                    break

        # Create blocks
        func = self.builder.block.function
        true_block = func.append_basic_block(name=f"if_true_{stmt_index}_{self.current_line_index}")
        if else_stmt_index is not None:
            false_block = func.append_basic_block(name=f"if_else_{stmt_index}_{self.current_line_index}")
        else:
            false_block = func.append_basic_block(name=f"if_false_{stmt_index}_{self.current_line_index}")
        after_block = func.append_basic_block(name=f"if_after_{stmt_index}_{self.current_line_index}")

        # Branch based on condition
        if not self.builder.block.is_terminated:
            self.builder.cbranch(condition, true_block, false_block)

        # TRUE block: execute THEN statements
        self.builder.position_at_end(true_block)
        if line_stmts and stmt_index is not None:
            k = stmt_index + 1
            while k < len(line_stmts) and not isinstance(line_stmts[k], ParsedStatementElse):
                self._generate_statement_ir(line_stmts[k], line_stmts, k)
                if self.builder.block.is_terminated:
                    break
                k += 1

        # Branch to after block if not terminated
        if not self.builder.block.is_terminated:
            self.builder.branch(after_block)

        # FALSE block: execute ELSE statements or jump to after
        self.builder.position_at_end(false_block)
        if else_stmt_index is not None:
            # Execute ELSE statements
            k = else_stmt_index + 1
            while k < len(line_stmts):
                self._generate_statement_ir(line_stmts[k], line_stmts, k)
                if self.builder.block.is_terminated:
                    break
                k += 1

        # Branch to after block if not terminated
        if not self.builder.block.is_terminated:
            self.builder.branch(after_block)

        # Continue execution from after block
        self.builder.position_at_end(after_block)

    def _codegen_goto(self, stmt):
        target_line = int(stmt.destination)
        if target_line in self.line_blocks:
            # Check if this is GOSUB or GOTO
            is_gosub = stmt.keyword.name == "GOSUB"

            # Normal unconditional GOTO/GOSUB (only if current block is not terminated)
            if not self.builder.block.is_terminated:
                if is_gosub:
                    # For GOSUB, push return address and branch
                    # This method is only called for standalone GOSUB (not compound statements)
                    # Find the next line to return to using tracked index
                    if self.current_line_index + 1 < len(self.program):
                        next_line = self.program[self.current_line_index + 1].line
                        self._push_return_address(next_line)
                        if self.debug:
                            print(
                                f"DEBUG: GOSUB from line {self.program[self.current_line_index].line} to {target_line}, return to {next_line}")

                    self.builder.branch(self.line_blocks[target_line])
                else:
                    # Normal GOTO
                    self.builder.branch(self.line_blocks[target_line])
        else:
            raise Exception(f"GOTO/GOSUB target line not found: {target_line}")

    def _codegen_else(self, stmt):
        """Generate LLVM IR for ELSE - jump to next line"""
        if not self.builder.block.is_terminated:
            # Find next line and jump to it
            if self.current_line_index + 1 < len(self.program):
                next_line_num = self.program[self.current_line_index + 1].line
                self.builder.branch(self.line_blocks[next_line_num])
            else:
                self.builder.ret(ir.Constant(ir.IntType(32), 0))

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
        """Generate LLVM IR for a DIM statement - create global or dynamic arrays (BASIC semantics)"""
        lexer = get_lexer()
        for name, dimensions in stmt._dimensions:
            # Try to parse all dimensions as constants
            all_constant = True
            const_dims = []
            dim_tokens_list = []
            for dim_expr in dimensions:
                tokens = lexer.lex(dim_expr)
                dim_tokens_list.append(tokens)
                try:
                    # Only allow integer constants
                    if len(tokens) == 1 and tokens[0].type == 'num':
                        dim = int(float(tokens[0].token))
                        const_dims.append(dim)
                    else:
                        all_constant = False
                        const_dims.append(None)
                except Exception:
                    all_constant = False
                    const_dims.append(None)

            is_string_array = name.endswith("$")
            element_type = ir.IntType(8).as_pointer() if is_string_array else ir.DoubleType()

            if all_constant:
                # Static allocation as before
                total_size = 1
                for dim in const_dims:
                    total_size *= (dim + 1)
                array_type = ir.ArrayType(element_type, total_size)
                default_value = ir.Constant(element_type, None) if is_string_array else ir.Constant(element_type, 0.0)
                array_init = ir.Constant(array_type, [default_value] * total_size)
                global_array = ir.GlobalVariable(self.module, array_type, name=f"global_array_{name}")
                global_array.linkage = 'internal'
                global_array.global_constant = False
                global_array.initializer = array_init
                # For string arrays, initialize to empty string at runtime
                if is_string_array:
                    empty_str_val = "\0"
                    c_empty_str = ir.Constant(ir.ArrayType(ir.IntType(8), len(empty_str_val)),
                                              bytearray(empty_str_val.encode("utf8")))
                    global_empty_str = ir.GlobalVariable(self.module, c_empty_str.type, name=f"empty_str_{name}")
                    global_empty_str.linkage = 'internal'
                    global_empty_str.global_constant = True
                    global_empty_str.initializer = c_empty_str
                    empty_ptr = self.builder.bitcast(global_empty_str, element_type)
                    for i in range(total_size):
                        element_ptr = self.builder.gep(global_array,
                                                       [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), i)])
                        self.builder.store(empty_ptr, element_ptr)
                self.array_info[name] = {
                    'storage': global_array,
                    'dimensions': const_dims,
                    'total_size': total_size,
                    'is_string': is_string_array,
                    'dynamic': False
                }
                self.symbol_table[name] = global_array
            else:
                # Dynamic allocation at runtime
                # Evaluate each dimension expression at runtime
                dim_vals = []
                for tokens in dim_tokens_list:
                    val = self._codegen_expr(tokens)
                    # Convert to integer
                    val_int = self.builder.fptoui(val, ir.IntType(32))
                    dim_vals.append(val_int)
                # Compute total size = product of (dim + 1) for each dimension
                total_size = ir.Constant(ir.IntType(32), 1)
                for dim in dim_vals:
                    plus_one = self.builder.add(dim, ir.Constant(ir.IntType(32), 1))
                    total_size = self.builder.mul(total_size, plus_one)
                # Allocate array with malloc
                elem_size = ir.Constant(ir.IntType(64), 8) if is_string_array else ir.Constant(ir.IntType(64), 8)
                # For double and pointer, both 8 bytes on 64-bit
                total_bytes = self.builder.zext(total_size, ir.IntType(64))
                total_bytes = self.builder.mul(total_bytes, elem_size)
                arr_ptr = self.builder.call(self.malloc, [total_bytes], name=f"dyn_array_{name}")
                # Cast to appropriate pointer type
                arr_ptr_cast = self.builder.bitcast(arr_ptr, element_type.as_pointer())
                # Store pointer in a global variable
                global_ptr = ir.GlobalVariable(self.module, element_type.as_pointer(), name=f"dyn_array_ptr_{name}")
                global_ptr.linkage = 'internal'
                global_ptr.global_constant = False
                global_ptr.initializer = ir.Constant(element_type.as_pointer(), None)
                self.builder.store(arr_ptr_cast, global_ptr)
                # For string arrays, initialize each element to empty string
                if is_string_array:
                    empty_str_val = "\0"
                    c_empty_str = ir.Constant(ir.ArrayType(ir.IntType(8), len(empty_str_val)),
                                              bytearray(empty_str_val.encode("utf8")))
                    global_empty_str = ir.GlobalVariable(self.module, c_empty_str.type, name=f"empty_str_{name}")
                    global_empty_str.linkage = 'internal'
                    global_empty_str.global_constant = True
                    global_empty_str.initializer = c_empty_str
                    empty_ptr = self.builder.bitcast(global_empty_str, element_type)
                    # Loop to initialize
                    idx_var = self.builder.alloca(ir.IntType(32), name=f"init_idx_{name}")
                    self.builder.store(ir.Constant(ir.IntType(32), 0), idx_var)
                    loop_block = self.builder.append_basic_block(f"init_loop_{name}")
                    after_block = self.builder.append_basic_block(f"after_init_{name}")
                    self.builder.branch(loop_block)
                    self.builder.position_at_end(loop_block)
                    idx = self.builder.load(idx_var)
                    cond = self.builder.icmp_signed('<', idx, total_size)
                    self.builder.cbranch(cond, loop_block, after_block)
                    # Store empty_ptr at arr_ptr_cast[idx]
                    arr_gep = self.builder.gep(arr_ptr_cast, [idx])
                    self.builder.store(empty_ptr, arr_gep)
                    # idx++
                    idx_next = self.builder.add(idx, ir.Constant(ir.IntType(32), 1))
                    self.builder.store(idx_next, idx_var)
                    self.builder.branch(loop_block)
                    self.builder.position_at_end(after_block)
                # Store array info
                self.array_info[name] = {
                    'storage': global_ptr,
                    'dimensions': dim_vals,  # These are LLVM values, not ints
                    'total_size': total_size,
                    'is_string': is_string_array,
                    'dynamic': True
                }
                self.symbol_table[name] = global_ptr

    def _codegen_array_access(self, array_name, indices, builder=None):
        """Generate LLVM IR for array access"""
        if builder is None:
            builder = self.builder

        if array_name not in self.array_info:
            raise Exception(f"Array {array_name} not declared")

        array_info = self.array_info[array_name]
        array_storage = array_info['storage']
        dimensions = array_info['dimensions']
        is_dynamic = array_info.get('dynamic', False)

        # Convert indices to 0-based and calculate offset
        if len(indices) != len(dimensions):
            raise Exception(f"Array {array_name} has {len(dimensions)} dimensions, got {len(indices)} indices")

        # For dynamic arrays, use only LLVM IR values for offset and multiplier
        if is_dynamic:
            offset = ir.Constant(ir.IntType(32), 0)
            multiplier = ir.Constant(ir.IntType(32), 1)
            for i in range(len(indices) - 1, -1, -1):
                index_val = builder.fptoui(indices[i], ir.IntType(32))
                one = ir.Constant(ir.IntType(32), 1)
                zero_based_index = builder.sub(index_val, one)
                index_offset = builder.mul(zero_based_index, multiplier)
                offset = builder.add(offset, index_offset)
                if i > 0:
                    # multiplier *= (dimensions[i] + 1) where dimensions[i] is an LLVM value
                    plus_one = builder.add(dimensions[i], one)
                    multiplier = builder.mul(multiplier, plus_one)
            # For dynamic arrays, array_storage is a pointer to the malloc'd array
            arr_ptr = builder.load(array_storage)
            element_ptr = builder.gep(arr_ptr, [offset])
            return element_ptr
        else:
            # Static array logic (Python ints)
            offset = ir.Constant(ir.IntType(32), 0)
            multiplier = 1
            for i in range(len(indices) - 1, -1, -1):
                index_val = builder.fptoui(indices[i], ir.IntType(32))
                one = ir.Constant(ir.IntType(32), 1)
                zero_based_index = builder.sub(index_val, one)
                index_offset = builder.mul(zero_based_index, ir.Constant(ir.IntType(32), multiplier))
                offset = builder.add(offset, index_offset)
                if i > 0:
                    multiplier *= (dimensions[i] + 1)
            element_ptr = builder.gep(array_storage, [ir.Constant(ir.IntType(32), 0), offset])
            return element_ptr

    def _collect_data_values(self):
        """Collect all DATA values from the program at compile time."""
        for program_line in self.program:
            line_has_data = False
            line_start_index = len(self.data_values)

            for stmt in program_line.stmts:
                if isinstance(stmt, ParsedStatementData):
                    if not line_has_data:
                        # Record the starting index for this line's DATA
                        self.data_line_map[program_line.line] = line_start_index
                        line_has_data = True

                    # Add each data value from this DATA statement
                    self.data_values.extend(stmt._values)

        if self.debug:
            print(f"DEBUG: Collected {len(self.data_values)} DATA values: {self.data_values}")
            print(f"DEBUG: DATA line map: {self.data_line_map}")

    def _codegen_data(self, stmt):
        """Generate LLVM IR for a DATA statement (no-op since data is collected at compile time)."""
        # DATA statements are passive - all data is collected at compile time
        # and stored in global data structures
        pass

    def _codegen_read(self, stmt):
        """Generate LLVM IR for a READ statement."""
        # Initialize data pointer if not already done
        if self.data_ptr is None:
            self.data_ptr = ir.GlobalVariable(self.module, ir.IntType(32), name="data_ptr")
            self.data_ptr.linkage = 'internal'
            self.data_ptr.global_constant = False
            self.data_ptr.initializer = ir.Constant(ir.IntType(32), 0)

        # Create global array of data values (stored as strings for flexibility)
        if "data_values" not in self.module.globals:
            self._create_global_data_array()

        # Read each variable in the READ statement
        for var_name in stmt._variables:
            self._read_data_value(var_name)

    def _codegen_restore(self, stmt):
        """Generate LLVM IR for a RESTORE statement."""
        # Initialize data pointer if not already done
        if self.data_ptr is None:
            self.data_ptr = ir.GlobalVariable(self.module, ir.IntType(32), name="data_ptr")
            self.data_ptr.linkage = 'internal'
            self.data_ptr.global_constant = False
            self.data_ptr.initializer = ir.Constant(ir.IntType(32), 0)

        if stmt._line_number is None:
            # RESTORE without line number - reset to beginning
            self.builder.store(ir.Constant(ir.IntType(32), 0), self.data_ptr)
            if self.debug:
                print(f"DEBUG: RESTORE - reset to beginning")
        else:
            # RESTORE with line number - reset to specific line
            line_number = stmt._line_number

            if line_number in self.data_line_map:
                start_index = self.data_line_map[line_number]
                self.builder.store(ir.Constant(ir.IntType(32), start_index), self.data_ptr)
                if self.debug:
                    print(f"DEBUG: RESTORE {line_number} - reset to index {start_index}")
            else:
                # Line not found or doesn't contain DATA - generate runtime error
                error_msg = f"RESTORE {line_number}: Line does not contain DATA\\n\0"
                c_error_msg = ir.Constant(ir.ArrayType(ir.IntType(8), len(error_msg)),
                                          bytearray(error_msg.encode("utf8")))
                error_msg_name = f"restore_error_msg_{line_number}"
                if error_msg_name not in self.module.globals:
                    global_error_msg = ir.GlobalVariable(self.module, c_error_msg.type, name=error_msg_name)
                    global_error_msg.linkage = 'internal'
                    global_error_msg.global_constant = True
                    global_error_msg.initializer = c_error_msg
                else:
                    global_error_msg = self.module.get_global(error_msg_name)

                error_msg_ptr = self.builder.bitcast(global_error_msg, ir.IntType(8).as_pointer())
                self.builder.call(self.printf, [error_msg_ptr])
                self.builder.ret(ir.Constant(ir.IntType(32), 1))  # Exit with error

    def _create_global_data_array(self):
        """Create a global array containing all DATA values as strings."""
        if not self.data_values:
            return

        # Create array of string pointers
        str_ptr_type = ir.IntType(8).as_pointer()
        array_type = ir.ArrayType(str_ptr_type, len(self.data_values))

        # Create global constants for each data value
        data_constants = []
        for i, value in enumerate(self.data_values):
            # Create global string constant for this data value
            str_val = value
            if str_val.startswith('"') and str_val.endswith('"'):
                str_val = str_val[1:-1]  # Remove quotes
            str_val += "\0"  # Add null terminator

            c_str = ir.Constant(ir.ArrayType(ir.IntType(8), len(str_val)), bytearray(str_val.encode("utf8")))
            global_str = ir.GlobalVariable(self.module, c_str.type, name=f"data_str_{i}")
            global_str.linkage = 'internal'
            global_str.global_constant = True
            global_str.initializer = c_str

            # Get pointer to the string
            str_ptr = global_str.bitcast(str_ptr_type)
            data_constants.append(str_ptr)

        # Create the array initializer
        array_init = ir.Constant(array_type, data_constants)

        # Create global variable for the data array
        data_array = ir.GlobalVariable(self.module, array_type, name="data_values")
        data_array.linkage = 'internal'
        data_array.global_constant = True
        data_array.initializer = array_init

    def _read_data_value(self, var_name):
        """Read one data value and assign it to the specified variable."""
        # Get current data pointer value
        current_ptr = self.builder.load(self.data_ptr, name="current_data_ptr")

        # Check bounds
        max_index = ir.Constant(ir.IntType(32), len(self.data_values))
        bounds_check = self.builder.icmp_signed("<", current_ptr, max_index, name="bounds_check")

        # Create blocks for bounds check
        func = self.builder.block.function
        valid_block = func.append_basic_block(name="valid_data")
        error_block = func.append_basic_block(name="data_error")
        continue_block = func.append_basic_block(name="continue_read")

        # Branch based on bounds check
        self.builder.cbranch(bounds_check, valid_block, error_block)

        # Error block - print error and exit
        self.builder.position_at_end(error_block)
        error_msg = "I tried to READ, but ran out of data.\\n\0"
        c_error_msg = ir.Constant(ir.ArrayType(ir.IntType(8), len(error_msg)),
                                  bytearray(error_msg.encode("utf8")))
        error_msg_name = "read_error_msg"
        if error_msg_name not in self.module.globals:
            global_error_msg = ir.GlobalVariable(self.module, c_error_msg.type, name=error_msg_name)
            global_error_msg.linkage = 'internal'
            global_error_msg.global_constant = True
            global_error_msg.initializer = c_error_msg
        else:
            global_error_msg = self.module.get_global(error_msg_name)

        error_msg_ptr = self.builder.bitcast(global_error_msg, ir.IntType(8).as_pointer())
        self.builder.call(self.printf, [error_msg_ptr])
        self.builder.ret(ir.Constant(ir.IntType(32), 1))  # Exit with error

        # Valid block - get data value
        self.builder.position_at_end(valid_block)
        data_array = self.module.get_global("data_values")
        data_ptr_val = self.builder.gep(data_array, [ir.Constant(ir.IntType(32), 0), current_ptr])
        data_str_ptr = self.builder.load(data_ptr_val, name="data_str_ptr")

        # Determine if this is a string or numeric variable
        is_string_var = self._is_string_variable(var_name)

        if is_string_var:
            # String variable - assign the string directly
            self._assign_string_variable(var_name, data_str_ptr)
        else:
            # Numeric variable - convert string to number
            self._assign_numeric_variable(var_name, data_str_ptr)

        # Increment data pointer
        next_ptr = self.builder.add(current_ptr, ir.Constant(ir.IntType(32), 1), name="next_data_ptr")
        self.builder.store(next_ptr, self.data_ptr)

        # Continue to next variable
        self.builder.branch(continue_block)
        self.builder.position_at_end(continue_block)

    def _is_string_variable(self, var_name):
        """Check if a variable name refers to a string variable."""
        var_clean = var_name.replace(" ", "")
        i = var_clean.find("(")
        if i != -1:
            # Array element - check base variable name
            base_var = var_clean[:i]
            return base_var.endswith("$")
        else:
            # Simple variable
            return var_name.endswith("$")

    def _assign_string_variable(self, var_name, str_ptr):
        """Assign a string value to a string variable."""
        if self._is_array_element(var_name):
            # Array element assignment
            self._assign_array_element(var_name, str_ptr)
        else:
            # Simple string variable assignment
            if var_name not in self.symbol_table:
                # Create the variable if it doesn't exist
                global_var = ir.GlobalVariable(self.module, ir.IntType(8).as_pointer(), name=f"global_{var_name}")
                global_var.linkage = 'internal'
                global_var.global_constant = False
                global_var.initializer = ir.Constant(ir.IntType(8).as_pointer(), None)
                self.symbol_table[var_name] = global_var

            var_ptr = self.symbol_table[var_name]
            self.builder.store(str_ptr, var_ptr)

    def _assign_numeric_variable(self, var_name, str_ptr):
        """Convert string to number and assign to numeric variable."""
        # Use sscanf to parse the number from the string
        double_fmt = "%lf\0"
        c_double_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(double_fmt)),
                                   bytearray(double_fmt.encode("utf8")))
        double_fmt_name = "double_parse_fmt"
        if double_fmt_name not in self.module.globals:
            global_double_fmt = ir.GlobalVariable(self.module, c_double_fmt.type, name=double_fmt_name)
            global_double_fmt.linkage = 'internal'
            global_double_fmt.global_constant = True
            global_double_fmt.initializer = c_double_fmt
        else:
            global_double_fmt = self.module.get_global(double_fmt_name)

        double_fmt_ptr = self.builder.bitcast(global_double_fmt, ir.IntType(8).as_pointer())

        # Allocate temporary variable for parsing
        temp_double = self.builder.alloca(ir.DoubleType(), name="temp_double")

        # Parse the string to double
        self.builder.call(self.sscanf, [str_ptr, double_fmt_ptr, temp_double])
        parsed_value = self.builder.load(temp_double, name="parsed_value")

        if self._is_array_element(var_name):
            # Array element assignment
            self._assign_array_element(var_name, parsed_value)
        else:
            # Simple numeric variable assignment
            if var_name not in self.symbol_table:
                # Create the variable if it doesn't exist
                global_var = ir.GlobalVariable(self.module, ir.DoubleType(), name=f"global_{var_name}")
                global_var.linkage = 'internal'
                global_var.global_constant = False
                global_var.initializer = ir.Constant(ir.DoubleType(), 0.0)
                self.symbol_table[var_name] = global_var

            var_ptr = self.symbol_table[var_name]
            self.builder.store(parsed_value, var_ptr)

    def _is_array_element(self, var_name):
        """Check if a variable name refers to an array element."""
        return "(" in var_name and ")" in var_name

    def _assign_array_element(self, var_name, value):
        """Assign a value to an array element."""
        # Parse array name and indices
        var_clean = var_name.replace(" ", "")
        i = var_clean.find("(")
        j = var_clean.rfind(")")

        array_name = var_clean[:i]
        indices_str = var_clean[i + 1:j]

        # Parse indices (handle multiple dimensions)
        indices = [idx.strip() for idx in indices_str.split(",")]

        # Evaluate each index expression
        lexer = get_lexer()
        index_values = []
        for idx in indices:
            idx_tokens = lexer.lex(idx)
            idx_value = self._codegen_expr(idx_tokens)
            index_values.append(idx_value)

        # Get array storage
        if array_name not in self.array_info:
            raise Exception(f"Array {array_name} not found")

        array_info = self.array_info[array_name]
        array_storage = array_info['storage']

        # Calculate linear index for multi-dimensional arrays
        if len(index_values) == 1:
            # 1D array
            index_val = self.builder.fptoui(index_values[0], ir.IntType(32))
            # Convert to 0-based index (BASIC arrays are 1-based by default)
            one = ir.Constant(ir.IntType(32), 1)
            zero_based_index = self.builder.sub(index_val, one)
        else:
            # Multi-dimensional array - calculate linear index
            # For array A(m,n), index A(i,j) = i*(n+1) + j (0-based)
            # Since BASIC arrays are 1-based, DIM S(3,3) creates a 4x4 array
            dimensions = array_info['dimensions']
            linear_index = None

            for dim_idx, idx_val in enumerate(index_values):
                # Convert to 0-based
                idx_int = self.builder.fptoui(idx_val, ir.IntType(32))
                one = ir.Constant(ir.IntType(32), 1)
                zero_based_idx = self.builder.sub(idx_int, one)

                if dim_idx == 0:
                    # First dimension
                    if len(dimensions) > 1:
                        # Multiply by size of remaining dimensions (dimension+1 for 1-based)
                        multiplier = ir.Constant(ir.IntType(32), dimensions[1] + 1)
                        linear_index = self.builder.mul(zero_based_idx, multiplier)
                    else:
                        linear_index = zero_based_idx
                else:
                    # Subsequent dimensions
                    if linear_index is None:
                        linear_index = zero_based_idx
                    else:
                        linear_index = self.builder.add(linear_index, zero_based_idx)

            zero_based_index = linear_index

        # Get element pointer and store value
        element_ptr = self.builder.gep(array_storage, [ir.Constant(ir.IntType(32), 0), zero_based_index])
        self.builder.store(value, element_ptr)


def generate_llvm_ir(program, debug=False, trace=False):
    codegen = LLVMCodeGenerator(program, debug=debug, trace=trace)
    return codegen.generate_ir()
