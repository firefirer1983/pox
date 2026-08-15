# pox 上下文无关文法（Context-Free Grammar）

本文根据 `pox/parser.py` 的递归下降解析器整理，
采用扩展巴科斯范式（EBNF）表示：
`*` 表示重复零次或多次，`?` 表示出现零次或一次，`|` 表示选择。
每条产生式后注明对应的解析方法及源码位置。

终结符用引号或大写标记：
关键字 `class fun var if else print return for while and or true false nil this`、
运算符 `= == != > >= < <= + - * / ! . , ; ( ) { }`、
以及 `IDENTIFIER` `NUMBER` `STRING`（由 scanner 产生的 token）。

## 文法

```ebnf
program        ::= declaration* EOF ;                        (* Parser.parse, :92 *)

declaration    ::= class_decl | fun_decl | var_decl | statement ;
                                                               (* declaration, :106 *)

class_decl     ::= "class" IDENTIFIER "{" fun_decl* "}" ;    (* class_declaration, :119 *)
                   (* 类体直调 func_declaration（:128），不经过消费 "fun" 的
                      declaration 层，故方法省略 "fun" 关键字，与标准 Lox 一致 *)

fun_decl       ::= "fun" IDENTIFIER "(" [ IDENTIFIER ( "," IDENTIFIER )* ] ")"
                   block ;                                   (* func_declaration, :143 *)

var_decl       ::= "var" IDENTIFIER [ "=" expression ] ";" ; (* var_declaration, :133 *)

statement      ::= if_stmt | print_stmt | return_stmt
                 | for_stmt | while_stmt | block | expr_stmt ;
                                                               (* statement, :242 *)

if_stmt        ::= "if" "(" expression ")" statement
                   [ "else" statement ] ;                     (* if_stmt, :177 *)

while_stmt     ::= "while" "(" expression ")" statement ;    (* while_stmt, :189 *)

(* 注意：for 在解析阶段被脱糖为 Block/While，AST 中没有 For 节点 *)
for_stmt       ::= "for" "("
                     ( var_decl | expression ";" | ";" )   (* 初始化 *)
                     [ expression ] ";"                    (* 条件，缺省为 true *)
                     [ expression ]                        (* 增量 *)
                   ")" statement ;                          (* for_stmt, :207 *)
                   (* 循环体为任意 statement（:227-230）：
                      若带 "{" 则解析为 block，否则用 Stmt.Block 包住单条语句，
                      以便把增量追加到体末尾 *)

return_stmt    ::= "return" [ expression ] ";" ;             (* return_stmt, :198 *)

print_stmt     ::= "print" expression ";" ;                  (* print_stmt, :266 *)

expr_stmt      ::= expression ";" ;                          (* expr_stmt, :259 *)

block          ::= "{" declaration* "}" ;                    (* block, :163 *)

(* ============ 表达式：优先级自低到高 ============ *)

expression     ::= assignment ;                              (* expression, :273 *)

assignment     ::= or_expr [ "=" assignment ] ;              (* assignment, :277 *)
                   (* 右结合，a = b = 1 可正确嵌套；
                      语义约束：左部为 Variable 时生成 Assign，
                      为 Get 时生成 Set，否则抛出 ParseError（:289） *)

or_expr        ::= and_expr ( "or" and_expr )* ;             (* or_expr, :293 *)
                   (* 左结合，支持链式，与标准 Lox 一致 *)

and_expr       ::= equality ( "and" equality )* ;            (* and_expr, :303 *)
                   (* 左结合，支持链式，与标准 Lox 一致 *)

equality       ::= comparison ( ("==" | "!=") comparison )* ;   (* equality, :313 *)

comparison     ::= term ( (">" | ">=" | "<" | "<=") term )* ;   (* comparision, :321 *)

term           ::= factor ( ("+" | "-") factor )* ;          (* term, :336 *)

factor         ::= unary ( ("*" | "/") unary )* ;            (* factor, :345 *)

unary          ::= ("-" | "!") unary | call ;                (* unary, :384 *)

call           ::= primary ( "(" arguments ")" | "." IDENTIFIER )* ;  (* call, :367 *)

arguments      ::= [ expression ( "," expression )* ] ;      (* _call, :353 *)

primary        ::= "true" | "false" | "nil" | "this"
                 | NUMBER | STRING
                 | "(" expression ")"
                 | IDENTIFIER ;                              (* primary, :391 *)
```

## 与标准 Lox 文法的差异（按实际代码整理）

1. **继承与 `super` 未实现**：标准 Lox 的
   `classDecl ::= "class" IDENTIFIER ( "<" IDENTIFIER )? "{" function* "}"`
   与 `primary` 中的 `"super" "." IDENTIFIER` 在 pox 中均无对应产生式。
   属于功能缺失，而非文法错误。

## 已与标准一致的项（曾经存在差异，现已修复）

- 赋值右结合、可嵌套：`assignment` 右部递归调用 `assignment`（`parser.py:281`）。
- 赋值左部非法时报错：不再静默丢弃 `=`，抛出 `ParseError`（`parser.py:289`）。
- `or` 左结合、可链式：`or_expr` 使用 `while` 循环（`parser.py:295`）。
- `and` 左结合、优先级高于 `or`：`and_expr` 使用 `while` 循环，
  右部为 `equality`，不再回跳 `or_expr`（`parser.py:303-310`）。
- `for` 循环体为任意 statement：无 `{` 时用 `Stmt.Block` 包住单条语句（`parser.py:227-230`）。
- 类方法省略 `fun` 关键字：与标准 Lox 一致（`fun` 在 `declaration()` 层消费，
  类体直调 `func_declaration()`）。

## 优先级与结合性总表

| 优先级（低→高） | 产生式 | 运算符 | 结合性 |
|---|---|---|---|
| 1 | assignment | `=` | 右 |
| 2 | or_expr | `or` | 左 |
| 3 | and_expr | `and` | 左 |
| 4 | equality | `==` `!=` | 左 |
| 5 | comparison | `>` `>=` `<` `<=` | 左 |
| 6 | term | `+` `-` | 左 |
| 7 | factor | `*` `/` | 左 |
| 8 | unary | `-` `!` | 右（一元递归） |
| 9 | call | `()` `.` | 左 |
| 10 | primary | 字面量 / 标识符 / 分组 | — |
