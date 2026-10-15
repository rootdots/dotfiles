# general
abbr --add ll 'ls -lha'

# git
abbr --add ga 'git add'
abbr --add gcm --set-cursor 'git commit -m "%"'
abbr --add gcp --set-cursor 'git commit -m "%" && git push'
abbr --add gcv 'git commit -v'
abbr --add gf 'git fetch'
abbr --add gfp 'git fetch && git pull'
abbr --add gp 'git pull'
abbr --add gpp 'git push'
abbr --add gr 'git restore'
abbr --add grs 'git restore --staged'

# astral - uv, ruff, ty
abbr --add rcf 'uv run ruff check --fix'
abbr --add rc 'uv run ruff check'
abbr --add rf 'uv run ruff format'
abbr --add tc 'ty check'
abbr --add ur 'uv run'

# help
abbr --add as 'abbr --show'
