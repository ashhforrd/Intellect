on run arguments
    set launcherScript to item 1 of arguments
    set shellCommand to "export PATH=/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH; bash " & quoted form of launcherScript
    tell application "Terminal"
        activate
        do script shellCommand
    end tell
end run
