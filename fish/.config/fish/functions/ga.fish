function ga
    set -l files (git status --porcelain | awk '$1 != "??" {print $2}')

    if test (count $files) -eq 0
        echo "No modified files to add."
        return
    end

    set -l selected (commandline -f complete | fzf --multi --prompt="Select files to add > ")

    if test -n "$selected"
        for file in $selected
            echo "git add $file"
        end
    else
        echo "No files selected."
    end
end
