on run argv
  set sourcePath to item 1 of argv
  set outputPath to item 2 of argv
  set sourceName to do shell script "basename " & quoted form of sourcePath
  set sourceFile to POSIX file sourcePath
  set outputAlias to (POSIX file outputPath) as alias
  tell application "Microsoft Word"
    activate
    try
      close (every document whose name is sourceName) saving no
    end try
    open file name sourceFile
    save as active document file name outputAlias file format format document
    close active document saving no
  end tell
end run
