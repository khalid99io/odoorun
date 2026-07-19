"""Shell integration for odoorun's dynamic completions."""

BASH_COMPLETION = r'''# Bash completion for odoorun database names.
_odoorun_complete() {
    local current previous prefix suggestion
    COMPREPLY=()
    current="${COMP_WORDS[COMP_CWORD]}"
    previous="${COMP_WORDS[COMP_CWORD-1]}"

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
    fi
}

complete -F _odoorun_complete odoorun
complete -F _odoorun_complete o
complete -F _odoorun_complete odoo
complete -F _odoorun_complete odoo-bin
complete -F _odoorun_complete ./odoo-bin
'''

BASH_COMPLETION_SOURCE = "# odoorun database completion\nsource <(odoorun completion bash)\n"
