function release
    set -l bump_type $argv[1]

    # Step 1: Determine new version
    if test -z "$bump_type"
        set -l new_version (git-cliff --bumped-version)
    else if contains $bump_type major minor patch
        set -l current_version (git-cliff --bumped-version)
        set -l major (string split . $current_version)[1]
        set -l minor (string split . $current_version)[2]
        set -l patch (string split . $current_version)[3]

        switch $bump_type
            case major
                set major (math "$major + 1")
                set minor 0
                set patch 0
            case minor
                set minor (math "$minor + 1")
                set patch 0
            case patch
                set patch (math "$patch + 1")
        end

        set new_version "$major.$minor.$patch"
    else
        echo "❌ Invalid bump type. Use: major, minor, patch or leave empty for auto."
        return 1
    end

    echo "🔢 New version: $new_version"

    # Step 2: Update version in pyproject.toml or fallback to VERSION file
    if test -f pyproject.toml
        sed -i '' "s/^version = \".*\"/version = \"$new_version\"/" pyproject.toml
        git add pyproject.toml
    else
        echo "$new_version" >VERSION
        git add VERSION
    end

    # Step 3: Commit version bump
    git commit -m "chore: release v$new_version"

    # Step 4: Tag the release
    git tag "v$new_version"

    # Step 5: Generate changelog
    git-cliff -t "v$new_version" -o CHANGELOG.md
    git add CHANGELOG.md
    git commit -m "docs: update changelog for v$new_version"

    # Step 6: Push changes and tag
    git push
    git push origin "v$new_version"

    echo "✅ Release v$new_version complete!"
end
