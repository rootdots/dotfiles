if status is-interactive
    # Commands to run in interactive sessions can go here
    set -Ux BAT_THEME ansi
    set -gx EDITOR hx
    set -g fzf_fd_opts --hidden --no-ignore --exclude .git

    starship init fish | source
    zoxide init fish | source
    envsource ~/.env
end
