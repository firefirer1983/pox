# cox — C 语言解释器（《Crafting Interpreters》clox 部分）
#
# 常用命令:
#   make               # 调试构建（默认，带 ASan/UBSan）
#   make run           # 编译并运行
#   make BUILD=release # 发布构建（-O2，无 sanitizer）
#   make gdb           # 用 gdb 调试
#   make clean         # 清理所有构建产物

CC       := cc
BUILD    ?= debug

ifeq ($(filter $(BUILD),debug release),)
$(error 未知的 BUILD="$(BUILD)"，可选值: debug, release)
endif

BIN_DIR  := build/$(BUILD)
BIN      := $(BIN_DIR)/cox

SRCS := $(wildcard *.c)
OBJS := $(SRCS:%.c=$(BIN_DIR)/%.o)
DEPS := $(OBJS:.o=.d)

WARNINGS := -Wall -Wextra

# 调试构建: 不优化、带调试符号，并开启 AddressSanitizer/UBSan，
# 内存错误（越界、use-after-free、double-free）会在运行时直接报告
CFLAGS_debug  := $(WARNINGS) -std=c11 -g -O0 -fno-omit-frame-pointer \
                 -fsanitize=address,undefined
LDFLAGS_debug := -fsanitize=address,undefined

# 发布构建: 开优化，关断言
CFLAGS_release  := $(WARNINGS) -std=c11 -O2 -DNDEBUG
LDFLAGS_release :=

CFLAGS  := $(CFLAGS_$(BUILD))
LDFLAGS := $(LDFLAGS_$(BUILD))

.PHONY: all run gdb clean

all: $(BIN)

$(BIN): $(OBJS)
	$(CC) $(LDFLAGS) -o $@ $^

$(BIN_DIR)/%.o: %.c | $(BIN_DIR)
	$(CC) $(CFLAGS) -MMD -MP -c $< -o $@

$(BIN_DIR):
	mkdir -p $@

run: $(BIN)
	./$(BIN)

gdb: $(BIN)
	gdb $(BIN)

clean:
	rm -rf build

# 自动生成的头文件依赖：改 .h 也会触发对应 .c 重新编译
-include $(DEPS)
