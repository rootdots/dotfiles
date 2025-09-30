if status is-interactive
    # Commands to run in interactive sessions can go here
end

set -Ux BAT_THEME ansi
set -gx EDITOR hx

starship init fish | source

# Homebrew
# --------
# Configuring Completions in fish
# No configuration is needed if you’re using Homebrew’s fish. Friendly!
# If your fish is from somewhere else, add the following to your ~/.config/fish/config.fish:
if test -d (brew --prefix)"/share/fish/completions"
    set -p fish_complete_path (brew --prefix)/share/fish/completions
end

if test -d (brew --prefix)"/share/fish/vendor_completions.d"
    set -p fish_complete_path (brew --prefix)/share/fish/vendor_completions.d
end
