这份 README 描述的是一个相当完整的**教学型 Decaf 编译器**：从源代码一路做到 MIPS，而不是只做到 AST 或语义检查。

核心流水线可以压缩成：

```text
Decaf Source
    ↓
Scanner / Flex
词法分析：字符 → Token
    ↓
Parser / Bison
语法分析：Token → AST
    ↓
Symbol Table
符号表 / 作用域
    ↓
Semantic Analysis
类型、继承、接口、override、调用检查
    ↓
TAC
三地址码 IR
    ↓
Code Generation
MIPS Assembly
    ↓
SPIM
执行
```

你可以把它当成一门编译原理课程的“纵向主线项目”。它最值得读的并不是 MIPS 本身，而是观察**高级语言语义怎样一层层降低到机器级表示**。

### 这 7 个 Pass 分别解决什么

| Pass | 阶段 | 本质问题 |
|---|---|---|
| 0 | Flex + Bison + AST | 程序“写的是什么结构”？ |
| 1 | Symbol Table | 声明了哪些名字？名字属于哪个作用域？ |
| 2 | Identifier Resolution | `x`、`foo`、`obj.a` 到底指谁？ |
| 3 | Inheritance | 类/接口/override 关系是否合法？ |
| 4 | Type Checking | 表达式、调用、赋值等在语义上是否合法？ |
| 5 | TAC | 如何把高级语言转换成简单 IR？ |
| 6 | MIPS | IR 如何变成真正可执行的机器指令？ |

其中 **Pass 1 → 4** 特别值得仔细看。很多 CRUD 工程师学编译原理时容易把注意力集中到 Flex/Bison，其实现代编译器里更重要、更复杂的是 AST 之后的部分。

例如：

```java
class Animal {
    void speak() { ... }
}

class Dog extends Animal {
    void speak() { ... }
}

Animal a = new Dog();
a.speak();
```

这个看似普通的调用，会一路涉及：

```text
AST
 ↓
名字解析
 ↓
类型检查
 ↓
继承关系分析
 ↓
override 检查
 ↓
对象布局
 ↓
VTable
 ↓
动态分派
 ↓
TAC
 ↓
MIPS 间接调用
```

因此 README 中的：

> Create VTable to support dynamically dispatching of virtual methods

其实是整个项目非常值得研究的一块。它能把你平时 C++/Java 里的“虚函数/动态分派”直接连接到**对象内存布局、函数地址和汇编间接调用**。

### 建议不要按照文件名顺序硬啃

第一轮建议走“编译流水线”：

```text
main.cc
  ↓
scanner.l
  ↓
parser.y
  ↓
ast*.h / ast*.cc
  ↓
symtab.*
  ↓
ast_stmt.cc
  ↓
tac.*
  ↓
codegen.*
  ↓
mips.*
```

然后拿一个极小 Decaf 程序贯穿全过程，例如：

```java
void main() {
    int a;
    int b;

    a = 10;
    b = a + 20;

    Print(b);
}
```

分别执行：

```bash
./dcc -d ast < test.decaf
./dcc -d st < test.decaf
./dcc -d tac < test.decaf
./dcc < test.decaf > test.asm
```

不要一开始研究 `tictactoe.decaf`。大型测试适合验证 compiler，**小程序更适合理解 compiler**。

第二轮再专门追踪一个表达式：

```text
b = a + 20
```

研究它如何经历：

```text
源代码
→ token
→ AST node
→ identifier lookup
→ type checking
→ TAC
→ MIPS
```

这一步完成以后，你基本就建立起了这个项目的骨架。

### 和你之前学 ABI / 汇编的路线正好能接起来

这个项目可以把几个原本分散的问题连接起来：

```text
高级语言
   │
   ├── 类型系统
   ├── 类 / 继承 / virtual
   ├── 函数调用
   │
Compiler
   │
   ├── AST
   ├── Symbol Table
   ├── IR / TAC
   ├── Object Layout
   ├── VTable
   │
ABI / Runtime Convention
   │
   ├── 参数怎么传
   ├── 返回值怎么传
   ├── stack frame
   ├── register
   ├── object layout
   │
Assembly
   ↓
Machine Code
```

不过要特别注意：**Decaf + MIPS/SPIM 是教学模型，不等于现代 GCC/Clang 的真实实现。**

如果最终目标是理解现代软件错误、ABI 和底层调试，我建议把这个 Decaf 项目定位为：

**“第一遍完整走通 compiler pipeline 的小型编译器。”**

走完以后再升级到：

```text
Decaf
   ↓
LLVM Kaleidoscope
   ↓
LLVM IR
   ↓
Clang
   ↓
GCC / LLVM 某些具体 Pass
```

这样再看：

```text
C++
↓
Clang AST
↓
LLVM IR
↓
优化 Pass
↓
x86-64 / AArch64
↓
ELF
↓
ABI
↓
linker / loader
↓
runtime
```

会比直接扎进 LLVM/GCC 几百万行代码容易得多。
