"""Shell integration for odoorun's dynamic completions."""

BASH_COMPLETION = r'''# Bash completion for odoorun commands and Odoo values.
_odoorun_complete() {
    local current previous prefix value leading selected suggestion program
    local module_completion
    COMPREPLY=()
    module_completion=0
    current="${COMP_WORDS[COMP_CWORD]}"
    previous="${COMP_WORDS[COMP_CWORD-1]}"
    program="${COMP_WORDS[0]##*/}"

    if [[ "$previous" == "-d" || "$previous" == "--database" ]]; then
        while IFS= read -r suggestion; do
            COMPREPLY+=("$suggestion")
        done < <(command odoorun __complete database "$current")
        return
    fi

    if [[ "$current" == --database=* ]]; then
        prefix="${current#--database=}"
        while IFS= read -r suggestion; do
            COMPREPLY+=("--database=$suggestion")
        done < <(command odoorun __complete database "$prefix")
        return
    fi

    if [[ "$previous" == "-u" || "$previous" == "--update" ||
          "$previous" == "-i" || "$previous" == "--init" ]]; then
        value="$current"
        leading=""
        module_completion=1
    elif [[ "$current" == --update=* ]]; then
        value="${current#--update=}"
        leading="--update="
        module_completion=1
    elif [[ "$current" == --init=* ]]; then
        value="${current#--init=}"
        leading="--init="
        module_completion=1
    else
        value=""
    fi

    if [[ "$module_completion" == 1 ]]; then
        prefix="${value##*,}"
        if [[ "$value" == *,* ]]; then
            selected="${value%,*},"
        else
            selected=""
        fi
        while IFS= read -r suggestion; do
            COMPREPLY+=("${leading}${selected}${suggestion}")
        done < <(command odoorun __complete module "$prefix" -- "${COMP_WORDS[@]}")
        compopt -o nospace 2>/dev/null || true
        return
    fi

    if [[ "$program" == "odoorun" || "$program" == "o" ]]; then
        while IFS= read -r suggestion; do
            COMPREPLY+=("$suggestion")
        done < <(
            command odoorun __complete command -- "$current" \
                "${COMP_WORDS[@]:1:COMP_CWORD-1}"
        )
    fi
}

complete -F _odoorun_complete odoorun
complete -F _odoorun_complete o
complete -F _odoorun_complete odoo
complete -F _odoorun_complete odoo-bin
complete -F _odoorun_complete ./odoo-bin
'''

BASH_COMPLETION_COMMAND = "source <(odoorun completion bash)"
BASH_COMPLETION_SOURCE = (
    "# odoorun command, database, and module completion\n"
    f"{BASH_COMPLETION_COMMAND}\n"
)
