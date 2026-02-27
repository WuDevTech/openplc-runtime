#!/bin/bash
set -euo pipefail

# Paths
ROOT="core/generated"
LIB_PATH="$ROOT/lib"
SRC_PATH="$ROOT"
BUILD_PATH="build"
PYTHON_INCLUDE_PATH="core/src/plc_app/include"
PYTHON_LOADER_SRC="core/src/plc_app/python_loader.c"

FLAGS="-w -O3 -fPIC"

check_required_files() {
    local missing_files=()

    if [ ! -f "$SRC_PATH/Config0.c" ]; then
        missing_files+=("$SRC_PATH/Config0.c")
    fi
    if [ ! -f "$SRC_PATH/Res0.c" ]; then
        missing_files+=("$SRC_PATH/Res0.c")
    fi
    if [ ! -f "$SRC_PATH/debug.c" ]; then
        missing_files+=("$SRC_PATH/debug.c")
    fi
    if [ ! -f "$SRC_PATH/glueVars.c" ]; then
        missing_files+=("$SRC_PATH/glueVars.c")
    fi
    if [ ! -d "$LIB_PATH" ]; then
        missing_files+=("$LIB_PATH (directory)")
    fi

    if [ ${#missing_files[@]} -ne 0 ]; then
        echo "[ERROR] Missing required source files:" >&2
        printf '  %s\n' "${missing_files[@]}" >&2
        exit 1
    fi
}

check_required_files

# Ensure build directory exists
mkdir -p "$BUILD_PATH"
if [ ! -d "$BUILD_PATH" ]; then
    echo "[ERROR] Failed to create build directory: $BUILD_PATH" >&2
    exit 1
fi

# On Cygwin/MSYS2, the PE loader cannot resolve symbols from the running
# executable at dlopen time (unlike Linux where -rdynamic handles this). We must
# compile runtime-provided functions (e.g. TCP communication blocks) directly
# into the PLC shared library. A minimal log_error stub is provided since the
# full log.c depends on plc_main internals (unix socket, keep_running signal).
EXTRA_OBJS=""
case "$(uname -s)" in
    CYGWIN*|MSYS*|MINGW*)
        TCP_SRC="core/src/plc_app/client_tcp_udp.c"
        if [ -f "$TCP_SRC" ]; then
            echo "[INFO] Compiling runtime communication functions for MSYS2/Cygwin..."
            cat > "$BUILD_PATH/log_stub.c" << 'STUB'
#include <stdio.h>
#include <stdarg.h>
void log_error(const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    fprintf(stderr, "[ERROR] ");
    vfprintf(stderr, fmt, args);
    fprintf(stderr, "\n");
    va_end(args);
}
STUB
            gcc $FLAGS -I "core/src/plc_app" -c "$TCP_SRC" -o "$BUILD_PATH/client_tcp_udp.o"
            gcc $FLAGS -c "$BUILD_PATH/log_stub.c" -o "$BUILD_PATH/log_stub.o"
            EXTRA_OBJS="$BUILD_PATH/client_tcp_udp.o $BUILD_PATH/log_stub.o"
        fi
        ;;
esac

# Compile objects into build/
echo "[INFO] Compiling Config0.c..."
gcc $FLAGS -I "$LIB_PATH" -I "$PYTHON_INCLUDE_PATH" -include iec_python.h -c "$SRC_PATH/Config0.c" -o "$BUILD_PATH/Config0.o"
echo "[INFO] Compiling Res0.c..."
gcc $FLAGS -I "$LIB_PATH" -I "$PYTHON_INCLUDE_PATH" -include iec_python.h -c "$SRC_PATH/Res0.c" -o "$BUILD_PATH/Res0.o"
echo "[INFO] Compiling debug.c..."
gcc $FLAGS -I "$LIB_PATH" -c "$SRC_PATH/debug.c" -o "$BUILD_PATH/debug.o"
echo "[INFO] Compiling glueVars.c..."
gcc $FLAGS -I "$LIB_PATH" -DOPENPLC_V4 -c "$SRC_PATH/glueVars.c" -o "$BUILD_PATH/glueVars.o"
echo "[INFO] Compiling c_blocks_code.cpp..."
g++ $FLAGS -I "$LIB_PATH" -c "$SRC_PATH/c_blocks_code.cpp" -o "$BUILD_PATH/c_blocks_code.o"
echo "[INFO] Compiling python_loader.c..."
gcc $FLAGS -I "core/src/plc_app" -c "$PYTHON_LOADER_SRC" -o "$BUILD_PATH/python_loader.o"

# Link shared library into build/
echo "[INFO] Linking shared library..."
g++ $FLAGS -shared -o "$BUILD_PATH/new_libplc.so" "$BUILD_PATH/Config0.o" \
    "$BUILD_PATH/Res0.o" "$BUILD_PATH/debug.o" "$BUILD_PATH/glueVars.o" \
    "$BUILD_PATH/c_blocks_code.o" "$BUILD_PATH/python_loader.o" $EXTRA_OBJS -lpthread -lrt
