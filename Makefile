##
## EPITECH PROJECT, 2024
## __
## File description:
## ./Makefile
##

MAKEFLAGS += -j

BIN_NAME := panoramix

SRC := $(wildcard src/*.c)

BUILD_DIR := .build

CC := clang

CFLAGS += -Wall -Wextra -Werror=write-strings -iquote ulib -iquote src
CFLAGS += -Wno-unused-parameter -Wunused-result
CFLAGS += -Wp,-U_FORTIFY_SOURCE -Wcast-qual
CFLAGS += -Wformat=2 -Wshadow -fno-builtin
CFLAGS += -Wstrict-aliasing=0 -Wstrict-prototypes -Wunreachable-code
CFLAGS += -Wwrite-strings -Werror=declaration-after-statement
CFLAGS += -Werror=format-nonliteral -Werror=int-conversion -Werror=return-type
CFLAGS += --std=gnu2x

LDLIBS += -lpthread

include utils.mk

.PHONY: _start all
_start: all

# call mk-profile release, SRC, additional CFLAGS
define mk-profile

NAME_$(strip $1) := $4
OBJ_$(strip $1) := $$($(strip $2):%.c=$$(BUILD_DIR)/$(strip $1)/%.o)

$$(BUILD_DIR)/$(strip $1)/%.o: %.c
	@ mkdir -p $$(dir $$@)
	@ $$(CC) $$(CFLAGS) -o $$@ -c $$<
	@ $$(LOG_TIME) "$$(C_GREEN) CC $$(C_PURPLE) $$(notdir $$@) $$(C_RESET)"

$$(NAME_$(strip $1)): $$(LIB_NAME_$(strip $1)) $$(OBJ_$(strip $1))
	@ $$(CC) $$(OBJ_$(strip $1)) $$(LDFLAGS) $$(LDLIBS) -o $$@
	@ $$(LOG_TIME) "$$(C_GREEN) CC $$(C_PURPLE) $$(notdir $$@) $$(C_RESET)"
	@ $$(LOG_TIME) "$$(C_GREEN) OK  Compilation finished $$(C_RESET)"

endef


$(eval $(call mk-profile, release, SRC, , $(BIN_NAME)))

all: $(NAME_release)

clean:
	@ $(RM) $(OBJ)
	@ $(LOG_TIME) "$(C_YELLOW) RM $(C_PURPLE) $(OBJ) $(C_RESET)"

fclean:
	@ $(RM) -r $(NAME_release) $(NAME_debug) $(BUILD_DIR) .cov \
		$(NAME_unit) $(PROF_DIR)  tests/unit_tests
	@ $(LOG_TIME) "$(C_YELLOW) RM $(C_PURPLE) $(NAME_release) $(NAME_debug) \
    .cov $(C_RESET)"

.NOTPARALLEL: re
re: fclean all


TESTS_DIR := tests
UNIT_SRC  := $(TESTS_DIR)/unit/test_unit.c \
             src/state.c src/druid.c src/villager.c

$(eval $(call mk-profile, unit, UNIT_SRC, , $(TESTS_DIR)/unit/unit_tests))

$(NAME_unit): CFLAGS := -std=gnu2x -iquote src -Wall -Wextra
$(NAME_unit): LDLIBS := -lcriterion -lpthread

.PHONY: tests_unit
tests_unit: $(NAME_unit)
	./$(NAME_unit) --verbose

.PHONY: tests_functional
tests_functional: all
	@ python3 $(TESTS_DIR)/functional/test_panoramix.py

.PHONY: tests_run
tests_run: tests_unit tests_functional


COV_FLAGS := -fprofile-instr-generate -fcoverage-mapping -O0
PROF_DIR  := .cov
PROF_DATA := $(PROF_DIR)/merged.profdata

$(eval $(call mk-profile, unit_cov, UNIT_SRC, , $(PROF_DIR)/unit_tests_cov))
$(eval $(call mk-profile, main_cov, SRC,       , $(PROF_DIR)/panoramix_cov))

$(PROF_DIR):
	@ mkdir -p $@

$(NAME_unit_cov): CFLAGS := -std=gnu2x -iquote src -Wall -Wextra $(COV_FLAGS)
$(NAME_unit_cov): LDLIBS := -lcriterion -lpthread
$(NAME_unit_cov): LDFLAGS := $(COV_FLAGS)
$(NAME_unit_cov): | $(PROF_DIR)

$(NAME_main_cov): CFLAGS := $(CFLAGS) $(COV_FLAGS)
$(NAME_main_cov): LDFLAGS := $(COV_FLAGS)
$(NAME_main_cov): | $(PROF_DIR)

.PHONY: cov
cov: $(NAME_unit_cov) $(NAME_main_cov)
	@ mkdir -p $(PROF_DIR)
	@ rm -f $(PROF_DIR)/*.profraw
	LLVM_PROFILE_FILE="$(PROF_DIR)/unit-%p.profraw" \
		./$(NAME_unit_cov) || true
	LLVM_PROFILE_FILE="$(PROF_DIR)/func-%p.profraw" \
		PANORAMIX_BIN="$(abspath $(NAME_main_cov))" \
		python3 $(TESTS_DIR)/functional/test_panoramix.py|| true
	llvm-profdata merge -sparse $(PROF_DIR)/*.profraw -o $(PROF_DATA)
	llvm-cov report $(NAME_main_cov) $(NAME_unit_cov) \
		-instr-profile=$(PROF_DATA) \
		--ignore-filename-regex='test_unit\.c'

.PHONY: all clean fclean re tests_unit tests_functional tests_run cov
