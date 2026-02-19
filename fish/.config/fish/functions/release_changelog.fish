#!/usr/bin/env fish

# Fånga --dry-run argumentet
set -l dry_run_mode false
if test (count $argv) -gt 0; and test "$argv[1]" = "--dry-run"
    set dry_run_mode true
end

# Kontrollera att nödvändiga verktyg finns
function check_tools
    set -l missing_tools
    for tool in git-cliff gum glow
        if not type -q $tool            set missing_tools $missing_tools $tool
        end
    end

    if test (count $missing_tools) -gt 0
        echo (gum style --foreground "#FF0000" "❌ Fel: Följande verktyg saknas:")
        echo (gum style --foreground "#FFA500" "  - " (string join ", " $missing_tools))
        echo ""
        echo "Installera dem för att köra scriptet."
        exit 1
    end
end

check_tools

echo (gum style --foreground "#4CAF50" "🚀 Startar release-process...")
echo ""

# 1. Räkna ut nästa version baserat på conventional commits
set -l new_version (git-cliff --bumped-version --unreleased 2> /dev/null)

if test -z "$new_version"
    echo (gum style --foreground "#FFA500" "⚠️ Inga nya commits sedan senaste taggen hittades, eller så är konventionen felaktig.")
    echo (gum style --foreground "#FFA500" "  - Avbryter...")
    exit 0
end

echo (gum style --foreground "#8A2BE2" "ℹ️ Ny version beräknad: " (gum style --bold --foreground "#FFFFFF" $new_version))

# 2. Generera den nya changelog-sektionen
set -l new_changelog (git-cliff --tag "$new_version")

# Förhandsgranskning av changelog
echo (gum style --foreground "#8A2BE2" "ℹ️ Förhandsgranskning av ny changelog-sektion:")
echo ""
echo $new_changelog | glow -

echo ""

if $dry_run_mode
    echo (gum style --foreground "#FFA500" "✨ KÖR I DRY-RUN-LÄGE ✨")
    echo (gum style --foreground "#FFA500" "  - Ingen filändring eller git-operation har utförts.")
    exit 0
end

# 3. Uppdatera CHANGELOG.md
set -l changelog_file "CHANGELOG.md"

if test -f "$changelog_file"
    # Prepend till befintlig fil
    echo (gum style --foreground "#4CAF50" "💾 Uppdaterar befintlig" (gum style --bold $changelog_file) "...")
    set -l temp_file (mktemp)
    echo $new_changelog > $temp_file
    cat $changelog_file >> $temp_file
    mv $temp_file $changelog_file
else
    # Skapa ny fil
    echo (gum style --foreground "#4CAF50" "💾 Skapar ny" (gum style --bold $changelog_file) "...")
    echo "# Changelog" > $changelog_file
    echo "" >> $changelog_file
    echo $new_changelog >> $changelog_file
end

# 4. Git-operationer
echo (gum style --foreground "#4CAF50" "🔨 Utför git-operationer...")

# Commit av CHANGELOG.md
git add "$changelog_file"
git commit -m "chore(release): release $new_version"

# Skapa ny tag
git tag -a "$new_version" -m "Release $new_version"

# Push
echo (gum style --foreground "#4CAF50" "📤 Pushar commits och taggar...")
if git push --follow-tags
    echo (gum style --foreground "#4CAF50" "✅ Release $new_version slutförd framgångsrikt!")
else
    echo (gum style --foreground "#FF0000" "❌ Fel vid git push. Kontrollera din anslutning och behörighet.")
    exit 1
end
