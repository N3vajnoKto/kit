#!/bin/bash

# Определяем абсолютный путь к директории, где находится этот скрипт
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_HOOKS_DIR="$SCRIPT_DIR/git-hooks"
GIT_HOOKS_DIR=".git/hooks"

# Флаг для принудительной перезаписи (по умолчанию выключен)
FORCE_OVERWRITE=false

# Функция вывода справки
show_help() {
    echo "Использование: $0 [команда] [опции]"
    echo ""
    echo "Команды:"
    echo "  init    Первичная настройка окружения (создание симлинков и копирование хуков)."
    echo "  update  Обновление хуков и конфигураций (по умолчанию не перезаписывает существующие)."
    echo ""
    echo "Опции:"
    echo "  -f      Принудительная перезапись (force) существующих хуков и симлинков."
    echo "  -h      Показать эту справку."
    echo ""
    echo "Примеры:"
    echo "  $0 init"
    echo "  $0 update -f"
    exit 0
}

# Секция обработки аргументов командной строки
if [ $# -eq 0 ]; then
    show_help
fi

COMMAND=$1
shift # Сдвигаем аргументы, чтобы обрабатывать флаги (например, -f)

while getopts "fh" opt; do
    case ${opt} in
        f ) FORCE_OVERWRITE=true ;;
        h ) show_help ;;
        \? ) echo "❌ Ошибка: Неверный флаг."; show_help ;;
    esac
done

# Проверяем корректность переданной команды
if [ "$COMMAND" != "init" ] && [ "$COMMAND" != "update" ]; then
    echo "❌ Ошибка: Неизвестная команда '$COMMAND'."
    show_help
fi

echo "========================================="
echo "⚙️  Executing: $COMMAND (Force mode: $FORCE_OVERWRITE)..."
echo "========================================="

# -----------------------------------------------------------------------------
# ШАГ 1: Настройка конфигурационных файлов (.clang-format и .clang-tidy)
# -----------------------------------------------------------------------------
if [ ! -f "$SCRIPT_DIR/.clang-format" ] || [ ! -f "$SCRIPT_DIR/.clang-tidy" ]; then
    echo "❌ Error: .clang-format or .clang-tidy not found in the script directory."
    exit 1
fi

echo "🔗 Setting up configuration symlinks in: $PWD"

for config_file in ".clang-format" ".clang-tidy"; do
    if [ -e "$config_file" ] || [ -L "$config_file" ]; then
        if [ "$FORCE_OVERWRITE" = true ]; then
            echo "🔥 [FORCE] Overwriting existing $config_file..."
            rm -f "$config_file"
            ln -s "$SCRIPT_DIR/$config_file" "$config_file"
            echo "✅ Symlink for $config_file recreated."
        else
            echo "⚠️  $config_file already exists in the destination. Skipping symlink."
        fi
    else
        ln -s "$SCRIPT_DIR/$config_file" "$config_file"
        echo "✅ Symlink for $config_file successfully created."
    fi
done

# -----------------------------------------------------------------------------
# ШАГ 2: Проверка репозитория Git
# -----------------------------------------------------------------------------
if [ ! -d "$GIT_HOOKS_DIR" ]; then
    echo "❌ Error: .git/hooks directory not found. Are you in the root of a Git repository?"
    exit 1
fi

# -----------------------------------------------------------------------------
# ШАГ 3: Деплой / Обновление Git-хуков
# -----------------------------------------------------------------------------
echo -e "\n🚀 Deploying project-specific Git hooks from: git-hooks/"

if [ ! -d "$SOURCE_HOOKS_DIR" ]; then
    echo "⚠️  Skipping hooks installation: Folder '$SOURCE_HOOKS_DIR' does not exist."
else
    # Находим все файлы в папке git-hooks
    FOUND_HOOKS=$(find "$SOURCE_HOOKS_DIR" -maxdepth 1 -type f)
    
    if [ -z "$FOUND_HOOKS" ]; then
        echo "ℹ️  No files found inside the '$SOURCE_HOOKS_DIR' directory to install."
    else
        while read -r src_hook_path; do
            HOOK_NAME=$(basename "$src_hook_path")
            DEST_HOOK="$GIT_HOOKS_DIR/$HOOK_NAME"
            
            # Проверяем, существует ли хук в целевой папке
            if [ -e "$DEST_HOOK" ] || [ -L "$DEST_HOOK" ]; then
                if [ "$FORCE_OVERWRITE" = true ]; then
                    echo "🔥 [FORCE] Overwriting existing hook '$HOOK_NAME'..."
                    rm -f "$DEST_HOOK"
                    cp "$src_hook_path" "$DEST_HOOK"
                    chmod +x "$DEST_HOOK"
                    echo "✅ Updated '$HOOK_NAME' successfully."
                else
                    echo "⚠️  The hook '$HOOK_NAME' already exists in .git/hooks/. Will NOT overwrite."
                fi
            else
                # Обычное копирование, если файла нет
                cp "$src_hook_path" "$DEST_HOOK"
                chmod +x "$DEST_HOOK"
                echo "✅ Installed '$HOOK_NAME' to .git/hooks/ and made it executable."
            fi
        done <<< "$FOUND_HOOKS"
    fi
fi

echo -e "\n========================================="
echo "🎉 Done! Project $COMMAND completed successfully."
echo "========================================="
