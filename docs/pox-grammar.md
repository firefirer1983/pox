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

fun_decl       ::= "fun" IDENTIFIER "(" [ IDENTIFIER ( "," IDENTIFIER )* ] ")"
                   block ;                                   (* func_declaration, :143 *)

var_decl       ::= "var" IDENTIFIER [ "=" expression ] ";" ; (* var_declaration, :133 *)

statement      ::= if_stmt | print_stmt | return_stmt
                 | for_stmt | while_stmt | block | expr_stmt ;
                                                               (* statement, :239 *)

if_stmt        ::= "if" "(" expression ")" statement
                   [ "else" statement ] ;                     (* if_stmt, :177 *)

while_stmt     ::= "while" "(" expression ")" statement ;    (* while_stmt, :189 *)

(* 注意：for 在解析阶段被脱糖为 Block/While，AST 中没有 For 节点 *)
for_stmt       ::= "for" "("
                     ( var_decl | expression ";" | ";" )   (* 初始化 *)
                     [ expression ] ";"                    (* 条件，缺省为 true *)
                     [ expression ]                        (* 增量 *)
                   ")" block ;                              (* for_stmt, :207 *)

return_stmt    ::= "return" [ expression ] ";" ;             (* return_stmt, :198 *)

print_stmt     ::= "print" expression ";" ;                  (* print_stmt, :263 *)

expr_stmt      ::= expression ";" ;                          (* expr_stmt, :256 *)

block          ::= "{" declaration* "}" ;                    (* block, :163 *)

(* ============ 表达式：优先级自低到高 ============ *)

expression     ::= assignment ;                              (* expression, :270 *)

assignment     ::= or_expr [ "=" or_expr ] ;                 (* assignment, :274 *)
                   (* 语义约束：左部为 Variable 时生成 Assign，
                      为 Get 时生成 Set，否则原样返回左部 *)

or_expr        ::= and_expr [ "or" and_expr ] ;              (* or_expr, :288 *)

and_expr       ::= equality [ ( "and" | "or" ) or_expr ] ;   (* and_expr, :298 *)

equality       ::= comparison ( ("==" | "!=") comparison )* ;   (* equality, :308 *)

comparison     ::= term ( (">" | ">=" | "<" | "<=") term )* ;   (* comparision, :316 *)

term           ::= factor ( ("+" | "-") factor )* ;          (* term, :331 *)

factor         ::= unary ( ("*" | "/") unary )* ;            (* factor, :340 *)

unary          ::= ("-" | "!") unary | call ;                (* unary, :379 *)

call           ::= primary ( "(" arguments ")" | "." IDENTIFIER )* ;  (* call, :362 *)

arguments      ::= [ expression ( "," expression )* ] ;      (* _call, :348 *)

primary        ::= "true" | "false" | "nil" | "this"
                 | NUMBER | STRING
                 | "(" expression ")"
                 | IDENTIFIER ;                              (* primary, :386 *)
```

## 与标准 Lox 文法的差异（按实际代码整理）

1. **赋值不可嵌套**：`assignment` 的右部递归调用的是 `or_expr`
   而非 `assignment`（`parser.py:278`），
   因此 `a = b = 1;` 中右侧的 `b = 1` 并非按嵌套赋值解析。
   标准写法应为 `assignment ::= or_expr ( "=" assignment )?`（右结合）。

2. **`or` / `and` 的解析混在一起**（`parser.py:298-305`）：
   `and_expr` 中 `match(AND, OR)` 同时接受两种关键字，
   且右部调用 `or_expr`，使 `and`/`or` 实际上右结合且可相互嵌套；
   两者都只匹配一次，链式 `a or b or c` 无法在文法层表达。

3. **赋值失败时不报错**：`assignment` 中若 `=` 已消费但左部
   既非 `Variable` 也非 `Get`，函数直接返回左部表达式，
   已消费的 `=` token 被丢弃，不会抛出 `ParseError`。

4. **`for` 被脱糖**：解析产物为
   `Block([initializer, While(cond, Block(body + increment))])`，
   循环体必须是 `{...}` 块（文法中直接写为 `block`），
   而标准 Lox 允许任意 statement 作为循环体。

5. **类方法省略 `fun` 关键字，与标准 Lox 一致**：
   `fun` 在 `declaration()`（`parser.py:110`）中被消费，
   而 `class_declaration` 的类体循环（`parser.py:128`）直接调用
   `func_declaration()`（其从函数名开始解析，不消费 `fun`），
   因此方法写作 `class A { m() {} }`；
   若写成 `class A { fun m() {} }` 反而会因 `consume(IDENTIFIER)`
   收到 `FUN` token 而报 `ParseError`。

## 优先级与结合性总表

| 优先级（低→高） | 产生式 | 运算符 | 结合性 |
|---|---|---|---|
| 1 | assignment | `=` | 右（受实现限制，见差异 1） |
| 2 | or_expr | `or` | 右（单层） |
| 3 | and_expr | `and` / `or` | 右（单层） |
| 4 | equality | `==` `!=` | 左 |
| 5 | comparison | `>` `>=` `<` `<=` | 左 |
| 6 | term | `+` `-` | 左 |
| 7 | factor | `*` `/` | 左 |
| 8 | unary | `-` `!` | 右（一元递归） |
| 9 | call | `()` `.` | 左 |
| 10 | primary | 字面量 / 标识符 / 分组 | — |
