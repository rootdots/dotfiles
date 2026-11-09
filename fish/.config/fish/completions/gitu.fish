# Print an optspec for argparse to handle cmd's options that are independent of any subcommand.
function __fish_gitu_global_optspecs
    string join \n k/keys= print log version c/config= h/help
end

function __fish_gitu_needs_command
    # Figure out if the current invocation already has a command.
    set -l cmd (commandline -opc)
    set -e cmd[1]
    argparse -s (__fish_gitu_global_optspecs) -- $cmd 2>/dev/null
    or return
    if set -q argv[1]
        # Also print the command, so this can be used to figure out what it is.
        echo $argv[1]
        return 1
    end
    return 0
end

function __fish_gitu_using_subcommand
    set -l cmd (__fish_gitu_needs_command)
    test -z "$cmd"
    and return 1
    contains -- $cmd[1] $argv
end

complete -c gitu -n "__fish_gitu_needs_command" -s k -l keys -d 'Send keys on startup (eg: `gitu -k ll`).     It is possible to send:     - single char-keys: a, b, c, ...     - special keys: <backspace>, <enter>, <up>, <tab>, <delete>, <esc>, ...     - modifiers: <ctrl+a>, <ctrl+shift+alt+a>, <shift+delete>' -r
complete -c gitu -n "__fish_gitu_needs_command" -s c -l config -d 'Config file to use' -r -F
complete -c gitu -n "__fish_gitu_needs_command" -l print -d 'Print one frame and exit. Useful for debugging'
complete -c gitu -n "__fish_gitu_needs_command" -l log -d 'Enable logging to \'gitu.log\''
complete -c gitu -n "__fish_gitu_needs_command" -l version -d 'Print version'
complete -c gitu -n "__fish_gitu_needs_command" -s h -l help -d 'Print help'
complete -c gitu -n "__fish_gitu_needs_command" -f -a "show"
complete -c gitu -n "__fish_gitu_needs_command" -f -a "blame"
complete -c gitu -n "__fish_gitu_needs_command" -f -a "completion" -d 'Print a shell completion script to stdout'
complete -c gitu -n "__fish_gitu_needs_command" -f -a "help" -d 'Print this message or the help of the given subcommand(s)'
complete -c gitu -n "__fish_gitu_using_subcommand show" -s h -l help -d 'Print help'
complete -c gitu -n "__fish_gitu_using_subcommand blame" -s r -l rev -r
complete -c gitu -n "__fish_gitu_using_subcommand blame" -s h -l help -d 'Print help'
complete -c gitu -n "__fish_gitu_using_subcommand completion" -s h -l help -d 'Print help (see more with \'--help\')'
complete -c gitu -n "__fish_gitu_using_subcommand help; and not __fish_seen_subcommand_from show blame completion help" -f -a "show"
complete -c gitu -n "__fish_gitu_using_subcommand help; and not __fish_seen_subcommand_from show blame completion help" -f -a "blame"
complete -c gitu -n "__fish_gitu_using_subcommand help; and not __fish_seen_subcommand_from show blame completion help" -f -a "completion" -d 'Print a shell completion script to stdout'
complete -c gitu -n "__fish_gitu_using_subcommand help; and not __fish_seen_subcommand_from show blame completion help" -f -a "help" -d 'Print this message or the help of the given subcommand(s)'
