function gc
    # Denna funktion guidar användaren att skriva ett konventionellt commit-meddelande.

    # 1. Välj commit-typ
    set TYPE (gum choose "fix" "feat" "docs" "style" "refactor" "test" "chore" "revert")

    # 2. Ange scope (valfritt)
    set SCOPE (gum input --placeholder "scope")

    # 3. Lägg till parenteser runt scope om det har ett värde
    if test -n "$SCOPE"
        set SCOPE "($SCOPE)"
    end

    # 4. Ange sammanfattning
    set SUMMARY (gum input --value "$TYPE$SCOPE: " --placeholder "Summary of this change")

    # 5. Ange beskrivning
    set DESCRIPTION (gum write --placeholder "Details of this change")

    # 6. Bekräfta och committa (Korrigerat för att använda if/end)
    if gum confirm "Commit changes?"
        git commit -m "$SUMMARY" -m "$DESCRIPTION"
    end
end
