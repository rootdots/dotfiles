function ga
    set ADD "Add"
    set RESET "Reset"

    # 1. Användaren väljer huvudåtgärden (Add/Reset)
    set ACTION (gum choose $ADD $RESET)

    # 2. Hämta en lista över ostäda/ändrade filer
    set FILES (git status --short | cut -c 4- | gum choose --no-limit)

    # 3. Kontrollera om användaren faktiskt valde några filer
    if test (string length "$FILES") -gt 0
        # Filer har valts
        if test "$ACTION" = "$ADD"
            # Skicka den valda listan till git add
            echo "$FILES" | xargs git add
        else
            # Skicka den valda listan till git restore
            echo "$FILES" | xargs git restore
        end
    else
        # Inga filer valdes, skriv ut ett meddelande
        echo (set_color yellow)"Inga filer valda. Avbryter åtgärden."(set_color normal)
    end
end
